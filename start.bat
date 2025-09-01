@echo off
echo 🚀 Starting AI Study Assistant...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo 📚 Installing dependencies...
    pip install -r requirements.txt
)

REM Check if .env exists, if not create from example
if not exist ".env" (
    if exist ".env.example" (
        echo 🔧 Creating .env file from template...
        copy .env.example .env
        echo ⚠️ Please edit .env file and add your API keys if needed
    )
)

REM Start the application
echo 🎯 Starting Streamlit application...
echo.
echo 📖 Your AI Study Assistant will open in your browser
echo 🌐 URL: http://localhost:8501
echo �️ Voice Tutor feature available in the app
echo �🛑 Press Ctrl+C to stop the application
echo.

streamlit run app_simple.py

pause
