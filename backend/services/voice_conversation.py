"""
Interactive Voice Conversation Manager
Provides continuous conversation capabilities similar to ChatGPT and Gemini
"""

import time
import threading
from typing import List, Dict, Any, Optional, Callable
import logging
import json
from datetime import datetime, timedelta
from backend.services.voice_tutor import VoiceTutor
from backend.services.ai_engine import AIEngine

logger = logging.getLogger(__name__)

class VoiceConversation:
    """Manages interactive voice conversations with the AI"""
    
    def __init__(self):
        self.voice_tutor = VoiceTutor()
        self.ai_engine = AIEngine()
        self.conversation_history: List[Dict[str, Any]] = []
        self.is_active = False
        self.listening_active = False
        self.conversation_context = ""
        self.user_preferences = {
            "voice_speed": 150,
            "voice_volume": 0.8,
            "auto_response": True,
            "conversation_timeout": 30  # seconds
        }
        self.last_interaction_time = None
        self.conversation_thread = None
        
    def start_conversation(self, initial_context: str = "") -> Dict[str, Any]:
        """Start a new interactive voice conversation"""
        try:
            self.conversation_context = initial_context
            self.conversation_history = []
            self.is_active = True
            self.last_interaction_time = datetime.now()
            
            # Add initial greeting to history
            greeting = self._get_conversation_greeting(initial_context)
            
            self._add_to_history("assistant", greeting)
            
            # Speak the greeting
            if self.voice_tutor.is_voice_output_available():
                self.voice_tutor.speak_text(greeting)
            
            logger.info("Voice conversation started")
            return {
                "status": "started",
                "message": greeting,
                "conversation_id": self._generate_conversation_id()
            }
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            return {
                "status": "error",
                "message": f"Failed to start conversation: {str(e)}"
            }
    
    def listen_and_respond(self, timeout: int = 10) -> Dict[str, Any]:
        """Listen for user input and provide AI response"""
        try:
            if not self.is_active:
                return {"status": "error", "message": "Conversation not active"}
            
            # Listen for user input
            logger.info("Listening for user input...")
            user_input = self.voice_tutor.listen_for_question(timeout=timeout)
            
            if not user_input:
                return {
                    "status": "no_input", 
                    "message": "No speech detected. Try speaking clearly into your microphone."
                }
            
            # Add user input to history
            self._add_to_history("user", user_input)
            
            # Check for conversation commands
            command_response = self._handle_conversation_commands(user_input)
            if command_response:
                return command_response
            
            # Generate AI response based on conversation history
            ai_response = self._generate_contextual_response(user_input)
            
            # Add AI response to history
            self._add_to_history("assistant", ai_response)
            
            # Speak the response
            if self.voice_tutor.is_voice_output_available():
                self.voice_tutor.speak_text(ai_response)
            
            self.last_interaction_time = datetime.now()
            
            return {
                "status": "success",
                "user_input": user_input,
                "ai_response": ai_response,
                "conversation_length": len(self.conversation_history)
            }
            
        except Exception as e:
            logger.error(f"Error in listen_and_respond: {e}")
            return {
                "status": "error", 
                "message": f"Error processing conversation: {str(e)}"
            }
    
    def continue_conversation(self, user_text: str = None) -> Dict[str, Any]:
        """Continue conversation with optional text input"""
        try:
            if not self.is_active:
                return {"status": "error", "message": "Conversation not active"}
            
            # Use provided text or listen for voice input
            if user_text:
                user_input = user_text
            else:
                user_input = self.voice_tutor.listen_for_question(timeout=15)
                
            if not user_input:
                return {
                    "status": "no_input",
                    "message": "Please speak or type your question."
                }
            
            # Process the input
            self._add_to_history("user", user_input)
            
            # Check for commands
            command_response = self._handle_conversation_commands(user_input)
            if command_response:
                return command_response
            
            # Generate response
            ai_response = self._generate_contextual_response(user_input)
            self._add_to_history("assistant", ai_response)
            
            # Speak response if voice is available
            if self.voice_tutor.is_voice_output_available():
                self.voice_tutor.speak_text(ai_response)
            
            self.last_interaction_time = datetime.now()
            
            return {
                "status": "success",
                "user_input": user_input,
                "ai_response": ai_response,
                "conversation_turn": len(self.conversation_history) // 2
            }
            
        except Exception as e:
            logger.error(f"Error continuing conversation: {e}")
            return {"status": "error", "message": str(e)}
    
    def end_conversation(self) -> Dict[str, Any]:
        """End the current conversation"""
        try:
            if self.is_active:
                farewell = self._get_conversation_farewell()
                self._add_to_history("assistant", farewell)
                
                if self.voice_tutor.is_voice_output_available():
                    self.voice_tutor.speak_text(farewell)
                
                self.is_active = False
                self.listening_active = False
                
                summary = self._generate_conversation_summary()
                
                logger.info("Voice conversation ended")
                return {
                    "status": "ended",
                    "message": farewell,
                    "summary": summary,
                    "total_turns": len(self.conversation_history) // 2
                }
            else:
                return {"status": "not_active", "message": "No active conversation to end"}
                
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return {"status": "error", "message": str(e)}
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the current conversation history"""
        return self.conversation_history.copy()
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """Get current conversation status"""
        return {
            "is_active": self.is_active,
            "listening_active": self.listening_active,
            "history_length": len(self.conversation_history),
            "voice_input_available": self.voice_tutor.is_voice_input_available(),
            "voice_output_available": self.voice_tutor.is_voice_output_available(),
            "last_interaction": self.last_interaction_time.isoformat() if self.last_interaction_time else None,
            "context": self.conversation_context
        }
    
    def _add_to_history(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
    
    def _generate_contextual_response(self, user_input: str) -> str:
        """Generate AI response based on conversation context"""
        try:
            # Prepare conversation context for AI
            recent_context = ""
            if len(self.conversation_history) > 1:
                # Include last few exchanges for context
                recent_messages = self.conversation_history[-6:]  # Last 3 exchanges
                for msg in recent_messages:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    recent_context += f"{role}: {msg['content']}\n"
            
            # Add current context if available
            if self.conversation_context:
                context_prompt = f"""
Context: {self.conversation_context}

Previous conversation:
{recent_context}

Current user question: {user_input}

Please provide a helpful, conversational response that:
1. Addresses the user's question directly
2. Considers the previous conversation context
3. Is educational and encouraging
4. Keeps the conversation flowing naturally
5. Is concise but informative (2-3 sentences max for voice)
"""
            else:
                context_prompt = f"""
Previous conversation:
{recent_context}

Current user question: {user_input}

Please provide a helpful, conversational response that addresses their question and keeps the conversation flowing naturally. Keep it concise for voice interaction (2-3 sentences max).
"""
            
            # Use AI engine to generate response
            response = self.ai_engine.answer_question(context_prompt, user_input)
            
            # Clean up response for voice
            cleaned_response = self._clean_response_for_voice(response)
            
            return cleaned_response
            
        except Exception as e:
            logger.error(f"Error generating contextual response: {e}")
            return "I'm having trouble processing that. Could you please rephrase your question?"
    
    def _clean_response_for_voice(self, response: str) -> str:
        """Clean AI response for better voice output"""
        try:
            # Remove markdown formatting
            response = response.replace("**", "").replace("*", "")
            response = response.replace("```", "").replace("`", "")
            
            # Remove excessive line breaks
            response = " ".join(response.split())
            
            # Limit length for voice (about 200 characters for natural speech)
            if len(response) > 250:
                sentences = response.split(". ")
                if len(sentences) > 1:
                    # Take first 2 sentences
                    response = ". ".join(sentences[:2]) + "."
                else:
                    # Truncate at word boundary
                    words = response.split()
                    response = " ".join(words[:40]) + "..."
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error cleaning response: {e}")
            return response
    
    def _handle_conversation_commands(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Handle special conversation commands"""
        user_input_lower = user_input.lower().strip()
        
        # End conversation commands
        if any(cmd in user_input_lower for cmd in ["goodbye", "bye", "end conversation", "stop", "exit", "quit"]):
            return self.end_conversation()
        
        # Repeat last response
        if any(cmd in user_input_lower for cmd in ["repeat", "say again", "pardon", "what did you say"]):
            if self.conversation_history and self.conversation_history[-1]["role"] == "assistant":
                last_response = self.conversation_history[-1]["content"]
                if self.voice_tutor.is_voice_output_available():
                    self.voice_tutor.speak_text(last_response)
                return {
                    "status": "repeated",
                    "message": last_response
                }
        
        # Help command
        if any(cmd in user_input_lower for cmd in ["help", "what can you do", "commands"]):
            help_text = "I can help you with educational topics, answer questions, explain concepts, and have conversations about your studies. Just speak naturally, and I'll respond. Say 'goodbye' to end our conversation."
            if self.voice_tutor.is_voice_output_available():
                self.voice_tutor.speak_text(help_text)
            return {
                "status": "help",
                "message": help_text
            }
        
        return None
    
    def _get_conversation_greeting(self, context: str = "") -> str:
        """Get appropriate greeting based on context"""
        if context:
            return f"Hi there! I'm your AI voice tutor. I see we have some material about {context[:50]}... How can I help you learn today? Feel free to ask me anything!"
        else:
            return "Hello! I'm your AI voice tutor. I'm here to help you learn and answer any questions you might have. What would you like to explore today?"
    
    def _get_conversation_farewell(self) -> str:
        """Get appropriate farewell message"""
        turn_count = len(self.conversation_history) // 2
        if turn_count > 5:
            return "Great conversation! We covered a lot of ground today. Keep up the excellent learning, and feel free to chat with me anytime. Goodbye!"
        elif turn_count > 2:
            return "Thanks for our chat! I hope I was helpful. Keep learning and don't hesitate to come back with more questions. See you later!"
        else:
            return "Thanks for chatting with me! I'm always here when you need help with your studies. Have a great day!"
    
    def _generate_conversation_summary(self) -> str:
        """Generate a summary of the conversation"""
        try:
            if len(self.conversation_history) < 2:
                return "Short conversation without substantial content."
            
            topics = []
            user_messages = [msg["content"] for msg in self.conversation_history if msg["role"] == "user"]
            
            # Extract key topics (simple keyword extraction)
            for message in user_messages:
                words = message.lower().split()
                topics.extend([word for word in words if len(word) > 4])
            
            unique_topics = list(set(topics))[:5]  # Top 5 unique topics
            
            return f"Conversation covered {len(user_messages)} questions about topics including: {', '.join(unique_topics)}"
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Unable to generate conversation summary."
    
    def _generate_conversation_id(self) -> str:
        """Generate unique conversation ID"""
        return f"voice_conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

# Helper functions for Streamlit integration
def format_conversation_for_display(conversation_history: List[Dict[str, Any]]) -> str:
    """Format conversation history for display"""
    formatted = ""
    for msg in conversation_history:
        role = "🧑 You" if msg["role"] == "user" else "🤖 AI Tutor"
        timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
        formatted += f"**{role}** ({timestamp})\n{msg['content']}\n\n"
    return formatted

def get_voice_conversation_css() -> str:
    """Get CSS for voice conversation interface"""
    return """
    <style>
    .voice-chat-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        color: white;
    }
    .voice-status {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .conversation-message {
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-left: 4px solid #FFD700;
    }
    .voice-controls {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 15px 0;
    }
    .voice-button {
        background: #FFD700;
        color: #333;
        border: none;
        border-radius: 25px;
        padding: 12px 25px;
        font-weight: bold;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .voice-button:hover {
        background: #FFC700;
        transform: translateY(-2px);
    }
    </style>
    """
