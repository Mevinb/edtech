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
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceTutor, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.recognizer = None
            self.tts_engine = None
            self.microphone = None
            self.is_speaking = False
            self.speech_stopped = False
            
            # Initialize available services
            self._initialize_services()
            VoiceTutor._initialized = True
    
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
        
        # Initialize TTS Engine with better error handling
        if PYTTSX3_AVAILABLE:
            try:
                # Check if we already have a working engine
                if self.tts_engine is None:
                    import pyttsx3
                    self.tts_engine = pyttsx3.init(driverName='sapi5', debug=False)
                    
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
                logger.warning(f"Local TTS engine failed, will use Google TTS: {e}")
                self.tts_engine = None
    
    def is_voice_input_available(self) -> bool:
        """Check if voice input is available"""
        return SPEECH_RECOGNITION_AVAILABLE and self.recognizer is not None
    
    def is_voice_output_available(self) -> bool:
        """Check if voice output is available"""
        # For now, always return True if gTTS is available to avoid local TTS conflicts
        return GTTS_AVAILABLE or (PYTTSX3_AVAILABLE and self.tts_engine is not None)
    
    def listen_for_question(self, timeout: int = 10, phrase_timeout: int = 3) -> Optional[str]:
        """
        Listen for a spoken question from the user with improved error handling
        
        Args:
            timeout: Maximum time to wait for speech (increased to 10s)
            phrase_timeout: Seconds of silence to mark end of phrase (increased to 3s)
            
        Returns:
            Transcribed text or None if failed
        """
        if not self.is_voice_input_available():
            logger.warning("Voice input not available")
            return None
        
        try:
            # Adjust for ambient noise before listening
            with self.microphone as source:
                logger.info("Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Listening for speech...")
                
                # Listen for speech with longer timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_timeout
                )
            
            logger.info("Audio captured, processing...")
            
            # Try multiple recognition services for better accuracy
            try:
                # Primary: Google Speech Recognition
                text = self.recognizer.recognize_google(audio)
                logger.info(f"Google Speech Recognition result: {text}")
                return text.strip()
            except sr.UnknownValueError:
                logger.warning("Google Speech Recognition could not understand audio")
                
                # Fallback: Try Sphinx (offline)
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Sphinx Recognition result: {text}")
                    return text.strip()
                except sr.UnknownValueError:
                    logger.warning("Sphinx could not understand audio either")
                    return None
                except sr.RequestError as e:
                    logger.warning(f"Sphinx error: {e}")
                    return None
                    
            except sr.RequestError as e:
                logger.error(f"Google Speech Recognition service error: {e}")
                
                # Fallback to Sphinx if Google fails
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    logger.info(f"Fallback Sphinx result: {text}")
                    return text.strip()
                except Exception as sphinx_error:
                    logger.error(f"All speech recognition services failed: {sphinx_error}")
                    return None
                
        except sr.WaitTimeoutError:
            logger.warning(f"No speech detected within {timeout} seconds")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during speech recognition: {e}")
            return None
    
    def speak_text(self, text: str, use_gtts: bool = True) -> Optional[str]:
        """
        Convert text to speech with improved reliability
        
        Args:
            text: Text to speak
            use_gtts: Whether to use Google TTS (default True to avoid conflicts)
            
        Returns:
            Audio file path if using gTTS, status string if using local TTS
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for TTS")
            return None
        
        # Check if speech was stopped
        if self.speech_stopped:
            logger.info("Speech was stopped, skipping TTS")
            return None
        
        # Set speaking flag
        self.is_speaking = True
        
        try:
            # Clean and prepare text for speech
            clean_text = self._clean_text_for_speech(text)
            logger.info(f"Speaking text: {clean_text[:100]}...")
            
            # Try local TTS first (more reliable and faster)
            if self.tts_engine and not use_gtts:
                try:
                    logger.info("Using local TTS engine")
                    result = self._speak_with_local_tts(clean_text)
                    logger.info("Local TTS completed successfully")
                    return "local_tts_success"
                    
                except Exception as e:
                    logger.warning(f"Local TTS failed: {e}, trying Google TTS")
                    use_gtts = True  # Fall back to Google TTS
            
            # Use Google TTS if requested or local TTS failed
            if use_gtts and GTTS_AVAILABLE:
                try:
                    logger.info("Using Google TTS")
                    return self._speak_with_gtts(clean_text)
                except Exception as e:
                    logger.error(f"Google TTS failed: {e}")
                    
                    # Final fallback to local TTS if Google fails
                    if self.tts_engine:
                        try:
                            logger.info("Final fallback to local TTS")
                            result = self._speak_with_local_tts(clean_text)
                            return "local_tts_fallback"
                        except Exception as local_error:
                            logger.error(f"All TTS methods failed: {local_error}")
                            return None
            
            logger.error("No TTS engine available or all methods failed")
            return None
            
        finally:
            # Reset speaking flag
            self.is_speaking = False
    
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
        """Speak using local TTS engine with improved error handling"""
        try:
            if not self.tts_engine:
                raise Exception("TTS engine not initialized")
            
            # Check if speech was stopped before starting
            if self.speech_stopped:
                logger.info("Speech stopped before starting local TTS")
                return
            
            # Use a more robust approach
            import threading
            import time
            
            def speak_in_thread():
                try:
                    # Configure speech properties
                    self.tts_engine.setProperty('rate', 160)
                    self.tts_engine.setProperty('volume', 0.9)
                    
                    # Speak the text
                    self.tts_engine.say(text)
                    
                    # Use runAndWait in a controlled way
                    self.tts_engine.runAndWait()
                    
                except Exception as e:
                    logger.error(f"Thread TTS error: {e}")
            
            # Run TTS in a separate thread to avoid blocking
            tts_thread = threading.Thread(target=speak_in_thread, daemon=True)
            tts_thread.start()
            
            # Wait for completion with timeout
            tts_thread.join(timeout=10)  # Max 10 seconds
            
            if tts_thread.is_alive():
                logger.warning("TTS thread timed out")
                return
                
            logger.info("Local TTS completed successfully")
            
        except Exception as e:
            logger.error(f"Local TTS error: {e}")
            # Don't try to reinitialize, just fail gracefully
            raise Exception(f"Local TTS failed: {str(e)}")
    
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

    def stop_speaking(self):
        """Stop current speech output immediately"""
        try:
            self.speech_stopped = True
            if self.tts_engine:
                self.tts_engine.stop()
                logger.info("Speech stopped successfully")
                return True
        except Exception as e:
            logger.error(f"Error stopping speech: {e}")
        return False
    
    def restart_voice_engine(self):
        """Restart the voice engine completely"""
        try:
            # Stop any current speech
            self.stop_speaking()
            
            # Reinitialize the TTS engine
            if PYTTSX3_AVAILABLE:
                try:
                    # Clean up old engine
                    if self.tts_engine:
                        try:
                            self.tts_engine.stop()
                        except:
                            pass
                    
                    # Create new engine
                    self.tts_engine = pyttsx3.init()
                    
                    # Reconfigure settings
                    self.tts_engine.setProperty('rate', 150)
                    self.tts_engine.setProperty('volume', 0.8)
                    
                    # Set voice preference
                    voices = self.tts_engine.getProperty('voices')
                    if voices:
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                self.tts_engine.setProperty('voice', voice.id)
                                break
                    
                    self.speech_stopped = False
                    logger.info("Voice engine restarted successfully")
                    return True
                    
                except Exception as e:
                    logger.error(f"Error restarting TTS engine: {e}")
                    return False
            else:
                logger.warning("pyttsx3 not available for restart")
                return False
                
        except Exception as e:
            logger.error(f"Error during voice engine restart: {e}")
            return False
    
    def get_speech_status(self):
        """Get current speech status"""
        return {
            "is_speaking": self.is_speaking,
            "speech_stopped": self.speech_stopped,
            "engine_available": self.tts_engine is not None,
            "voice_input_available": self.is_voice_input_available(),
            "voice_output_available": self.is_voice_output_available()
        }
    
    def clear_speech_flag(self):
        """Clear the speech stopped flag to allow new speech"""
        self.speech_stopped = False
        logger.info("Speech flag cleared - ready for new speech")

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
