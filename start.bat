@echo off

REM Create virtual environment if it doesn't exist
if not exist venv (
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt

REM Create output directories
if not exist output\images mkdir output\images
if not exist output\models mkdir output\models

REM Start the backend server in a new window
start cmd /k "venv\Scripts\python.exe main.py"

REM Wait for the backend to start
timeout /t 5

REM Start the Streamlit interface
venv\Scripts\streamlit.exe run app.py 