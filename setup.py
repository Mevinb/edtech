# Quick Setup Script for AI Study Assistant
import os
import subprocess
import sys
from pathlib import Path

def install_dependencies():
    """Install required Python packages"""
    print("🔧 Installing dependencies...")
    
    # Core packages (always install)
    core_packages = [
        "streamlit>=1.28.1",
        "fastapi>=0.104.1", 
        "uvicorn>=0.24.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "requests>=2.31.0",
        "pandas>=2.1.3",
        "numpy>=1.25.2"
    ]
    
    # PDF processing packages
    pdf_packages = [
        "PyPDF2>=3.0.1",
        "pdfplumber>=0.10.3", 
        "pymupdf>=1.23.8",
        "Pillow>=10.1.0"
    ]
    
    # AI packages (optional)
    ai_packages = [
        "openai>=1.3.5",
        "transformers>=4.36.2",
        "torch>=2.1.1",
        "sentence-transformers>=2.2.2"
    ]
    
    try:
        # Install core packages
        print("📦 Installing core packages...")
        for package in core_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # Install PDF packages
        print("📄 Installing PDF processing packages...")
        for package in pdf_packages:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        
        # Try to install AI packages
        print("🤖 Installing AI packages (this may take a while)...")
        for package in ai_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installed successfully")
            except subprocess.CalledProcessError:
                print(f"⚠️ Failed to install {package}, skipping...")
        
        print("✅ Dependencies installation completed!")
        
    except Exception as e:
        print(f"❌ Error installing dependencies: {str(e)}")
        print("🔧 Please install manually using: pip install -r requirements.txt")

def setup_environment():
    """Setup environment and configuration"""
    print("🔧 Setting up environment...")
    
    # Create .env file if it doesn't exist
    if not os.path.exists('.env'):
        with open('.env.example', 'r') as example:
            content = example.read()
        
        with open('.env', 'w') as env_file:
            env_file.write(content)
        
        print("✅ Created .env file from template")
        print("🔑 Please edit .env file and add your API keys if needed")
    
    # Create necessary directories
    directories = [
        'data/uploads',
        'data/processed', 
        'data/database',
        'models',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created project directories")

def test_installation():
    """Test if everything is working"""
    print("🧪 Testing installation...")
    
    try:
        # Test imports
        import streamlit
        print("✅ Streamlit: OK")
        
        try:
            import PyPDF2
            print("✅ PDF Processing: OK")
        except ImportError:
            print("⚠️ PDF Processing: Some packages missing")
        
        try:
            import openai
            print("✅ OpenAI: Available")
        except ImportError:
            print("ℹ️ OpenAI: Not installed (optional)")
        
        try:
            import transformers
            print("✅ Transformers: Available")
        except ImportError:
            print("ℹ️ Transformers: Not installed (optional)")
        
        print("✅ Installation test completed!")
        
    except Exception as e:
        print(f"❌ Installation test failed: {str(e)}")

def main():
    """Main setup function"""
    print("🚀 AI Study Assistant - Quick Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Setup steps
    setup_environment()
    install_dependencies()
    test_installation()
    
    print("\n🎉 Setup Complete!")
    print("=" * 50)
    print("📚 To start the AI Study Assistant:")
    print("   1. Edit .env file with your API keys (optional)")
    print("   2. Run: streamlit run app.py")
    print("   3. Open browser at: http://localhost:8501")
    print("\n📖 For detailed instructions, see README.md")

if __name__ == "__main__":
    main()
