#!/bin/bash

# TemHumi Log Plotter Shell Script
# This script activates the conda environment and runs the Python plotter

# Change to the script's directory
cd "$(dirname "$0")"

echo "Starting TemHumi Log Plotter..."
echo "Working directory: $(pwd)"

# Check if TemHumi.log exists
if [ ! -f "TemHumi.log" ]; then
    echo "Error: TemHumi.log file not found!"
    echo "Make sure you're in the correct directory with the log file."
    exit 1
fi

# Activate conda environment and run the plotter
echo "Activating conda environment 'copilot'..."

# Try different conda initialization paths
if [ -f ~/miniconda3/etc/profile.d/conda.sh ]; then
    source ~/miniconda3/etc/profile.d/conda.sh
elif [ -f ~/anaconda3/etc/profile.d/conda.sh ]; then
    source ~/anaconda3/etc/profile.d/conda.sh
elif [ -f /opt/miniconda3/etc/profile.d/conda.sh ]; then
    source /opt/miniconda3/etc/profile.d/conda.sh
else
    echo "Warning: conda.sh not found, using system Python"
fi

# Try to activate copilot environment, fall back to system python if it fails
conda activate copilot 2>/dev/null || echo "Warning: copilot environment not found, using default Python"

echo "Running Python plotter (non-interactive)..."
python plot_temhumi_noninteractive.py

echo "Plot complete! Check 'temhumi_plot.png' in this directory."

# Keep the terminal open to see results
read -p "Press Enter to exit..."