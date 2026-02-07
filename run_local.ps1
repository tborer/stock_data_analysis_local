# Check for python command
$PythonCmd = "python"
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCmd = "python3"
}
elseif (!(Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}

Write-Host "Using Python command: $PythonCmd"

# Check/Create venv
# Check/Create venv
$VenvDir = ".venv"

if (Test-Path $VenvDir) {
    # Check if we have Windows structure
    if (!(Test-Path "$VenvDir\Scripts\activate") -and !(Test-Path "$VenvDir/bin/activate")) {
        # This one is trickier cross platform as path separators differ
        # But for Windows execution, if Scripts is missing but bin exists, it's likely Linux venv
        if (Test-Path "$VenvDir/bin/activate") {
            Write-Host "Detected incompatible virtual environment (likely from Linux). Recreating..."
            Remove-Item -Recurse -Force $VenvDir
        }
    }
}

if (!(Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..."
    & $PythonCmd -m venv $VenvDir
}

# Activate venv
if ($IsLinux) {
    $VenvActivate = "$VenvDir/bin/Activate.ps1"
}
else {
    $VenvActivate = "$VenvDir\Scripts\Activate.ps1"
}

if (Test-Path $VenvActivate) {
    . $VenvActivate
}
else {
    Write-Host "Could not find activation script at $VenvActivate" -ForegroundColor Red
    exit 1
}

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements..."
    pip install -r requirements.txt | Out-Null
}

# Run Main Script
Write-Host "Running Stock Data Aanalysis..."
python main.py

# Deactivate
deactivate
