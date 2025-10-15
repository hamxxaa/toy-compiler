#!/bin/bash
# Cross-platform wrapper for Toy Compiler

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# Detect Python command
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found!"
    exit 1
fi

# Run compiler from project root
cd "${PROJECT_ROOT}"
"${PYTHON_CMD}" main.py "$@"