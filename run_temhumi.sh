#!/bin/bash

# TemHumi Monitor Launcher Script
# This script launches the Arduino DHT22 Temperature and Humidity Monitor

echo "🌡️ TemHumi Monitor - Arduino DHT22 Sensor"
echo "=========================================="
echo ""

# Check if the Python script exists
SCRIPT_PATH="$(dirname "$0")/TemHum_read_serial_DHT.py"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Error: TemHum_read_serial_DHT.py not found!"
    echo "Make sure this script is in the same directory as TemHum_read_serial_DHT.py"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "📍 Script found: $SCRIPT_PATH"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed!"
    echo "Please install Python 3 from https://www.python.org"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "🐍 Python found: $(python3 --version)"

# Check for required Python packages
echo "📦 Checking required packages..."

PACKAGES=("serial" "matplotlib" "numpy")
MISSING_PACKAGES=()

for package in "${PACKAGES[@]}"; do
    if ! python3 -c "import $package" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

# Handle pyserial vs serial naming
if ! python3 -c "import serial" 2>/dev/null; then
    if [[ " ${MISSING_PACKAGES[@]} " =~ " serial " ]]; then
        MISSING_PACKAGES=(${MISSING_PACKAGES[@]/serial/})
        MISSING_PACKAGES+=("pyserial")
    fi
fi

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo "❌ Missing required packages: ${MISSING_PACKAGES[*]}"
    echo ""
    echo "To install missing packages, run:"
    echo "pip3 install ${MISSING_PACKAGES[*]}"
    echo ""
    read -p "Do you want to install them now? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Installing packages..."
        pip3 install "${MISSING_PACKAGES[@]}"
        
        if [ $? -ne 0 ]; then
            echo "❌ Failed to install packages!"
            read -p "Press Enter to exit..."
            exit 1
        fi
        echo "✅ Packages installed successfully!"
    else
        echo "Please install the required packages manually and run this script again."
        read -p "Press Enter to exit..."
        exit 1
    fi
fi

echo "✅ All packages are available"
echo ""

# Launch the program
echo "🚀 Starting TemHumi Monitor..."
echo "Press Ctrl+C to stop the program"
echo ""

# Change to script directory to ensure log files are created in the right place
cd "$(dirname "$0")"

# Run the Python script
python3 "$SCRIPT_PATH"

echo ""
echo "Program ended."
read -p "Press Enter to close..."