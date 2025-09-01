import streamlit as st
import os
import tempfile
import time
import random
from datetime import datetime
import json
from pathlib import Path

# Try to import our modules, handle gracefully if dependencies are missing
try:
    from backend.services.pdf_processor import PDFProcessor
    PDF_AVAILABLE = True
except ImportError as e:
    PDF_AVAILABLE = False
    st.error(f"PDF processing not available: {str(e)}")

try:
    from backend.services.ai_engine import AIEngine
    AI_AVAILABLE = True
except ImportError as e:
    AI_AVAILABLE = False
    st.warning(f"AI engine not fully available: {str(e)}")

try:
    from backend.utils.database import DatabaseManager
    DB_AVAILABLE = True
except ImportError as e:
    DB_AVAILABLE = False
    st.warning(f"Database not available: {str(e)}")

try:
    from backend.services.voice_conversation import VoiceConversation, format_conversation_for_display, get_voice_conversation_css
    from backend.services.voice_tutor import VoiceTutor
    from backend.services.audio_visualizer import AudioVisualizer, create_audio_level_bars_html, create_microphone_test_html
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    st.warning(f"Voice features not available: {str(e)}")

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .upload-section {
        border: 2px dashed #2E86AB;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .user-message {
        background-color: #E3F2FD;
        margin-left: 2rem;
    }
    .ai-message {
        background-color: #F3E5F5;
        margin-right: 2rem;
    }
    .summary-box {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2E86AB;
    }
    .demo-content {
        background-color: #E8F5E8;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #4CAF50;
    }
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
        text-align: center;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

class SimplifiedStudyAssistant:
    def __init__(self):
        # Initialize components that are available
        self.pdf_processor = PDFProcessor() if PDF_AVAILABLE else None
        self.ai_engine = AIEngine() if AI_AVAILABLE else None
        self.db_manager = DatabaseManager() if DB_AVAILABLE else None
        self.voice_conversation = VoiceConversation() if VOICE_AVAILABLE else None
        self.audio_visualizer = AudioVisualizer() if VOICE_AVAILABLE else None
        
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_document' not in st.session_state:
            st.session_state.current_document = None
        if 'processed_content' not in st.session_state:
            st.session_state.processed_content = None
        if 'voice_conversation_active' not in st.session_state:
            st.session_state.voice_conversation_active = False
        if 'voice_conversation_history' not in st.session_state:
            st.session_state.voice_conversation_history = []
        if 'voice_last_response' not in st.session_state:
            st.session_state.voice_last_response = ""
        if 'audio_monitoring' not in st.session_state:
            st.session_state.audio_monitoring = False
        if 'mic_level' not in st.session_state:
            st.session_state.mic_level = 0.0
        if 'ai_speech_level' not in st.session_state:
            st.session_state.ai_speech_level = 0.0

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">📚 AI Study Assistant 🤖</h1>', unsafe_allow_html=True)
        
        # Status indicators
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            status = "✅ Ready" if PDF_AVAILABLE else "⚠️ Setup Needed"
            st.metric("PDF Processing", status)
        with col2:
            status = "✅ Ready" if AI_AVAILABLE else "⚠️ Optional"
            st.metric("AI Engine", status)
        with col3:
            status = "✅ Ready" if DB_AVAILABLE else "⚠️ Optional"
            st.metric("Database", status)
        with col4:
            status = "✅ Ready" if VOICE_AVAILABLE else "⚠️ Setup Needed"
            st.metric("Voice Tutor", status)
        with col5:
            st.metric("Demo Mode", "✅ Available")

    def render_sidebar(self):
        """Render the sidebar with controls"""
        with st.sidebar:
            st.header("🎯 Study Controls")
            
            # Grade selection
            grade = st.selectbox(
                "Select Grade Level",
                ["Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12"],
                index=3
            )
            
            # Subject selection
            subject = st.selectbox(
                "Subject",
                ["Science", "Mathematics", "Social Science", "English", "Hindi"],
                index=0
            )
            
            # Feature availability
            st.subheader("🔧 System Status")
            
            if PDF_AVAILABLE:
                st.success("✅ PDF Processing Ready")
            else:
                st.error("❌ PDF Processing Unavailable")
                if st.button("📦 Install PDF Dependencies"):
                    st.code("pip install PyPDF2 pdfplumber pymupdf")
            
            if AI_AVAILABLE:
                st.success("✅ AI Engine Ready")
            else:
                st.warning("⚠️ AI Engine Limited")
                if st.button("🤖 Install AI Dependencies"):
                    st.code("pip install openai transformers torch")
            
            if VOICE_AVAILABLE:
                st.success("✅ Voice Tutor Ready")
            else:
                st.warning("⚠️ Voice Features Unavailable")
                if st.button("🎤 Install Voice Dependencies"):
                    st.code("pip install speechrecognition pyttsx3 gtts pyaudio")
            
            st.markdown("---")
            
            # Quick actions
            st.subheader("🚀 Quick Actions")
            if st.button("🎯 Load Demo Content"):
                self.load_demo_content()
            
            if st.button("📖 Show Instructions"):
                self.show_instructions()
            
            return {
                'grade': grade,
                'subject': subject
            }

    def render_upload_section(self):
        """Render the file upload section"""
        st.header("📎 Upload Your Study Material")
        
        if not PDF_AVAILABLE:
            st.error("❌ PDF processing is not available. Please install required dependencies.")
            st.code("pip install PyPDF2 pdfplumber pymupdf")
            return
        
        with st.container():
            st.markdown('<div class="upload-section">', unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Choose a PDF file (NCERT textbooks, notes, etc.)",
                type=['pdf'],
                help="Upload NCERT textbooks or any educational PDF for AI-powered summarization and Q&A"
            )
            
            if uploaded_file is not None:
                # Display file info
                col1, col2 = st.columns(2)
                with col1:
                    st.success(f"✅ File: {uploaded_file.name}")
                    st.info(f"📊 Size: {uploaded_file.size / 1024 / 1024:.1f} MB")
                
                with col2:
                    if st.button("🚀 Process Document", type="primary"):
                        self.process_uploaded_file(uploaded_file)
            
            st.markdown('</div>', unsafe_allow_html=True)

    def process_uploaded_file(self, uploaded_file):
        """Process the uploaded PDF file"""
        if not self.pdf_processor:
            st.error("❌ PDF processor not available")
            return
            
        try:
            with st.spinner("🔄 Processing your document..."):
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Extract text from PDF
                progress_bar = st.progress(0)
                st.text("📖 Extracting text from PDF...")
                progress_bar.progress(25)
                
                extracted_text = self.pdf_processor.extract_text(tmp_file_path)
                progress_bar.progress(50)
                
                # Generate summary (with or without AI)
                st.text("🤖 Generating summary...")
                if self.ai_engine:
                    summary = self.ai_engine.generate_summary(extracted_text)
                else:
                    summary = self.generate_simple_summary(extracted_text)
                progress_bar.progress(75)
                
                # Update session state
                st.session_state.current_document = uploaded_file.name
                st.session_state.processed_content = {
                    'text': extracted_text,
                    'summary': summary,
                    'file_name': uploaded_file.name
                }
                
                progress_bar.progress(100)
                
                # Clean up
                os.unlink(tmp_file_path)
                
                st.success("✅ Document processed successfully!")
                st.balloons()
                
                # Immediately display the results
                self.display_processing_results()
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")
    
    def display_processing_results(self):
        """Display the processing results immediately"""
        if not st.session_state.processed_content:
            return
            
        st.markdown("---")
        st.header("📋 Document Analysis Results")
        
        summary = st.session_state.processed_content['summary']
        file_name = st.session_state.processed_content['file_name']
        
        # Display file info
        st.info(f"📄 **File:** {file_name}")
        
        # Display summary
        st.subheader("📝 Summary")
        if isinstance(summary, dict) and 'overview' in summary:
            st.write(summary['overview'])
            
            # Display key points
            if 'key_points' in summary and summary['key_points']:
                st.subheader("🔑 Key Points")
                for i, point in enumerate(summary['key_points'][:5], 1):
                    st.write(f"{i}. {point}")
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Word Count", summary.get('word_count', 0))
            with col2:
                st.metric("📄 Summary Length", summary.get('summary_length', 0))
            with col3:
                st.metric("🤖 Generated By", summary.get('generated_by', 'AI'))
        else:
            st.write(summary)
        
        # Add Q&A section
        st.markdown("---")
        st.subheader("❓ Ask Questions About This Document")
        
        question = st.text_input("💭 Enter your question:", key="post_process_question")
        if st.button("🔍 Get Answer", key="post_process_ask"):
            if question:
                with st.spinner("🤔 Thinking..."):
                    context = st.session_state.processed_content['text']
                    if self.ai_engine:
                        response = self.ai_engine.answer_question(question, context)
                    else:
                        response = self.simple_answer(question, context)
                    
                    st.write("**Answer:**")
                    st.write(response)
            else:
                st.warning("Please enter a question first.")
                
        st.markdown("---")

    def generate_simple_summary(self, text: str) -> dict:
        """Generate a simple summary without AI"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Take key sentences
        summary_sentences = []
        if len(sentences) > 5:
            summary_sentences.extend(sentences[:2])  # First 2
            summary_sentences.extend(sentences[len(sentences)//2:len(sentences)//2+2])  # Middle 2
            summary_sentences.extend(sentences[-2:])  # Last 2
        else:
            summary_sentences = sentences
        
        # Extract key points (sentences with educational keywords)
        educational_keywords = [
            'definition', 'important', 'concept', 'principle', 'formula', 
            'example', 'theory', 'law', 'process', 'characteristic'
        ]
        
        key_points = []
        for sentence in sentences:
            for keyword in educational_keywords:
                if keyword.lower() in sentence.lower() and len(sentence.split()) > 5:
                    key_points.append(sentence.strip())
                    break
        
        return {
            'overview': '. '.join(summary_sentences),
            'key_points': key_points[:8],
            'word_count': len(text.split()),
            'generated_by': 'Simple Extraction'
        }

    def render_summary_section(self):
        """Render the document summary section"""
        if st.session_state.processed_content:
            st.header("📋 Document Summary")
            
            summary = st.session_state.processed_content['summary']
            
            with st.container():
                st.markdown('<div class="summary-box">', unsafe_allow_html=True)
                
                # Summary tabs
                tab1, tab2, tab3 = st.tabs(["📖 Summary", "🎯 Key Points", "📊 Analysis"])
                
                with tab1:
                    st.markdown("### Chapter Overview")
                    st.write(summary.get('overview', 'Summary not available'))
                
                with tab2:
                    st.markdown("### Important Points")
                    key_points = summary.get('key_points', [])
                    for i, point in enumerate(key_points, 1):
                        st.markdown(f"**{i}.** {point}")
                
                with tab3:
                    st.markdown("### Content Analysis")
                    col1, col2 = st.columns(2)
                    with col1:
                        word_count = summary.get('word_count', 0)
                        st.metric("Word Count", f"{word_count:,}")
                        st.metric("Reading Time", f"{word_count // 200} min")
                    with col2:
                        st.metric("Key Concepts", len(key_points))
                        st.metric("Generated By", summary.get('generated_by', 'Unknown'))
                
                st.markdown('</div>', unsafe_allow_html=True)

    def render_chat_section(self):
        """Render the Q&A chat section"""
        if st.session_state.processed_content:
            st.header("💬 Ask Questions About Your Document")
            
            # Chat history
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'<div class="chat-message user-message">👤 <strong>You:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message ai-message">🤖 <strong>AI:</strong> {message["content"]}</div>', 
                              unsafe_allow_html=True)
            
            # Chat input
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_question = st.text_input(
                    "Ask a question about the document:",
                    placeholder="e.g., What is diffusion? Explain the water cycle...",
                    key="chat_input"
                )
            
            with col2:
                if st.button("Send 📤", type="primary"):
                    if user_question:
                        self.handle_user_question(user_question)

    def handle_user_question(self, question):
        """Handle user question and generate response"""
        try:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            
            # Generate response
            if self.ai_engine:
                context = st.session_state.processed_content['text']
                response = self.ai_engine.answer_question(question, context)
            else:
                response = self.simple_answer(question, st.session_state.processed_content['text'])
            
            # Add AI response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Rerun to update chat
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")

    def simple_answer(self, question: str, context: str) -> str:
        """Simple keyword-based answering"""
        question_words = question.lower().split()
        sentences = context.split('.')
        
        # Find sentences containing question keywords
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            matches = sum(1 for word in question_words if word in sentence_lower and len(word) > 2)
            if matches >= 2:
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            return f"Based on the document: {'. '.join(relevant_sentences[:2])}"
        else:
            return "I couldn't find specific information about your question in the document. Please try asking about topics that are directly covered in the text."

    def load_demo_content(self):
        """Load demo content for testing"""
        demo_content = {
            'text': """
            Matter in Our Surroundings - NCERT Class 9 Science Chapter 1
            
            Everything around us is made up of matter. Matter is anything that has mass and occupies space. 
            The air we breathe, the food we eat, stones, clouds, stars, plants and animals, even a small drop of water or a particle of sand - everything is matter.
            
            Physical Nature of Matter:
            Matter is made up of particles. These particles are very small - so small that we cannot see them with naked eyes.
            
            Characteristics of Particles of Matter:
            1. Particles of matter have space between them
            2. Particles of matter are continuously moving
            3. Particles of matter attract each other
            
            States of Matter:
            Based on physical properties, matter is classified into three states:
            1. Solid State: Particles are closely packed, have definite shape and volume
            2. Liquid State: Particles are less closely packed, have definite volume but no definite shape
            3. Gaseous State: Particles are far apart, no definite shape or volume
            
            Diffusion:
            The mixing of particles of two different types of matter on their own is called diffusion.
            For example, when we light an incense stick in one corner of our room, we can smell it sitting in the other corner. This is due to diffusion.
            
            Examples of Diffusion:
            - Spreading of perfume in air
            - Mixing of two gases
            - Sugar dissolving in water
            
            Temperature and Particle Motion:
            As temperature increases, particles move faster. This affects the rate of diffusion and state changes.
            """,
            'summary': {
                'overview': 'This chapter introduces the fundamental concept that everything around us is made of matter, which consists of tiny particles in constant motion. Matter exists in three states - solid, liquid, and gas - based on how closely packed the particles are.',
                'key_points': [
                    'Matter is anything that has mass and occupies space',
                    'All matter is made up of very small particles',
                    'Particles have spaces between them and are in continuous motion',
                    'Particles of matter attract each other',
                    'Matter exists in three states: solid, liquid, and gas',
                    'Diffusion is the mixing of particles of different substances',
                    'Temperature affects particle motion and diffusion rate'
                ],
                'word_count': 230,
                'generated_by': 'Demo Content'
            }
        }
        
        st.session_state.processed_content = demo_content
        st.session_state.current_document = "Demo: NCERT Class 9 Science - Matter in Our Surroundings"
        st.success("✅ Demo content loaded! You can now try the Q&A feature below.")
        st.rerun()

    def show_instructions(self):
        """Show setup and usage instructions"""
        st.markdown("""
        ## 📖 AI Study Assistant - Setup Guide
        
        ### 🔧 Installation Steps:
        
        1. **Install PDF Dependencies** (Required):
           ```bash
           pip install PyPDF2 pdfplumber pymupdf Pillow
           ```
        
        2. **Install AI Dependencies** (Optional but Recommended):
           ```bash
           pip install openai transformers torch sentence-transformers
           ```
        
        3. **Setup API Keys** (Optional):
           - Create `.env` file from `.env.example`
           - Add your OpenAI API key for better AI responses
        
        ### 🎯 How to Use:
        
        1. **Upload PDF**: Click "Choose a PDF file" and select your NCERT textbook
        2. **Review Summary**: Get instant chapter overview and key points
        3. **Ask Questions**: Use the chat interface to ask about the content
        4. **Get Answers**: Receive student-friendly explanations
        
        ### 🎮 Try Demo Mode:
        - Click "Load Demo Content" to see how it works
        - Sample NCERT Class 9 Science content included
        - Perfect for testing before uploading your own PDFs
        """)

    def render_demo_section(self):
        """Render demo section with sample content"""
        if not st.session_state.processed_content:
            st.header("🎯 Demo Mode")
            
            st.markdown('<div class="demo-content">', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📖 Try Our Demo
                **NCERT Class 9 Science - Matter in Our Surroundings**
                
                Experience the AI Study Assistant with sample educational content:
                - ✅ Instant PDF processing simulation
                - ✅ Smart summarization
                - ✅ Interactive Q&A
                - ✅ Student-friendly explanations
                """)
                
                if st.button("🚀 Load Demo Content", type="primary", key="demo_main"):
                    self.load_demo_content()
            
            with col2:
                st.markdown("""
                ### 🎓 Perfect For:
                - **NCERT Textbooks** - All subjects and grades
                - **Study Notes** - Your own or teacher's notes
                - **Reference Materials** - Additional resources
                - **Question Papers** - Previous year papers
                
                ### 🔥 Features:
                - **Fast Processing** - Get summaries in seconds
                - **Smart Q&A** - Ask anything about the content
                - **Grade-appropriate** - Suitable explanations
                - **Works Offline** - No internet needed for basic features
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)

    def render_voice_conversation_section(self):
        """Render the interactive voice conversation section"""
        st.header("🗣️ Interactive Voice Tutor")
        
        if not VOICE_AVAILABLE:
            st.error("❌ Voice features are not available. Please install required dependencies.")
            st.code("pip install speechrecognition pyttsx3 gtts pyaudio")
            return
        
        # Voice conversation container
        st.markdown('<div class="voice-chat-container">', unsafe_allow_html=True)
        
        st.markdown("### 🎤 Talk with Your AI Tutor")
        st.markdown("Have a natural conversation with your AI tutor! Just like ChatGPT or Gemini, but with voice!")
        
        # Voice status
        if self.voice_conversation:
            status = self.voice_conversation.get_conversation_status()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                status_text = "🟢 Active" if status["is_active"] else "⚪ Inactive"
                st.markdown(f"**Conversation:** {status_text}")
            with col2:
                voice_in = "🎤 Ready" if status["voice_input_available"] else "❌ Not Available"
                st.markdown(f"**Voice Input:** {voice_in}")
            with col3:
                voice_out = "🔊 Ready" if status["voice_output_available"] else "❌ Not Available"
                st.markdown(f"**Voice Output:** {voice_out}")
            
            st.markdown("---")
            
            # Audio Level Visualization
            st.markdown("### 📊 Audio Levels")
            
            # Use Streamlit's native progress bars for better visualization
            col_mic, col_ai = st.columns(2)
            
            with col_mic:
                st.markdown("**🎤 Microphone Input**")
                mic_level = st.session_state.get('mic_level', 0.0)
                
                # Convert level to 0-1 range for progress bar
                mic_progress = min(1.0, max(0.0, mic_level / 100.0))
                
                # Color coding based on level
                if mic_level < 20:
                    mic_status = "🟢 Quiet"
                elif mic_level < 60:
                    mic_status = "🟡 Moderate"
                else:
                    mic_status = "🔴 Loud"
                
                st.progress(mic_progress)
                st.caption(f"{mic_status} - {mic_level:.0f}%")
            
            with col_ai:
                st.markdown("**🔊 AI Voice Output**")
                ai_level = st.session_state.get('ai_speech_level', 0.0)
                
                # Convert level to 0-1 range for progress bar
                ai_progress = min(1.0, max(0.0, ai_level / 100.0))
                
                # Color coding based on level
                if ai_level < 20:
                    ai_status = "⚪ Silent"
                elif ai_level < 60:
                    ai_status = "🟡 Speaking"
                else:
                    ai_status = "🔴 Loud Speech"
                
                st.progress(ai_progress)
                st.caption(f"{ai_status} - {ai_level:.0f}%")
            
            # Audio monitoring controls
            st.markdown("**🎤 Microphone Testing**")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🎤 Start Mic Test", disabled=st.session_state.audio_monitoring):
                    if self.audio_visualizer and self.audio_visualizer.is_available():
                        if self.audio_visualizer.start_input_monitoring():
                            st.session_state.audio_monitoring = True
                            st.success("🎤 Microphone monitoring started!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to start microphone monitoring")
                    else:
                        # For now, simulate mic levels for testing the bars
                        st.session_state.audio_monitoring = True
                        st.session_state.mic_level = 25.0  # Test level
                        st.info("🎤 Demo mode: Mic test simulation started")
                        st.rerun()
            
            with col_b:
                if st.button("⏹️ Stop Mic Test", disabled=not st.session_state.audio_monitoring):
                    if self.audio_visualizer:
                        self.audio_visualizer.stop_input_monitoring()
                    st.session_state.audio_monitoring = False
                    st.session_state.mic_level = 0.0
                    st.session_state.ai_speech_level = 0.0
                    st.success("⏹️ Microphone monitoring stopped")
                    st.rerun()
            
            # Test AI Speech button
            st.markdown("**🔊 AI Speech Testing**")
            if st.button("🔊 Test AI Speech Levels"):
                st.session_state.ai_speech_level = 75.0  # Test level
                st.info("🔊 AI speech simulation: Level set to 75%")
                st.rerun()
            
            # Auto-refresh audio levels if monitoring
            if st.session_state.audio_monitoring:
                # Update microphone level (simulated for now)
                if self.audio_visualizer and self.audio_visualizer.is_available():
                    current_mic_level = self.audio_visualizer.get_input_level()
                    st.session_state.mic_level = current_mic_level
                    
                    # Update AI speech level
                    current_ai_level = self.audio_visualizer.get_output_level()
                    st.session_state.ai_speech_level = current_ai_level
                else:
                    # Simulate varying mic levels for demo
                    import random
                    st.session_state.mic_level = max(0, st.session_state.mic_level + random.randint(-5, 10))
                    st.session_state.mic_level = min(100, st.session_state.mic_level)
                
                # Auto-refresh for real-time visualization
                if st.session_state.mic_level > 5 or st.session_state.ai_speech_level > 5:
                    time.sleep(0.5)  # Slower refresh to see the bars better
                    st.rerun()
            
            # Instructions
            st.info("""
            **📋 How to test audio levels:**
            1. **🎤 Start Mic Test** - Begin monitoring your microphone
            2. **Speak into your mic** - Watch the blue progress bar move
            3. **🔊 Test AI Speech** - Simulate AI voice output
            4. **⏹️ Stop Mic Test** - End monitoring when done
            
            💡 **Note**: If bars don't move when speaking, we'll fix the microphone integration next!
            """)
            
            st.markdown("---")
            
            # Conversation controls
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🚀 Start Conversation", disabled=status["is_active"]):
                    context = ""
                    if st.session_state.processed_content:
                        context = f"Document: {st.session_state.current_document}"
                    
                    result = self.voice_conversation.start_conversation(context)
                    if result["status"] == "started":
                        st.session_state.voice_conversation_active = True
                        st.session_state.voice_conversation_history = [
                            {"role": "assistant", "content": result["message"], "timestamp": "now"}
                        ]
                        st.success("🎉 Conversation started! You can now talk with your AI tutor.")
                        st.rerun()
            
            with col2:
                if st.button("🎤 Listen & Respond", disabled=not status["is_active"]):
                    with st.spinner("🎤 Listening... Speak now!"):
                        result = self.voice_conversation.listen_and_respond(timeout=15)
                        
                        if result["status"] == "success":
                            st.session_state.voice_conversation_history.append({
                                "role": "user", 
                                "content": result["user_input"], 
                                "timestamp": "now"
                            })
                            st.session_state.voice_conversation_history.append({
                                "role": "assistant", 
                                "content": result["ai_response"], 
                                "timestamp": "now"
                            })
                            st.session_state.voice_last_response = result["ai_response"]
                            
                            # Simulate AI speech output level
                            if self.audio_visualizer:
                                self.audio_visualizer.simulate_output_speech(duration=3.0)
                            
                            st.success(f"✅ Heard: '{result['user_input']}'")
                            st.rerun()
                        elif result["status"] == "no_input":
                            st.warning("🤔 " + result["message"])
                        else:
                            st.error("❌ " + result["message"])
            
            with col3:
                if st.button("💬 Type & Continue", disabled=not status["is_active"]):
                    st.session_state.show_text_input = True
                    st.rerun()
            
            with col4:
                if st.button("⏹️ End Conversation", disabled=not status["is_active"]):
                    result = self.voice_conversation.end_conversation()
                    st.session_state.voice_conversation_active = False
                    st.success("👋 " + result["message"])
                    st.rerun()
            
            # Text input option
            if hasattr(st.session_state, 'show_text_input') and st.session_state.show_text_input:
                user_text = st.text_input("💬 Type your question:", key="voice_text_input")
                if user_text and st.button("Send"):
                    result = self.voice_conversation.continue_conversation(user_text)
                    if result["status"] == "success":
                        st.session_state.voice_conversation_history.append({
                            "role": "user", 
                            "content": result["user_input"], 
                            "timestamp": "now"
                        })
                        st.session_state.voice_conversation_history.append({
                            "role": "assistant", 
                            "content": result["ai_response"], 
                            "timestamp": "now"
                        })
                        
                        # Simulate AI speech output level
                        if self.audio_visualizer:
                            self.audio_visualizer.simulate_output_speech(duration=3.0)
                        
                        st.session_state.show_text_input = False
                        st.rerun()
            
            st.markdown("---")
            
            # Conversation History
            if st.session_state.voice_conversation_history:
                st.markdown("### 💬 Conversation History")
                
                # Display conversation in chat format
                for i, msg in enumerate(st.session_state.voice_conversation_history):
                    if msg["role"] == "user":
                        st.markdown(f"""
                        <div class="conversation-message" style="margin-left: 20px;">
                            <strong>🧑 You:</strong><br>{msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="conversation-message" style="margin-right: 20px; border-left-color: #4CAF50;">
                            <strong>🤖 AI Tutor:</strong><br>{msg["content"]}
                        </div>
                        """, unsafe_allow_html=True)
                
                # Clear history button
                if st.button("🗑️ Clear Conversation History"):
                    st.session_state.voice_conversation_history = []
                    st.rerun()
            
            else:
                st.markdown("### 💡 How to Use Voice Tutor")
                st.markdown("""
                1. **🚀 Start Conversation** - Begin a new chat session
                2. **🎤 Listen & Respond** - Click and speak your question
                3. **💬 Type & Continue** - Type if you prefer text input
                4. **⏹️ End Conversation** - Finish when you're done
                
                **Voice Commands:**
                - Say "goodbye" or "bye" to end
                - Say "repeat" to hear the last response again
                - Say "help" to get assistance
                
                **Tips:**
                - Speak clearly and at normal pace
                - Ensure your microphone is working
                - Questions can be about uploaded documents or general topics
                """)
        else:
            st.error("❌ Voice conversation system not initialized")
        
        st.markdown('</div>', unsafe_allow_html=True)

    def render_study_history_section(self):
        """Render the study history section"""
        st.header("📋 Study History & Progress")
        
        st.markdown("""
        ### 📊 Your Learning Journey
        Track your study sessions, conversation history, and progress over time.
        """)
        
        # Study statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            doc_count = 1 if st.session_state.processed_content else 0
            st.metric("📄 Documents Processed", doc_count)
        
        with col2:
            chat_count = len(st.session_state.messages)
            st.metric("💬 Chat Messages", chat_count)
        
        with col3:
            voice_count = len(st.session_state.voice_conversation_history)
            st.metric("🗣️ Voice Exchanges", voice_count)
        
        with col4:
            total_interactions = chat_count + voice_count
            st.metric("🎯 Total Interactions", total_interactions)
        
        # Recent activity
        if st.session_state.processed_content or st.session_state.messages or st.session_state.voice_conversation_history:
            st.markdown("### 📝 Recent Activity")
            
            # Show recent document
            if st.session_state.current_document:
                st.markdown(f"**📄 Latest Document:** {st.session_state.current_document}")
            
            # Show recent chat messages
            if st.session_state.messages:
                st.markdown("**💬 Recent Chat Messages:**")
                for msg in st.session_state.messages[-3:]:  # Last 3 messages
                    role = "🧑 You" if msg["role"] == "user" else "🤖 AI"
                    st.markdown(f"- {role}: {msg['content'][:100]}...")
            
            # Show recent voice conversations
            if st.session_state.voice_conversation_history:
                st.markdown("**🗣️ Recent Voice Exchanges:**")
                for msg in st.session_state.voice_conversation_history[-3:]:  # Last 3 exchanges
                    role = "🧑 You" if msg["role"] == "user" else "🤖 AI Tutor"
                    st.markdown(f"- {role}: {msg['content'][:100]}...")
        
        else:
            st.info("📝 No study activity yet. Start by uploading a document or having a voice conversation!")

    def run(self):
        """Main application runner"""
        # Render header
        self.render_header()
        
        # Render sidebar and get settings
        settings = self.render_sidebar()
        
        # Main content area with tabs
        tab1, tab2, tab3 = st.tabs(["📄 Document Processing", "🗣️ Voice Tutor", "📋 Study History"])
        
        with tab1:
            if st.session_state.processed_content:
                # Show summary and chat for processed documents
                self.render_summary_section()
                st.markdown("---")
                self.render_chat_section()
            else:
                # Show upload section and demo
                self.render_upload_section()
                st.markdown("---")
                self.render_demo_section()
        
        with tab2:
            self.render_voice_conversation_section()
        
        with tab3:
            self.render_study_history_section()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 2rem;'>
            <p>📚 AI Study Assistant - Empowering Education Through AI</p>
            <p>🎯 Week 1-2 Progress: Core PDF processing ✅ | AI integration ✅ | Basic UI ✅</p>
            <p>Built with ❤️ for students • <a href='#'>GitHub</a> • <a href='#'>Documentation</a></p>
        </div>
        """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    app = SimplifiedStudyAssistant()
    app.run()
