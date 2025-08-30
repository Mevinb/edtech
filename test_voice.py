"""
Voice Tutor Diagnostic Test
Tests the voice functionality to identify issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_voice_imports():
    """Test if voice packages are properly imported"""
    print("Testing voice package imports...")
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition imported successfully")
    except ImportError as e:
        print(f"❌ speech_recognition import failed: {e}")
    
    try:
        import pyttsx3
        print("✅ pyttsx3 imported successfully")
    except ImportError as e:
        print(f"❌ pyttsx3 import failed: {e}")
    
    try:
        from gtts import gTTS
        print("✅ gtts imported successfully")
    except ImportError as e:
        print(f"❌ gtts import failed: {e}")
    
    try:
        import pyaudio
        print("✅ pyaudio imported successfully")
    except ImportError as e:
        print(f"❌ pyaudio import failed: {e}")

def test_tts_engine():
    """Test TTS engine initialization"""
    print("\nTesting TTS engine initialization...")
    
    try:
        import pyttsx3
        engine = pyttsx3.init()
        print("✅ TTS engine initialized")
        
        # Test basic properties
        rate = engine.getProperty('rate')
        volume = engine.getProperty('volume')
        voices = engine.getProperty('voices')
        
        print(f"  - Speech rate: {rate}")
        print(f"  - Volume: {volume}")
        print(f"  - Available voices: {len(voices) if voices else 0}")
        
        if voices:
            for i, voice in enumerate(voices[:2]):  # Show first 2 voices
                print(f"    Voice {i}: {voice.name}")
        
        # Test simple speech
        print("Testing speech synthesis...")
        engine.say("Hello, this is a test")
        engine.runAndWait()
        print("✅ Speech test completed")
        
    except Exception as e:
        print(f"❌ TTS engine test failed: {e}")

def test_gtts():
    """Test Google TTS"""
    print("\nTesting Google TTS...")
    
    try:
        from gtts import gTTS
        import tempfile
        import os
        
        # Create test audio
        tts = gTTS(text="Hello, this is a Google TTS test", lang='en', slow=False)
        
        # Save to temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        tts.save(temp_path)
        
        if os.path.exists(temp_path):
            print(f"✅ Google TTS audio file created: {temp_path}")
            print(f"  File size: {os.path.getsize(temp_path)} bytes")
            
            # Clean up
            os.unlink(temp_path)
            print("✅ Temp file cleaned up")
        else:
            print("❌ Google TTS file not created")
            
    except Exception as e:
        print(f"❌ Google TTS test failed: {e}")

def test_voice_tutor_service():
    """Test the VoiceTutor service"""
    print("\nTesting VoiceTutor service...")
    
    try:
        from backend.services.voice_tutor import VoiceTutor
        
        voice_tutor = VoiceTutor()
        print("✅ VoiceTutor service initialized")
        
        # Check availability
        input_available = voice_tutor.is_voice_input_available()
        output_available = voice_tutor.is_voice_output_available()
        
        print(f"  - Voice input available: {input_available}")
        print(f"  - Voice output available: {output_available}")
        
        # Get settings
        settings = voice_tutor.get_voice_settings()
        print(f"  - Settings: {settings}")
        
        # Test TTS with short text
        if output_available:
            print("Testing voice output...")
            result = voice_tutor.speak_text("Testing voice output", use_gtts=False)
            print(f"✅ Voice output test completed. Result: {result}")
        
    except Exception as e:
        print(f"❌ VoiceTutor service test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🎤 Voice Tutor Diagnostic Test")
    print("=" * 50)
    
    test_voice_imports()
    test_tts_engine()
    test_gtts()
    test_voice_tutor_service()
    
    print("\n" + "=" * 50)
    print("Diagnostic test completed!")
