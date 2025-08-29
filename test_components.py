#!/usr/bin/env python
"""
Test script to verify AI Study Assistant components
"""
import sys
import os
from pathlib import Path

def test_imports():
    """Test if required modules can be imported"""
    print("🧪 Testing AI Study Assistant Components")
    print("=" * 50)
    
    # Test basic imports
    try:
        import streamlit
        print("✅ Streamlit:", streamlit.__version__)
    except ImportError as e:
        print("❌ Streamlit:", str(e))
    
    try:
        import PyPDF2
        print("✅ PyPDF2: Available")
    except ImportError as e:
        print("❌ PyPDF2:", str(e))
    
    try:
        import pdfplumber
        print("✅ pdfplumber: Available")
    except ImportError as e:
        print("❌ pdfplumber:", str(e))
    
    # Test our backend modules
    print("\n🔧 Testing Backend Modules:")
    try:
        from backend.models.document import Document
        print("✅ Document model: OK")
    except ImportError as e:
        print("❌ Document model:", str(e))
    
    try:
        from backend.services.pdf_processor import PDFProcessor
        processor = PDFProcessor()
        print("✅ PDF Processor: OK")
    except ImportError as e:
        print("❌ PDF Processor:", str(e))
    
    try:
        from backend.services.ai_engine import AIEngine
        engine = AIEngine()
        print("✅ AI Engine: OK")
    except ImportError as e:
        print("❌ AI Engine:", str(e))
    
    try:
        from backend.utils.database import DatabaseManager
        db = DatabaseManager()
        print("✅ Database Manager: OK")
    except ImportError as e:
        print("❌ Database Manager:", str(e))
    
    print("\n🎯 Ready to run Streamlit app!")
    print("Command: streamlit run app_simple.py")

def test_demo_content():
    """Test demo content processing"""
    print("\n📖 Testing Demo Content Processing:")
    
    try:
        from backend.services.ai_engine import AIEngine
        
        demo_text = """
        Matter in Our Surroundings
        
        Everything around us is made up of matter. Matter is anything that has mass and occupies space.
        Matter is made up of particles. These particles are very small.
        
        States of Matter:
        1. Solid State
        2. Liquid State
        3. Gaseous State
        """
        
        engine = AIEngine()
        summary = engine.generate_summary(demo_text)
        
        print("✅ Summary generated successfully")
        print(f"   Overview length: {len(summary.get('overview', ''))}")
        print(f"   Key points: {len(summary.get('key_points', []))}")
        
    except Exception as e:
        print(f"⚠️ Demo processing test failed: {str(e)}")

if __name__ == "__main__":
    test_imports()
    test_demo_content()
