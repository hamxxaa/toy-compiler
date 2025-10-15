@echo off
REM Windows batch file for Toy Compiler

REM Get batch file directory
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

REM Detect Python command
where python >nul 2>nul
if %errorlevel% == 0 (
    set PYTHON_CMD=python
    goto found_python
)

where python3 >nul 2>nul
if %errorlevel% == 0 (
    set PYTHON_CMD=python3
    goto found_python
)

where py >nul 2>nul
if %errorlevel% == 0 (
    set PYTHON_CMD=py
    goto found_python
)

echo Error: Python not found!
echo Please ensure that Python is installed and available in PATH.
exit /b 1

:found_python
REM Run main.py from project root
cd /d "%PROJECT_ROOT%"
%PYTHON_CMD% main.py %*