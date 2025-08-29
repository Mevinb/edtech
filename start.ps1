# PowerShell launcher for AI Study Assistant
Write-Host "🚀 Starting AI Study Assistant..." -ForegroundColor Green
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Install dependencies if requirements.txt exists
if (Test-Path "requirements.txt") {
    Write-Host "📚 Installing dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# Check if .env exists, if not create from example
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "🔧 Creating .env file from template..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "⚠️ Please edit .env file and add your API keys if needed" -ForegroundColor Yellow
    }
}

# Start the application
Write-Host "🎯 Starting Streamlit application..." -ForegroundColor Green
Write-Host ""
Write-Host "📖 Your AI Study Assistant will open in your browser" -ForegroundColor Cyan
Write-Host "🌐 URL: http://localhost:8501" -ForegroundColor Cyan
Write-Host "🛑 Press Ctrl+C to stop the application" -ForegroundColor Yellow
Write-Host ""

try {
    streamlit run app.py
} catch {
    Write-Host "❌ Error starting application: $_" -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
