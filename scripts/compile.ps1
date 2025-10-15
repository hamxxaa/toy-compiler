# PowerShell script for Toy Compiler
# To run this file: powershell -ExecutionPolicy Bypass -File compile.ps1

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir

# Detect Python command
$pythonCmd = $null

if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} else {
    Write-Host "Error: Python not found!" -ForegroundColor Red
    Write-Host "Please ensure that Python is installed and available in PATH." -ForegroundColor Yellow
    exit 1
}

# Run main.py from project root
Set-Location $ProjectRoot
& $pythonCmd main.py @args