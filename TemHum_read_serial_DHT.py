#!/Volumes/Mini/opt/anaconda3/envs/copilot/bin/python

# TEMHUMI

"""
Arduino Serial Monitor with Real-Time Plotting
Reads temperature and humidity data from Arduino
Expected serial format: "humidity|temperature" (e.g., "65.5|23.2")
"""
import serial
import time
import sys
import matplotlib
matplotlib.use('TkAgg')  # Force TkAgg backend for better window visibility
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque
import numpy as np
from datetime import datetime, timedelta
import matplotlib.dates as mdates
from scipy.interpolate import make_interp_spline

# Serial port configuration
PORT = '/dev/cu.usbserial-31310'
BAUDRATE = 9600
TIMEOUT = 1

# Plot configuration
TIME_WINDOW = 60*60*24  # Time window in seconds to display (24 hours)
PLOT_INTERVAL_MINUTES = 10  # Interval in minutes for plotting data points

# Change detection thresholds - Lowered to capture more data variations
HUMIDITY_THRESHOLD = 0.5    # Minimum humidity change (%) to trigger plot/log
TEMPERATURE_THRESHOLD = 0.5 # Minimum temperature change (°C) to trigger plot/log

# Calibration adjustments
HUMIDITY_OFFSET = -4         # Adjustment for humidity (+ or - percentage points)
TEMPERATURE_OFFSET = -0.5     # Adjustment for temperature (+ or - degrees Celsius)

# Data buffers
humidity_buffer = deque()
temperature_buffer = deque()
time_buffer = deque()  # Will store datetime objects

def read_serial_with_plot():
    """Read and display temperature/humidity data from Arduino with real-time plotting"""
    try:
        # Open serial connection
        print(f"Connecting to {PORT} at {BAUDRATE} baud...")
        ser = serial.Serial(
            PORT, 
            BAUDRATE, 
            timeout=TIMEOUT,
            exclusive=False  # Allow multiple access
        )
        
        # Flush any existing data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Wait for connection to establish and Arduino to reset
        print("Waiting for Arduino to reset...")
        time.sleep(3)
        
        print("Connected! Reading serial output...")
        print(f"Plot interval: Every {PLOT_INTERVAL_MINUTES} minutes")
        print(f"Calibration: Humidity offset {HUMIDITY_OFFSET:+.1f}%, Temperature offset {TEMPERATURE_OFFSET:+.1f}°C")
        print("Waiting for Arduino data... (Make sure Arduino is sending data)")
        print("-" * 50)
        
        # Initialize log file with header if it doesn't exist
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        log_filename = os.path.join(script_dir, "TemHumi.log")
        try:
            # Check if file exists and is empty
            if not os.path.exists(log_filename) or os.path.getsize(log_filename) == 0:
                with open(log_filename, 'w') as log_file:
                    log_file.write("# Temperature and Humidity Data Log\n")
                    log_file.write("# Format: Timestamp,Humidity(%),Temperature(°C)\n")
                    log_file.write("# Started: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n")
                    log_file.write("Timestamp,Humidity,Temperature\n")
                print(f"Created new log file: {log_filename}")
            else:
                print(f"Appending to existing log file: {log_filename}")
        except Exception as log_error:
            print(f"Warning: Could not initialize log file: {log_error}")
            print(f"Script directory: {script_dir}")
            print(f"Log file path: {log_filename}")
        
        # Set up the plot with two subplots - Dark Theme
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.patch.set_facecolor('black')
        
        # Humidity plot (top) - Smooth curve style
        humidity_line, = ax1.plot([], [], '#00BFFF', linewidth=3, label='Humidity')
        ax1.set_ylabel('Humidity (%)', fontsize=12, color='white')
        ax1.set_title('Real-Time Temperature and Humidity', fontsize=14, fontweight='bold', color='white')
        ax1.set_ylim(20, 100)  # Humidity range 20-100%
        ax1.grid(True, alpha=0.3, color='gray')
        ax1.tick_params(colors='white')
        ax1.set_facecolor('black')
        legend1 = ax1.legend()
        legend1.get_frame().set_facecolor('black')
        legend1.get_frame().set_edgecolor('white')
        for text in legend1.get_texts():
            text.set_color('white')
        
        # Temperature plot (bottom) - Smooth curve style
        temperature_line, = ax2.plot([], [], '#FF6347', linewidth=3, label='Temperature')
        ax2.set_xlabel('Timestamp', fontsize=12, color='white')
        ax2.set_ylabel('Temperature (°C)', fontsize=12, color='white')
        ax2.set_ylim(10, 40)  # Temperature range 10-40°C
        ax2.grid(True, alpha=0.3, color='gray')
        ax2.tick_params(colors='white')
        ax2.set_facecolor('black')
        legend2 = ax2.legend()
        legend2.get_frame().set_facecolor('black')
        legend2.get_frame().set_edgecolor('white')
        for text in legend2.get_texts():
            text.set_color('white')
        
        # Format x-axis to show timestamps (better formatting for 24 hour window)
        date_formatter = mdates.DateFormatter('%H:%M')  # Show hours:minutes only
        ax2.xaxis.set_major_formatter(date_formatter)
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=1))  # Major ticks every 1 hour
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        fig.autofmt_xdate()  # Auto-format date labels
        
        # Store annotations for value changes
        annotations = []
        
        # Track last values for change detection
        last_humidity = None
        last_temperature = None
        last_plot_time = None  # Track when we last plotted data
        
        # Text annotations for current values
        humidity_text = None
        temperature_text = None
        
        # Start labels (shown only once at the beginning)
        start_humidity_label = None
        start_temperature_label = None
        start_labels_added = False
        
        # 6-hour interval labels
        six_hour_labels_humidity = []
        six_hour_labels_temperature = []
        last_six_hour_labels = set()  # Track which 6-hour marks we've already labeled
        
        def update_plot(frame):
            """Update function for animation"""
            nonlocal last_humidity, last_temperature, last_plot_time, humidity_text, temperature_text, start_humidity_label, start_temperature_label, start_labels_added, six_hour_labels_humidity, six_hour_labels_temperature, last_six_hour_labels
            
            if ser.in_waiting > 0:
                # Read line from serial port
                line_data = ser.readline().decode('utf-8', errors='ignore').strip()
                if line_data:
                    current_time = datetime.now()
                    print(f"{time.strftime('%H:%M:%S')} | RAW: {line_data}")
                    
                    # Parse humidity,temperature or humidity|temperature format
                    try:
                        # Split by pipe or comma separator
                        if '|' in line_data:
                            parts = line_data.split('|')
                        elif ',' in line_data:
                            parts = line_data.split(',')
                        else:
                            parts = []
                            
                        if len(parts) >= 2:
                            # Parse raw sensor values
                            humidity_raw = float(parts[0].strip())
                            temperature_raw = float(parts[1].strip())
                            
                            # Apply calibration adjustments using offset variables
                            humidity = round((humidity_raw + HUMIDITY_OFFSET) * 10) / 10  # Apply humidity offset and round to one decimal place
                            temperature = round((temperature_raw + TEMPERATURE_OFFSET) * 10) / 10  # Apply temperature offset and round to one decimal place
                            
                            if HUMIDITY_OFFSET != 0 or TEMPERATURE_OFFSET != 0:
                                print(f"  -> ADJUSTED: H={humidity:.1f}% (was {humidity_raw:.1f}%), T={temperature:.1f}°C (was {temperature_raw:.1f}°C)")
                            else:
                                print(f"  -> RAW VALUES: H={humidity:.1f}%, T={temperature:.1f}°C")
                            
                            # Check if 10 minutes have passed since last plot (or first reading)
                            should_plot = False
                            if last_plot_time is None:
                                should_plot = True  # First reading
                                print(f"  -> FIRST READING: Will plot initial values")
                            else:
                                time_since_last_plot = (current_time - last_plot_time).total_seconds()
                                interval_seconds = PLOT_INTERVAL_MINUTES * 60
                                if time_since_last_plot >= interval_seconds:
                                    should_plot = True
                                    print(f"  -> {PLOT_INTERVAL_MINUTES} MINUTES PASSED: Will plot new values ({time_since_last_plot:.0f}s since last plot)")
                                else:
                                    print(f"  -> WAITING: {interval_seconds - time_since_last_plot:.0f}s until next plot")
                            
                            # Calculate changes for display
                            h_change = abs(humidity - last_humidity) if last_humidity is not None else 0
                            t_change = abs(temperature - last_temperature) if last_temperature is not None else 0
                            
                            # Plot data every 10 minutes
                            if should_plot:
                                # Store current timestamp as datetime object
                                time_buffer.append(current_time)
                                humidity_buffer.append(humidity)
                                temperature_buffer.append(temperature)
                                
                                # Write data to log file (append mode)
                                try:
                                    with open(log_filename, 'a') as log_file:
                                        log_entry = f"{current_time.strftime('%Y-%m-%d %H:%M:%S')},{humidity:.1f},{temperature:.1f}\n"
                                        log_file.write(log_entry)
                                        log_file.flush()  # Ensure data is written immediately
                                    print(f"  -> LOGGED to {os.path.basename(log_filename)}")
                                except Exception as log_error:
                                    print(f"  -> ERROR writing to log file: {log_error}")
                                    print(f"  -> Log file path: {log_filename}")
                                
                                # Update last values AFTER logging
                                last_humidity = humidity
                                last_temperature = temperature
                                last_plot_time = current_time
                                
                                print(f"  -> PLOTTED ({PLOT_INTERVAL_MINUTES}min interval): Humi: {humidity:.1f}%, Tempe: {temperature:.1f}°C")
                            else:
                                # Still update current values for change calculation, but don't plot
                                last_humidity = humidity
                                last_temperature = temperature
                                print(f"  -> NOT PLOTTED (waiting for {PLOT_INTERVAL_MINUTES}min): Humi: {humidity:.1f}%, Tempe: {temperature:.1f}°C")
                        
                    except (ValueError, IndexError) as e:
                        print(f"  -> Error parsing data: {e}")
            
            # Remove data points older than TIME_WINDOW
            if len(time_buffer) > 0:
                cutoff_time = datetime.now() - timedelta(seconds=TIME_WINDOW)
                while len(time_buffer) > 0 and time_buffer[0] < cutoff_time:
                    time_buffer.popleft()
                    humidity_buffer.popleft()
                    temperature_buffer.popleft()
            
            # Update plot data
            if len(time_buffer) > 0:
                # Create smooth curves if we have enough data points
                if len(time_buffer) > 3:  # Need at least 4 points for spline interpolation
                    try:
                        # Convert timestamps to numerical values for interpolation
                        time_nums = mdates.date2num(list(time_buffer))
                        
                        # Create smooth interpolation (3x density)
                        time_smooth = np.linspace(time_nums[0], time_nums[-1], len(time_buffer) * 3)
                        
                        # Interpolate humidity and temperature
                        spl_humidity = make_interp_spline(time_nums, list(humidity_buffer), k=3)
                        spl_temperature = make_interp_spline(time_nums, list(temperature_buffer), k=3)
                        
                        humidity_smooth = spl_humidity(time_smooth)
                        temperature_smooth = spl_temperature(time_smooth)
                        
                        # Convert back to datetime objects for plotting
                        timestamps_smooth = mdates.num2date(time_smooth)
                        
                        # Update lines with smooth data
                        humidity_line.set_data(timestamps_smooth, humidity_smooth)
                        temperature_line.set_data(timestamps_smooth, temperature_smooth)
                    except:
                        # Fallback to regular plot if interpolation fails
                        humidity_line.set_data(list(time_buffer), list(humidity_buffer))
                        temperature_line.set_data(list(time_buffer), list(temperature_buffer))
                else:
                    # Use regular plot for few data points
                    humidity_line.set_data(list(time_buffer), list(humidity_buffer))
                    temperature_line.set_data(list(time_buffer), list(temperature_buffer))
                
                # Set x-axis range to show last TIME_WINDOW seconds
                now = datetime.now()
                x_min = now - timedelta(seconds=TIME_WINDOW)
                x_max = now
                ax1.set_xlim(mdates.date2num(x_min), mdates.date2num(x_max))
                ax2.set_xlim(mdates.date2num(x_min), mdates.date2num(x_max))
                
                # Add/update labels on data points
                if len(time_buffer) > 0:
                    # Get the first and latest values
                    first_time = list(time_buffer)[0]
                    first_humidity = list(humidity_buffer)[0]
                    first_temperature = list(temperature_buffer)[0]
                    
                    latest_time = list(time_buffer)[-1]
                    latest_humidity = list(humidity_buffer)[-1]
                    latest_temperature = list(temperature_buffer)[-1]
                    
                    # Add start labels (only once at the beginning) - BELOW the curve
                    if not start_labels_added and len(time_buffer) >= 1:
                        start_humidity_label = ax1.annotate(f'START: {first_humidity:.1f}%', 
                                                          xy=(mdates.date2num(first_time), first_humidity),
                                                          xytext=(-80, -25), textcoords='offset points',
                                                          bbox=dict(boxstyle='round,pad=0.4', facecolor='#00FF00', alpha=0.9, edgecolor='white'),
                                                          fontsize=11, fontweight='bold', color='black',
                                                          arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', color='white', lw=1.5))
                        
                        start_temperature_label = ax2.annotate(f'START: {first_temperature:.1f}°C', 
                                                             xy=(mdates.date2num(first_time), first_temperature),
                                                             xytext=(-80, -25), textcoords='offset points',
                                                             bbox=dict(boxstyle='round,pad=0.4', facecolor='#00FF00', alpha=0.9, edgecolor='white'),
                                                             fontsize=11, fontweight='bold', color='black',
                                                             arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0.1', color='white', lw=1.5))
                        
                        start_labels_added = True
                    
                    # Add 6-hour interval labels for all data points
                    for i, (timestamp, humidity_val, temp_val) in enumerate(zip(list(time_buffer), list(humidity_buffer), list(temperature_buffer))):
                        # Check if this timestamp is at a 6-hour mark (00:00, 06:00, 12:00, 18:00)
                        hour = timestamp.hour
                        if hour % 6 == 0:  # 0, 6, 12, 18 hours
                            # Create unique key for this 6-hour mark
                            six_hour_key = f"{timestamp.strftime('%Y-%m-%d_%H')}"
                            
                            # Only add label if we haven't already labeled this 6-hour mark
                            if six_hour_key not in last_six_hour_labels:
                                # Add humidity label at 6-hour mark
                                six_hour_label_hum = ax1.annotate(f'{timestamp.strftime("%H:%M")}\n{humidity_val:.1f}%', 
                                                                 xy=(mdates.date2num(timestamp), humidity_val),
                                                                 xytext=(0, 35), textcoords='offset points',
                                                                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFD700', alpha=0.8, edgecolor='white'),
                                                                 fontsize=9, fontweight='bold', color='black',
                                                                 ha='center',
                                                                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='white', lw=1))
                                
                                # Add temperature label at 6-hour mark  
                                six_hour_label_temp = ax2.annotate(f'{timestamp.strftime("%H:%M")}\n{temp_val:.1f}°C', 
                                                                  xy=(mdates.date2num(timestamp), temp_val),
                                                                  xytext=(0, 35), textcoords='offset points',
                                                                  bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFD700', alpha=0.8, edgecolor='white'),
                                                                  fontsize=9, fontweight='bold', color='black',
                                                                  ha='center',
                                                                  arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='white', lw=1))
                                
                                # Store labels and mark this 6-hour period as labeled
                                six_hour_labels_humidity.append(six_hour_label_hum)
                                six_hour_labels_temperature.append(six_hour_label_temp)
                                last_six_hour_labels.add(six_hour_key)
                    
                    # Remove previous real-time text annotations
                    if humidity_text:
                        humidity_text.remove()
                    if temperature_text:
                        temperature_text.remove()
                    
                    # Add current real-time value labels (always at the end) - ABOVE the curve
                    humidity_text = ax1.annotate(f'NOW: {latest_humidity:.1f}%', 
                                               xy=(mdates.date2num(latest_time), latest_humidity),
                                               xytext=(-80, 25), textcoords='offset points',
                                               bbox=dict(boxstyle='round,pad=0.4', facecolor='#00BFFF', alpha=0.9, edgecolor='white'),
                                               fontsize=11, fontweight='bold', color='white',
                                               arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='white', lw=1.5))
                    
                    temperature_text = ax2.annotate(f'NOW: {latest_temperature:.1f}°C', 
                                                   xy=(mdates.date2num(latest_time), latest_temperature),
                                                   xytext=(-80, 25), textcoords='offset points',
                                                   bbox=dict(boxstyle='round,pad=0.4', facecolor='#FF6347', alpha=0.9, edgecolor='white'),
                                                   fontsize=11, fontweight='bold', color='white',
                                                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='white', lw=1.5))
                
                # Keep fixed y-axis ranges (20-100% humidity, 10-40°C temperature)
                # Auto-scaling disabled to maintain consistent scale
                # if len(humidity_buffer) > 0:
                #     h_values = list(humidity_buffer)
                #     h_min, h_max = min(h_values), max(h_values)
                #     h_padding = (h_max - h_min) * 0.1 if h_max != h_min else 5
                #     ax1.set_ylim(max(0, h_min - h_padding), min(100, h_max + h_padding))
                
                # if len(temperature_buffer) > 0:
                #     t_values = list(temperature_buffer)
                #     t_min, t_max = min(t_values), max(t_values)
                #     t_padding = (t_max - t_min) * 0.1 if t_max != t_min else 2
                #     ax2.set_ylim(t_min - t_padding, t_max + t_padding)
                
                # Force redraw
                fig.canvas.draw_idle()
            
            return humidity_line, temperature_line
        
        # Make window more visible
        try:
            mngr = fig.canvas.manager
            mngr.window.wm_attributes('-topmost', True)
            mngr.window.wm_attributes('-topmost', False)
            mngr.window.lift()
        except:
            pass  # Skip if window manager commands fail
        
        # Create animation (blit=False to allow axis updates)
        ani = animation.FuncAnimation(
            fig, update_plot, interval=100, blit=False, cache_frame_data=False
        )
        
        plt.tight_layout()
        plt.show()
            
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {PORT}")
        print(f"Details: {e}")
        print("\nTroubleshooting:")
        print("1. Check if Arduino is connected")
        print("2. Verify the port name with: arduino-cli board list")
        print("3. Make sure no other program is using the port")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n" + "-" * 50)
        print("Serial monitor stopped by user")
        ser.close()
        sys.exit(0)
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    read_serial_with_plot()
