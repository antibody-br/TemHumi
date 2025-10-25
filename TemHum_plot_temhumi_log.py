#!/usr/bin/env python3
"""
TemHumi Log Plotter
Reads and plots temperature and humidity data from TemHumi.log file
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import sys
import csv
import numpy as np
from scipy.interpolate import make_interp_spline

def plot_temhumi_log(log_file="TemHumi.log"):
    """
    Read and plot temperature and humidity data from log file
    """
    
    # Check if log file exists
    if not os.path.exists(log_file):
        print(f"Error: Log file '{log_file}' not found!")
        print("Make sure you're running this script in the same directory as TemHumi.log")
        return
    
    try:
        # Read the CSV file, skipping comment lines that start with #
        print(f"Reading data from {log_file}...")
        
        timestamps = []
        humidity_values = []
        temperature_values = []
        
        with open(log_file, 'r') as file:
            # Skip comment lines
            lines = [line for line in file if not line.strip().startswith('#')]
            
            # Parse CSV data
            csv_reader = csv.DictReader(lines)
            
            for row in csv_reader:
                try:
                    timestamp = datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S')
                    humidity = float(row['Humidity'])
                    temperature = float(row['Temperature'])
                    
                    timestamps.append(timestamp)
                    humidity_values.append(humidity)
                    temperature_values.append(temperature)
                except (ValueError, KeyError) as e:
                    print(f"Skipping invalid row: {row} - Error: {e}")
                    continue
        
        if len(timestamps) == 0:
            print("No valid data found in log file!")
            return
            
        print(f"Loaded {len(timestamps)} raw data points")
        print(f"Time range: {min(timestamps)} to {max(timestamps)}")
        print(f"Humidity range: {min(humidity_values)}% to {max(humidity_values)}%")
        print(f"Temperature range: {min(temperature_values)}°C to {max(temperature_values)}°C")
        
        # Aggregate data into 10-minute intervals
        print("Aggregating data into 10-minute intervals...")
        
        # Create 10-minute time bins
        start_time = min(timestamps)
        end_time = max(timestamps)
        
        # Round start time down to nearest 10 minutes
        start_rounded = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
        
        aggregated_timestamps = []
        aggregated_humidity = []
        aggregated_temperature = []
        
        current_time = start_rounded
        while current_time <= end_time:
            next_time = current_time + timedelta(minutes=10)
            
            # Find all data points in this 10-minute window
            window_humidity = []
            window_temperature = []
            
            for i, ts in enumerate(timestamps):
                if current_time <= ts < next_time:
                    window_humidity.append(humidity_values[i])
                    window_temperature.append(temperature_values[i])
            
            # If we have data in this window, calculate averages
            if window_humidity and window_temperature:
                aggregated_timestamps.append(current_time + timedelta(minutes=5))  # Use middle of interval
                aggregated_humidity.append(sum(window_humidity) / len(window_humidity))
                aggregated_temperature.append(sum(window_temperature) / len(window_temperature))
            
            current_time = next_time
        
        # Update variables to use aggregated data
        timestamps = aggregated_timestamps
        humidity_values = aggregated_humidity
        temperature_values = aggregated_temperature
        
        print(f"Aggregated to {len(timestamps)} data points (10-minute intervals)")
        
        # Set up the plot with dark theme
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
        fig.patch.set_facecolor('black')
        
        # Plot humidity (top subplot) - Smooth curve
        if len(timestamps) > 3:  # Need at least 4 points for spline interpolation
            # Convert timestamps to numerical values for interpolation
            time_nums = mdates.date2num(timestamps)
            
            # Create smooth interpolation
            time_smooth = np.linspace(time_nums[0], time_nums[-1], len(timestamps) * 3)
            try:
                spl_humidity = make_interp_spline(time_nums, humidity_values, k=3)
                humidity_smooth = spl_humidity(time_smooth)
                
                # Convert back to datetime objects
                timestamps_smooth = mdates.num2date(time_smooth)
                
                ax1.plot(timestamps_smooth, humidity_smooth, 
                        color='#00BFFF', linewidth=2, alpha=0.8,
                        label=f'Humidity (avg: {sum(humidity_values)/len(humidity_values):.1f}%)')
                
                # Also plot original data points
                ax1.scatter(timestamps, humidity_values, 
                           color='#00BFFF', s=20, alpha=0.6, zorder=5)
            except:
                # Fallback to regular plot if interpolation fails
                ax1.plot(timestamps, humidity_values, 
                        color='#00BFFF', linewidth=2,
                        label=f'Humidity (avg: {sum(humidity_values)/len(humidity_values):.1f}%)')
        else:
            # Regular plot for few data points
            ax1.plot(timestamps, humidity_values, 
                    color='#00BFFF', linewidth=2,
                    label=f'Humidity (avg: {sum(humidity_values)/len(humidity_values):.1f}%)')
        ax1.set_ylabel('Humidity (%)', fontsize=12, color='white')
        ax1.set_title('Temperature and Humidity Data from Log File', 
                     fontsize=14, fontweight='bold', color='white')
        ax1.grid(True, alpha=0.3, color='gray', which='major')
        ax1.grid(True, alpha=0.15, color='gray', which='minor')
        ax1.tick_params(colors='white')
        ax1.set_facecolor('black')
        
        # Set fixed humidity range
        ax1.set_ylim(20, 100)  # Fixed humidity range 20-100%
        
        # Add legend for humidity
        legend1 = ax1.legend(loc='upper right')
        legend1.get_frame().set_facecolor('black')
        legend1.get_frame().set_edgecolor('white')
        for text in legend1.get_texts():
            text.set_color('white')
        
        # Plot temperature (bottom subplot) - Smooth curve
        if len(timestamps) > 3:  # Need at least 4 points for spline interpolation
            # Convert timestamps to numerical values for interpolation
            time_nums = mdates.date2num(timestamps)
            
            # Create smooth interpolation
            time_smooth = np.linspace(time_nums[0], time_nums[-1], len(timestamps) * 3)
            try:
                spl_temperature = make_interp_spline(time_nums, temperature_values, k=3)
                temperature_smooth = spl_temperature(time_smooth)
                
                # Convert back to datetime objects
                timestamps_smooth = mdates.num2date(time_smooth)
                
                ax2.plot(timestamps_smooth, temperature_smooth, 
                        color='#FF6347', linewidth=2, alpha=0.8,
                        label=f'Temperature (avg: {sum(temperature_values)/len(temperature_values):.1f}°C)')
                
                # Also plot original data points
                ax2.scatter(timestamps, temperature_values, 
                           color='#FF6347', s=20, alpha=0.6, zorder=5)
            except:
                # Fallback to regular plot if interpolation fails
                ax2.plot(timestamps, temperature_values, 
                        color='#FF6347', linewidth=2,
                        label=f'Temperature (avg: {sum(temperature_values)/len(temperature_values):.1f}°C)')
        else:
            # Regular plot for few data points
            ax2.plot(timestamps, temperature_values, 
                    color='#FF6347', linewidth=2,
                    label=f'Temperature (avg: {sum(temperature_values)/len(temperature_values):.1f}°C)')
        ax2.set_xlabel('Time', fontsize=12, color='white')
        ax2.set_ylabel('Temperature (°C)', fontsize=12, color='white')
        ax2.grid(True, alpha=0.3, color='gray', which='major')
        ax2.grid(True, alpha=0.15, color='gray', which='minor')
        ax2.tick_params(colors='white')
        ax2.set_facecolor('black')
        
        # Set fixed temperature range
        ax2.set_ylim(10, 40)  # Fixed temperature range 10-40°C
        
        # Add legend for temperature
        legend2 = ax2.legend(loc='upper right')
        legend2.get_frame().set_facecolor('black')
        legend2.get_frame().set_edgecolor('white')
        for text in legend2.get_texts():
            text.set_color('white')
        
        # Format x-axis for time display - More specific timestamps
        time_span = (max(timestamps) - min(timestamps)).total_seconds()
        
        if time_span <= 1800:  # Less than 30 minutes
            # Show hours, minutes and seconds with 2-minute intervals
            date_formatter = mdates.DateFormatter('%H:%M:%S')
            ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=2))
            ax2.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
        elif time_span <= 3600:  # Less than 1 hour
            # Show hours, minutes and seconds with 5-minute intervals
            date_formatter = mdates.DateFormatter('%H:%M:%S')
            ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=5))
            ax2.xaxis.set_minor_locator(mdates.MinuteLocator(interval=1))
        elif time_span <= 7200:  # Less than 2 hours
            # Show hours and minutes with 10-minute intervals
            date_formatter = mdates.DateFormatter('%H:%M:%S')
            ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            ax2.xaxis.set_minor_locator(mdates.MinuteLocator(interval=5))
        elif time_span <= 86400:  # Less than 1 day
            # Show hours and minutes with 30-minute intervals
            date_formatter = mdates.DateFormatter('%H:%M')
            ax2.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            ax2.xaxis.set_minor_locator(mdates.MinuteLocator(interval=10))
        else:
            # Show date, hours and minutes
            date_formatter = mdates.DateFormatter('%m-%d %H:%M')
            ax2.xaxis.set_major_locator(mdates.HourLocator(interval=3))
            ax2.xaxis.set_minor_locator(mdates.HourLocator(interval=1))
        
        # Apply formatting to both subplots
        ax1.xaxis.set_major_formatter(date_formatter)
        ax1.xaxis.set_major_locator(ax2.xaxis.get_major_locator())
        ax1.xaxis.set_minor_locator(ax2.xaxis.get_minor_locator())
        ax1.tick_params(axis='x', which='minor', length=3, color='gray')
        ax1.tick_params(axis='x', which='major', length=6, color='white')
        
        ax2.xaxis.set_major_formatter(date_formatter)
        ax2.tick_params(axis='x', which='minor', length=3, color='gray')
        ax2.tick_params(axis='x', which='major', length=6, color='white')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=10)
        
        # Add statistics text box
        stats_text = f"""Data Points: {len(timestamps)}
Time Span: {max(timestamps) - min(timestamps)}
Humidity: {min(humidity_values):.1f}% - {max(humidity_values):.1f}% (avg: {sum(humidity_values)/len(humidity_values):.1f}%)
Temperature: {min(temperature_values):.1f}°C - {max(temperature_values):.1f}°C (avg: {sum(temperature_values)/len(temperature_values):.1f}°C)"""
        
        fig.text(0.02, 0.02, stats_text, fontsize=9, color='white', 
                bbox=dict(boxstyle="round,pad=0.3", facecolor='black', edgecolor='white', alpha=0.8))
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)  # Make room for stats
        
        # Save the plot
        output_file = "temhumi_plot.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight', 
                   facecolor='black', edgecolor='white')
        print(f"Plot saved as: {output_file}")
        
        # Show the plot
        plt.show()
        
    except Exception as e:
        print(f"Error reading or plotting data: {e}")
        return

def main():
    """Main function"""
    # Get script directory to find log file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(script_dir, "TemHumi.log")
    
    print("TemHumi Log Plotter")
    print("=" * 50)
    
    # Check if custom log file is provided as argument
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
        print(f"Using log file: {log_file}")
    else:
        print(f"Using default log file: {log_file}")
    
    plot_temhumi_log(log_file)

if __name__ == "__main__":
    main()