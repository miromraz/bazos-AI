#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment and ensuring dependencies are installed..."
source .venv/bin/activate
pip install -r requirements.txt > /dev/null 2>&1

if [ -f ".env" ]; then
    echo "Loading .env file..."
    export $(grep -v '^#' .env | xargs)
fi

echo "Starting Bazos AI Scraper..."
python app.py
