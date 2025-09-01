"""
Audio Visualizer for Voice Tutor
Provides real-time audio level visualization for microphone input and AI speech output
"""

import numpy as np
import threading
import time
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

# Try to import pyaudio for real-time audio monitoring
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    logger.warning("PyAudio not available for real-time audio monitoring")

class AudioVisualizer:
    """Real-time audio level visualization"""
    
    def __init__(self):
        self.is_monitoring = False
        self.current_input_level = 0.0
        self.current_output_level = 0.0
        self.audio_stream = None
        self.audio_instance = None
        self.monitoring_thread = None
        
        # Audio settings
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.channels = 1
        
        self._initialize_audio()
    
    def _initialize_audio(self):
        """Initialize PyAudio for real-time monitoring"""
        if not PYAUDIO_AVAILABLE:
            logger.warning("PyAudio not available, audio visualization disabled")
            return
        
        try:
            self.audio_instance = pyaudio.PyAudio()
            logger.info("Audio visualizer initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize audio: {e}")
            self.audio_instance = None
    
    def start_input_monitoring(self) -> bool:
        """Start monitoring microphone input levels"""
        if not self.audio_instance:
            logger.warning("Audio system not available")
            return False
        
        try:
            # Open microphone stream
            self.audio_stream = self.audio_instance.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.is_monitoring = True
            self.audio_stream.start_stream()
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitor_audio_levels, 
                daemon=True
            )
            self.monitoring_thread.start()
            
            logger.info("Microphone monitoring started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start audio monitoring: {e}")
            return False
    
    def stop_input_monitoring(self):
        """Stop monitoring microphone input"""
        self.is_monitoring = False
        
        if self.audio_stream:
            try:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
        
        self.current_input_level = 0.0
        logger.info("Microphone monitoring stopped")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback for real-time level detection"""
        try:
            # Convert audio data to numpy array
            audio_data = np.frombuffer(in_data, dtype=np.float32)
            
            # Calculate RMS (Root Mean Square) for audio level
            rms = np.sqrt(np.mean(audio_data**2))
            
            # Convert to decibel-like scale (0-100)
            if rms > 0:
                level = min(100, max(0, 20 * np.log10(rms) + 60))
            else:
                level = 0
            
            self.current_input_level = level
            
        except Exception as e:
            logger.error(f"Audio callback error: {e}")
        
        return (in_data, pyaudio.paContinue)
    
    def _monitor_audio_levels(self):
        """Background thread for monitoring audio levels"""
        while self.is_monitoring:
            try:
                # Gradually decay the input level if no new audio
                self.current_input_level = max(0, self.current_input_level - 2)
                time.sleep(0.05)  # 20 FPS update rate
            except Exception as e:
                logger.error(f"Audio monitoring error: {e}")
                break
    
    def get_input_level(self) -> float:
        """Get current microphone input level (0-100)"""
        return self.current_input_level
    
    def get_output_level(self) -> float:
        """Get current AI speech output level (0-100)"""
        return self.current_output_level
    
    def set_output_level(self, level: float):
        """Set AI speech output level (for visualization during TTS)"""
        self.current_output_level = max(0, min(100, level))
    
    def simulate_output_speech(self, duration: float = 3.0):
        """Simulate AI speech output for visualization"""
        def animate_output():
            start_time = time.time()
            while time.time() - start_time < duration:
                # Simulate speech pattern with random variations
                base_level = 60 + 30 * np.sin(time.time() * 10)  # Oscillating pattern
                noise = np.random.normal(0, 10)  # Add some randomness
                level = max(20, min(90, base_level + noise))
                
                self.current_output_level = level
                time.sleep(0.1)
            
            # Fade out
            for i in range(10):
                self.current_output_level = max(0, self.current_output_level - 10)
                time.sleep(0.1)
        
        # Run animation in background thread
        animation_thread = threading.Thread(target=animate_output, daemon=True)
        animation_thread.start()
    
    def cleanup(self):
        """Clean up audio resources"""
        self.stop_input_monitoring()
        
        if self.audio_instance:
            try:
                self.audio_instance.terminate()
            except Exception as e:
                logger.error(f"Error terminating audio: {e}")
    
    def is_available(self) -> bool:
        """Check if audio visualization is available"""
        return PYAUDIO_AVAILABLE and self.audio_instance is not None
    
    def get_microphone_devices(self) -> list:
        """Get list of available microphone devices"""
        if not self.audio_instance:
            return []
        
        devices = []
        try:
            for i in range(self.audio_instance.get_device_count()):
                device_info = self.audio_instance.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Input device
                    devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels']
                    })
        except Exception as e:
            logger.error(f"Error getting audio devices: {e}")
        
        return devices

# Streamlit integration functions
def create_audio_level_bars_html(input_level: float, output_level: float) -> str:
    """Create HTML for audio level visualization bars"""
    
    # Normalize levels to 0-100
    input_percent = max(0, min(100, input_level))
    output_percent = max(0, min(100, output_level))
    
    # Color coding for levels
    def get_bar_color(level):
        if level < 20:
            return "#4CAF50"  # Green - quiet
        elif level < 60:
            return "#FF9800"  # Orange - moderate
        else:
            return "#F44336"  # Red - loud
    
    input_color = get_bar_color(input_percent)
    output_color = get_bar_color(output_percent)
    
    html = f"""
    <div style="background: rgba(0,0,0,0.1); padding: 20px; border-radius: 10px; margin: 10px 0;">
        <div style="display: flex; gap: 20px; align-items: center;">
            
            <!-- Microphone Input Bar -->
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <span style="font-weight: bold; color: #333; margin-right: 10px;">🎤 Mic Input:</span>
                    <span style="color: #666; font-size: 0.9em;">{input_percent:.0f}%</span>
                </div>
                <div style="width: 100%; height: 25px; background: #e0e0e0; border-radius: 12px; overflow: hidden; position: relative;">
                    <div style="height: 100%; background: linear-gradient(90deg, {input_color}, {input_color}); 
                                width: {input_percent}%; transition: width 0.1s ease-in-out; border-radius: 12px;"></div>
                    <!-- Level markers -->
                    <div style="position: absolute; top: 0; left: 20%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                    <div style="position: absolute; top: 0; left: 60%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                    <div style="position: absolute; top: 0; left: 80%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                </div>
                <div style="font-size: 0.8em; color: #666; margin-top: 2px;">
                    Quiet ←→ Loud
                </div>
            </div>
            
            <!-- AI Speech Output Bar -->
            <div style="flex: 1;">
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <span style="font-weight: bold; color: #333; margin-right: 10px;">🔊 AI Voice:</span>
                    <span style="color: #666; font-size: 0.9em;">{output_percent:.0f}%</span>
                </div>
                <div style="width: 100%; height: 25px; background: #e0e0e0; border-radius: 12px; overflow: hidden; position: relative;">
                    <div style="height: 100%; background: linear-gradient(90deg, {output_color}, {output_color}); 
                                width: {output_percent}%; transition: width 0.1s ease-in-out; border-radius: 12px;"></div>
                    <!-- Level markers -->
                    <div style="position: absolute; top: 0; left: 20%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                    <div style="position: absolute; top: 0; left: 60%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                    <div style="position: absolute; top: 0; left: 80%; width: 1px; height: 100%; background: rgba(0,0,0,0.2);"></div>
                </div>
                <div style="font-size: 0.8em; color: #666; margin-top: 2px;">
                    Silent ←→ Speaking
                </div>
            </div>
            
        </div>
        
        <!-- Status indicators -->
        <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
            <div style="display: flex; gap: 30px; justify-content: center;">
                <span>🎤 {'🟢 Active' if input_percent > 5 else '⚪ Quiet'}</span>
                <span>🔊 {'🟢 Speaking' if output_percent > 5 else '⚪ Silent'}</span>
            </div>
        </div>
    </div>
    """
    
    return html

def create_microphone_test_html() -> str:
    """Create HTML for microphone testing interface"""
    return """
    <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); 
                padding: 15px; border-radius: 10px; text-align: center; color: white; margin: 10px 0;">
        <h4 style="margin: 0 0 10px 0;">🎤 Microphone Test</h4>
        <p style="margin: 5px 0; font-size: 0.9em;">
            Speak into your microphone and watch the level bar above.<br>
            The bar should move when you speak. If it doesn't move, check your microphone permissions.
        </p>
        <div style="margin-top: 10px; font-size: 0.8em; opacity: 0.9;">
            💡 Tip: Your browser may ask for microphone permission - please allow it!
        </div>
    </div>
    """
