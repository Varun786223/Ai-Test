#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create output directories
mkdir -p output/images
mkdir -p output/models

# Start the backend server in the background
python main.py &
BACKEND_PID=$!

# Wait for the backend to start
sleep 5

# Start the Streamlit interface
streamlit run app.py

# Cleanup
kill $BACKEND_PID 