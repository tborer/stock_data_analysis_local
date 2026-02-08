#!/bin/bash

# Navigate to the project directory
# This ensures relative paths (like config/sites.yaml) work correctly
cd "/home/travis/AntiGravity Projects/stock-data-analysis-local/stock_data_analysis_local" || exit

# Activate the virtual environment
source .venv/bin/activate

# Run the main script
# Output is redirected to a log file with a timestamp
LOG_FILE="logs/cron_job_$(date +\%Y-\%m-\%d).log"
mkdir -p logs

echo "Starting job at $(date)" >> "$LOG_FILE"
python3 main.py >> "$LOG_FILE" 2>&1
echo "Job finished at $(date)" >> "$LOG_FILE"
