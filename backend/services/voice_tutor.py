"""
Voice Tutor Service
Provides Text-to-Speech (TTS) and Speech-to-Text (STT) functionality
"""

import os
import tempfile
import base64
from typing import Optional, Dict, Any
from pathlib import Path
import logging

# Try to import speech recognition libraries
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("SpeechRecognition not available. Install with: pip install speechrecognition")

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available. Install with: pip install pyttsx3")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available. Install with: pip install gtts")

logger = logging.getLogger(__name__)

class VoiceTutor:
    """Voice Tutor for speech-to-text and text-to-speech functionality"""
    
    def __init__(self):
        self.recognizer = None
        self.tts_engine = None
        self.microphone = None
        
        # Initialize available services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize speech recognition and TTS services"""
        
        # Initialize Speech Recognition
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                
                # Adjust for ambient noise
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                logger.info("Speech recognition initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing speech recognition: {e}")
        
        # Initialize TTS Engine
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
                
                # Configure TTS settings
                self.tts_engine.setProperty('rate', 150)  # Speed of speech
                self.tts_engine.setProperty('volume', 0.8)  # Volume level
                
                # Try to set a pleasant voice
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Prefer female voice if available
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
                
                logger.info("TTS engine initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing TTS engine: {e}")
    
    def is_voice_input_available(self) -> bool:
        """Check if voice input is available"""
        return SPEECH_RECOGNITION_AVAILABLE and self.recognizer is not None
    
    def is_voice_output_available(self) -> bool:
        """Check if voice output is available"""
        return (PYTTSX3_AVAILABLE and self.tts_engine is not None) or GTTS_AVAILABLE
    
    def listen_for_question(self, timeout: int = 5, phrase_timeout: int = 1) -> Optional[str]:
        """
        Listen for a spoken question from the user
        
        Args:
            timeout: Maximum time to wait for speech
            phrase_timeout: Seconds of silence to mark end of phrase
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.is_voice_input_available():
            return None
        
        try:
            # Listen for audio
            with self.microphone as source:
                # Listen for speech
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            # Recognize speech using Google's free service
            try:
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Speech recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                return None
                
        except sr.WaitTimeoutError:
            logger.warning("No speech detected within timeout")
            return None
        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return None
    
    def speak_text(self, text: str, use_gtts: bool = False) -> Optional[str]:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            use_gtts: Whether to use Google TTS (requires internet)
            
        Returns:
            Audio file path if using gTTS, None if using local TTS
        """
        if not text or not text.strip():
            return None
        
        # Clean text for speech
        clean_text = self._clean_text_for_speech(text)
        
        # Use local TTS first (more reliable for real-time)
        if self.tts_engine and not use_gtts:
            try:
                self._speak_with_local_tts(clean_text)
                return "local_tts_used"  # Indicate local TTS was used
            except Exception as e:
                logger.warning(f"Local TTS failed, trying Google TTS: {e}")
        
        # Try Google TTS as fallback or if specifically requested
        if GTTS_AVAILABLE:
            try:
                return self._speak_with_gtts(clean_text)
            except Exception as e:
                logger.error(f"Google TTS failed: {e}")
                # Try local TTS as final fallback
                if self.tts_engine:
                    try:
                        self._speak_with_local_tts(clean_text)
                        return "local_tts_fallback"
                    except Exception as local_e:
                        logger.error(f"Local TTS fallback failed: {local_e}")
        
        logger.error("No TTS engine available")
        return None
    
    def _speak_with_gtts(self, text: str) -> str:
        """Speak using Google TTS and return audio file path"""
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        # Generate speech
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(temp_path)
        
        return temp_path
    
    def _speak_with_local_tts(self, text: str):
        """Speak using local TTS engine"""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text to make it more suitable for speech synthesis"""
        # Remove markdown formatting
        clean_text = text.replace('**', '').replace('*', '')
        clean_text = clean_text.replace('###', '').replace('##', '').replace('#', '')
        
        # Replace common symbols with words
        replacements = {
            '&': ' and ',
            '@': ' at ',
            '%': ' percent ',
            '$': ' dollars ',
            '+': ' plus ',
            '=': ' equals ',
            '<': ' less than ',
            '>': ' greater than ',
            '→': ' leads to ',
            '←': ' comes from ',
            '↑': ' increases ',
            '↓': ' decreases '
        }
        
        for symbol, word in replacements.items():
            clean_text = clean_text.replace(symbol, word)
        
        # Remove excessive whitespace
        clean_text = ' '.join(clean_text.split())
        
        # Limit length for TTS
        if len(clean_text) > 500:
            sentences = clean_text.split('. ')
            clean_text = '. '.join(sentences[:3]) + '.'
        
        return clean_text
    
    def get_voice_settings(self) -> Dict[str, Any]:
        """Get current voice settings"""
        settings = {
            "input_available": self.is_voice_input_available(),
            "output_available": self.is_voice_output_available(),
            "services": {
                "speech_recognition": SPEECH_RECOGNITION_AVAILABLE,
                "pyttsx3": PYTTSX3_AVAILABLE,
                "gtts": GTTS_AVAILABLE
            }
        }
        
        if self.tts_engine:
            try:
                settings["tts_rate"] = self.tts_engine.getProperty('rate')
                settings["tts_volume"] = self.tts_engine.getProperty('volume')
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    current_voice = self.tts_engine.getProperty('voice')
                    settings["current_voice"] = current_voice
                    settings["available_voices"] = len(voices)
            except:
                pass
        
        return settings
    
    def set_voice_rate(self, rate: int):
        """Set speech rate (words per minute)"""
        if self.tts_engine:
            try:
                self.tts_engine.setProperty('rate', max(50, min(300, rate)))
            except Exception as e:
                logger.error(f"Error setting voice rate: {e}")
    
    def set_voice_volume(self, volume: float):
        """Set speech volume (0.0 to 1.0)"""
        if self.tts_engine:
            try:
                self.tts_engine.setProperty('volume', max(0.0, min(1.0, volume)))
            except Exception as e:
                logger.error(f"Error setting voice volume: {e}")

# Helper functions for Streamlit integration
def create_audio_player_html(audio_file_path: str) -> str:
    """Create HTML audio player for Streamlit"""
    try:
        with open(audio_file_path, 'rb') as audio_file:
            audio_data = audio_file.read()
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        audio_html = f"""
        <audio controls autoplay style="width: 100%;">
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        return audio_html
    except Exception as e:
        logger.error(f"Error creating audio player: {e}")
        return "<p>Error playing audio</p>"

def get_microphone_html() -> str:
    """Get HTML for microphone interface"""
    return """
    <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin: 1rem 0;">
        <p style="color: white; margin: 0.5rem 0;"><strong>🎤 Voice Input</strong></p>
        <p style="color: white; font-size: 0.9rem; margin: 0;">Click the button below and speak your question</p>
    </div>
    """

# Example usage
if __name__ == "__main__":
    # Test voice tutor functionality
    voice_tutor = VoiceTutor()
    
    print("Voice Tutor Status:")
    print(f"Input available: {voice_tutor.is_voice_input_available()}")
    print(f"Output available: {voice_tutor.is_voice_output_available()}")
    
    # Test TTS
    if voice_tutor.is_voice_output_available():
        voice_tutor.speak_text("Hello! I am your AI voice tutor. How can I help you learn today?")
