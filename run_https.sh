#!/bin/bash

# Ensure script directory is current directory
cd "$(dirname "$0")"

# Check if .venv exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please create it first."
    exit 1
fi

echo "Starting RSC Server (HTTPS Mode)..."
echo "NOTE: You will see a security warning in the browser. This is normal."

# Use python3 or python depending on system
if command -v python3 &> /dev/null; then
    python3 app.py ssl
else
    python app.py ssl
fi
