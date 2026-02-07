#!/bin/bash

# Check for python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "Python is not installed or not in PATH."
    exit 1
fi

echo "Using Python command: $PYTHON_CMD"

# Check/Create venv
VENV_DIR=".venv"

if [ -d "$VENV_DIR" ] && [ ! -f "$VENV_DIR/bin/activate" ]; then
    echo "Detected incompatible virtual environment (likely from Windows). Recreating..."
    rm -rf "$VENV_DIR"
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activate venv
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
else
    echo "Could not find activation script at $VENV_DIR/bin/activate"
    exit 1
fi

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing requirements..."
    pip install -r requirements.txt
fi

# Run Main Script
echo "Running Stock Data Analysis..."
python main.py

# Deactivate is automatic when script ends as it runs in subshell if executed directly, 
# but source won't work in subshell context anyway for parent. 
# However, usually for run scripts we just want the app to run.
