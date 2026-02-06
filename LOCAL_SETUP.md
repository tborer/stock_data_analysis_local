# Local Setup and Execution Guide

This guide explains how to run the Stock Data Analysis tool on your local machine.

## Prerequisites

- **Python**: Ensure Python 3.9+ is installed. The script supports the `py` launcher or `python` command.
- **PowerShell**: Used for the setup script.

## Configuration

1.  Copy `.env.example` to a new file named `.env`.
2.  Open `.env` and fill in your email credentials.
    - If using Gmail, you may need to generate an **App Password**.

```env
EMAIL_SENDER=your-email@xm.com
EMAIL_PASSWORD=your-app-password
EMAIL_RECIPIENT=recipient@xm.com
```

## Running the Application

Double-click `run_local.ps1` or run it from a PowerShell terminal:

```powershell
.\run_local.ps1
```

This script will automatically:
1.  Create a virtual environment (`.venv`) if one doesn't exist.
2.  Install dependencies from `requirements.txt`.
3.  Run the main analysis script.

## Output

- Console logs will show progress.
- Findings will be emailed to the configured recipient.
- `processed_urls.json` will track which articles have been analyzed to prevent duplicates.
