"""
AI Study Assistant - Unified Phase 1 & Phase 2
Complete learning platform with PDF processing, adaptive difficulty, quizzes, and progress tracking
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
import pandas as pd
from pathlib import Path
import uuid
import json

# Import existing modules
from backend.services.pdf_processor import PDFProcessor
from backend.services.ai_engine import AIEngine
from backend.models.document import Document, ChatMessage
from backend.utils.database import DatabaseManager

# Import Phase 2 modules
from backend.services.quiz_generator import QuizGenerator, DifficultyLevel, QuestionType
from backend.services.difficulty_adapter import DifficultyAdapter
from backend.services.progress_tracker import ProgressTracker, QuizResult
from backend.services.voice_tutor import VoiceTutor, create_audio_player_html, get_microphone_html

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant - Complete",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'processed_content' not in st.session_state:
    st.session_state.processed_content = None
if 'difficulty_level' not in st.session_state:
    st.session_state.difficulty_level = DifficultyLevel.TEEN
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = False
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'study_session_id' not in st.session_state:
    st.session_state.study_session_id = None
if 'voice_tutor' not in st.session_state:
    st.session_state.voice_tutor = VoiceTutor()
if 'voice_enabled' not in st.session_state:
    st.session_state.voice_enabled = False
if 'use_local_tts' not in st.session_state:
    st.session_state.use_local_tts = True

# Enhanced CSS for unified app
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .upload-section {
        border: 2px dashed #2E86AB;
        border-radius: 10px;
        padding: 2rem;
        margin: 1rem 0;
        text-align: center;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        margin-left: 2rem;
    }
    .ai-message {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        margin-right: 2rem;
    }
    .summary-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .difficulty-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        color: white;
    }
    .quiz-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .progress-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
    }
    .achievement-badge {
        background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .tab-content {
        padding: 2rem;
        min-height: 500px;
    }
    .quick-question-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        margin: 0.2rem;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

class UnifiedStudyAssistant:
    def __init__(self):
        """Initialize all services"""
        if 'services_initialized' not in st.session_state:
            try:
                self.pdf_processor = PDFProcessor()
                self.ai_engine = AIEngine()
                self.db_manager = DatabaseManager()
                self.quiz_generator = QuizGenerator(self.ai_engine)
                self.difficulty_adapter = DifficultyAdapter(self.ai_engine)
                self.progress_tracker = ProgressTracker()
                
                # Create user profile
                self.progress_tracker.create_user(
                    st.session_state.user_id, 
                    "Student", 
                    st.session_state.difficulty_level.value
                )
                
                st.session_state.services_initialized = True
                st.session_state.app_instance = self
            except Exception as e:
                st.error(f"Error initializing services: {e}")
                return
        else:
            # Retrieve from session state
            self.pdf_processor = st.session_state.app_instance.pdf_processor
            self.ai_engine = st.session_state.app_instance.ai_engine
            self.db_manager = st.session_state.app_instance.db_manager
            self.quiz_generator = st.session_state.app_instance.quiz_generator
            self.difficulty_adapter = st.session_state.app_instance.difficulty_adapter
            self.progress_tracker = st.session_state.app_instance.progress_tracker

    def generate_document_summary(self, text_content, document_name):
        """Generate a comprehensive summary of the document"""
        try:
            # Create a simpler, more reliable summary generation
            text_preview = text_content[:2000]  # Use first 2000 characters
            
            # Extract basic key points from the text
            sentences = text_content.split('. ')
            key_sentences = [s.strip() for s in sentences if len(s.strip()) > 50][:5]
            
            # Try to generate AI summary
            summary_prompt = f"""
            Create a brief summary of this educational content:
            
            {text_preview}
            
            Provide:
            1. A 2-3 sentence overview
            2. 3-5 key learning points
            3. Main topics covered
            
            Keep it simple and educational.
            """
            
            try:
                ai_response = self.ai_engine.answer_question(
                    "Create a summary of this educational content",
                    f"{summary_prompt}\n\nContent: {text_preview}"
                )
                
                # Parse the response more reliably
                lines = ai_response.split('\n')
                overview_lines = []
                key_points = []
                topics = []
                
                current_section = None
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if 'overview' in line.lower() or 'summary' in line.lower():
                        current_section = 'overview'
                        continue
                    elif 'key' in line.lower() and 'point' in line.lower():
                        current_section = 'key_points'
                        continue
                    elif 'topic' in line.lower():
                        current_section = 'topics'
                        continue
                    
                    # Extract content based on current section
                    if current_section == 'overview' and len(overview_lines) < 3:
                        if not line.startswith(('1.', '2.', '3.', '-', '•')):
                            overview_lines.append(line)
                    elif current_section == 'key_points' and len(key_points) < 5:
                        # Remove numbering and bullet points
                        clean_line = line.lstrip('0123456789.-• ').strip()
                        if clean_line and len(clean_line) > 10:
                            key_points.append(clean_line)
                    elif current_section == 'topics' and len(topics) < 5:
                        clean_line = line.lstrip('0123456789.-• ').strip()
                        if clean_line and len(clean_line) > 3:
                            topics.append(clean_line)
                
                # If sections are empty, extract from the full response
                if not overview_lines:
                    overview_lines = [ai_response[:200] + "..."]
                
                if not key_points:
                    key_points = key_sentences[:3]
                
                if not topics:
                    # Try to extract topics from document name and content
                    topics = self.extract_topics_from_content(text_preview, document_name)
                
                summary = {
                    "overview": ' '.join(overview_lines),
                    "key_points": key_points,
                    "topics": topics,
                    "difficulty_level": self.estimate_difficulty_level(text_content),
                    "estimated_reading_time": f"{len(text_content.split()) // 200} minutes"
                }
                
            except Exception as ai_error:
                print(f"AI summary generation failed: {ai_error}")
                # Fallback to rule-based summary
                summary = self.create_fallback_summary(text_content, document_name)
            
            return summary
            
        except Exception as e:
            print(f"Summary generation error: {e}")
            return self.create_fallback_summary(text_content, document_name)
    
    def extract_topics_from_content(self, text_content, document_name):
        """Extract topics from content and document name"""
        topics = []
        
        # Extract from document name
        name_parts = document_name.lower().replace('.pdf', '').replace('_', ' ').replace('-', ' ').split()
        for part in name_parts:
            if len(part) > 3 and part not in ['the', 'and', 'for', 'with', 'chapter', 'class', 'ncert']:
                topics.append(part.title())
        
        # Look for common educational keywords
        keywords = ['photosynthesis', 'gravity', 'atoms', 'molecules', 'physics', 'chemistry', 'biology', 
                   'mathematics', 'history', 'geography', 'science', 'evolution', 'cell', 'energy']
        
        text_lower = text_content.lower()
        for keyword in keywords:
            if keyword in text_lower and keyword.title() not in topics:
                topics.append(keyword.title())
        
        return topics[:5] if topics else ["General Educational Content"]
    
    def estimate_difficulty_level(self, text_content):
        """Estimate the difficulty level of the content"""
        # Simple heuristic based on vocabulary complexity
        complex_words = ['phenomenon', 'synthesis', 'analysis', 'molecular', 'quantum', 'thermodynamics']
        simple_words = ['what', 'how', 'why', 'simple', 'easy', 'basic']
        
        text_lower = text_content.lower()
        complex_count = sum(1 for word in complex_words if word in text_lower)
        simple_count = sum(1 for word in simple_words if word in text_lower)
        
        if complex_count > simple_count:
            return "advanced"
        elif simple_count > complex_count * 2:
            return "beginner"
        else:
            return "intermediate"
    
    def create_fallback_summary(self, text_content, document_name):
        """Create a basic summary when AI fails"""
        # Extract first few sentences as overview
        sentences = text_content.split('. ')
        overview_sentences = [s.strip() + '.' for s in sentences[:2] if len(s.strip()) > 20]
        overview = ' '.join(overview_sentences) if overview_sentences else f"This document contains educational content from {document_name}."
        
        # Create basic key points
        key_points = [
            "Document successfully processed and ready for study",
            "Content available for questions and answers",
            "Quiz generation enabled for this material"
        ]
        
        # Try to extract some meaningful sentences as key points
        meaningful_sentences = [s.strip() for s in sentences if 30 < len(s.strip()) < 100]
        if meaningful_sentences:
            key_points = meaningful_sentences[:3]
        
        return {
            "overview": overview,
            "key_points": key_points,
            "topics": self.extract_topics_from_content(text_content, document_name),
            "difficulty_level": "intermediate",
            "estimated_reading_time": f"{len(text_content.split()) // 200} minutes"
        }

    def render_header(self):
        """Render enhanced header with stats"""
        st.markdown('<h1 class="main-header">🤖 AI Study Assistant - Complete Learning Platform</h1>', unsafe_allow_html=True)
        
        # Get user stats
        if st.session_state.get('services_initialized'):
            stats = self.progress_tracker.get_user_stats(st.session_state.user_id)
            
            # Quick stats row
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>📚 {stats.documents_studied}</h3>
                    <p>Documents Studied</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>🎯 {stats.quizzes_completed}</h3>
                    <p>Quizzes Completed</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>⏱️ {stats.total_study_time}</h3>
                    <p>Minutes Studied</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class='metric-card'>
                    <h3>🔥 {stats.current_streak}</h3>
                    <p>Day Streak</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")

    def render_difficulty_selector(self):
        """Render difficulty level selector"""
        st.markdown('<div class="difficulty-selector">', unsafe_allow_html=True)
        st.markdown("### 🎯 Choose Your Learning Level")
        
        difficulty_options = {
            "👶 Kid Mode (8-12 years)": DifficultyLevel.KID,
            "🧑 Teen Mode (13-17 years)": DifficultyLevel.TEEN,
            "🎓 College Mode (18+ years)": DifficultyLevel.COLLEGE
        }
        
        current_option = None
        for option, level in difficulty_options.items():
            if level == st.session_state.difficulty_level:
                current_option = option
                break
        
        selected = st.radio(
            "Select your preferred explanation style:",
            options=list(difficulty_options.keys()),
            index=list(difficulty_options.keys()).index(current_option) if current_option else 1,
            help="This affects how concepts are explained to you"
        )
        
        st.session_state.difficulty_level = difficulty_options[selected]
        
        # Show difficulty description
        descriptions = {
            DifficultyLevel.KID: "🌟 Simple explanations with fun examples and stories",
            DifficultyLevel.TEEN: "🎯 Clear explanations with relatable examples",
            DifficultyLevel.COLLEGE: "🔬 Technical depth with academic rigor"
        }
        
        st.info(descriptions[st.session_state.difficulty_level])
        st.markdown('</div>', unsafe_allow_html=True)

    def process_document(self, uploaded_file):
        """Process uploaded PDF document"""
        try:
            with st.spinner("🔄 Processing your document..."):
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Save uploaded file temporarily
                status_text.text("📁 Saving file...")
                progress_bar.progress(10)
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Extract text
                status_text.text("📄 Extracting text from PDF...")
                progress_bar.progress(30)
                
                extracted_text = self.pdf_processor.extract_text(tmp_file_path)
                
                if not extracted_text:
                    st.error("Could not extract text from PDF. Please try a different file.")
                    return
                
                # Generate summary using AI
                status_text.text("🤖 Generating intelligent summary...")
                progress_bar.progress(60)
                
                # Create a more robust summary generation
                summary = self.generate_document_summary(extracted_text, uploaded_file.name)
                
                status_text.text("💾 Saving to database...")
                progress_bar.progress(80)
                
                # Create document object
                document = Document(
                    title=uploaded_file.name,
                    content=extracted_text,
                    summary=summary,  # Now providing the required summary
                    file_path=tmp_file_path,
                    upload_date=datetime.now(),
                    word_count=len(extracted_text.split()),
                    grade_level=st.session_state.difficulty_level.value
                )
                
                # Save to database
                doc_id = self.db_manager.save_document(document)
                progress_bar.progress(90)
                
                # Start study session
                st.session_state.study_session_id = self.progress_tracker.start_study_session(
                    st.session_state.user_id,
                    uploaded_file.name,
                    st.session_state.difficulty_level.value
                )
                
                # Update session state
                st.session_state.current_document = document
                st.session_state.processed_content = {
                    'text': extracted_text,
                    'summary': summary,
                    'doc_id': doc_id
                }
                
                progress_bar.progress(100)
                status_text.text("✅ Document processed successfully!")
                
                # Clean up
                os.unlink(tmp_file_path)
                
                st.success("🎉 Document ready for learning and quizzes!")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")

    def render_learn_tab(self):
        """Render the Learn tab - combines Phase 1 functionality"""
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        
        # Difficulty selector
        self.render_difficulty_selector()
        
        # Document upload section
        st.markdown("### 📄 Upload Your Study Material")
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file (NCERT textbooks, notes, study materials)",
            type="pdf",
            help="Upload any educational PDF to start learning"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("📚 Process Document", type="primary"):
                    self.process_document(uploaded_file)
            with col2:
                st.info("This will extract text, generate summary, and prepare the document for Q&A and quizzes")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Document summary section
        if st.session_state.processed_content:
            self.render_summary_section()
            
            # Q&A Section
            st.markdown("### 💬 Ask Questions About Your Document")
            self.render_chat_section()
        
        st.markdown("</div>", unsafe_allow_html=True)

    def render_summary_section(self):
        """Render document summary with enhanced styling"""
        summary = st.session_state.processed_content['summary']
        
        st.markdown('<div class="summary-box">', unsafe_allow_html=True)
        st.markdown("## 📋 Document Analysis")
        
        # Summary tabs
        tab1, tab2, tab3 = st.tabs(["📖 Overview", "🎯 Key Points", "📊 Analysis"])
        
        with tab1:
            st.markdown("### 📚 Content Overview")
            overview = summary.get('overview', 'No overview available')
            if overview and overview.strip():
                st.write(overview)
            else:
                st.write("This document has been successfully processed and is ready for study.")
            
            topics = summary.get('topics', [])
            if topics:
                st.markdown("### 🏷️ Topics Covered")
                for topic in topics:
                    if topic and topic.strip():
                        st.write(f"• {topic}")
            else:
                st.markdown("### 🏷️ Topics Covered")
                st.write("• Educational content ready for exploration")
        
        with tab2:
            st.markdown("### 🎯 Key Learning Points")
            key_points = summary.get('key_points', [])
            if key_points:
                for i, point in enumerate(key_points, 1):
                    if point and point.strip():
                        st.markdown(f"**{i}.** {point}")
            else:
                st.markdown("**1.** Content has been successfully extracted from your document")
                st.markdown("**2.** You can now ask questions about the material")
                st.markdown("**3.** Quiz generation is available for this content")
        
        with tab3:
            st.markdown("### 📊 Content Metrics")
            col1, col2 = st.columns(2)
            with col1:
                reading_time = summary.get('estimated_reading_time', 'Unknown')
                st.metric("� Reading Time", reading_time)
                difficulty = summary.get('difficulty_level', 'Intermediate')
                st.metric("📈 Difficulty", difficulty.title())
            with col2:
                if st.session_state.current_document:
                    word_count = getattr(st.session_state.current_document, 'word_count', 0)
                    st.metric("📄 Word Count", f"{word_count:,}" if word_count else "Unknown")
                    st.metric("🎯 Your Level", st.session_state.difficulty_level.value.title())
        
        st.markdown('</div>', unsafe_allow_html=True)

    def render_chat_section(self):
        """Enhanced chat section with adaptive responses"""
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    st.markdown(f'''
                    <div class="chat-message user-message">
                        <strong>👤 You:</strong> {message["content"]}
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div class="chat-message ai-message">
                        <strong>🤖 AI Tutor:</strong> {message["content"]}
                    </div>
                    ''', unsafe_allow_html=True)
        
        # Chat input
        if st.session_state.voice_enabled and st.session_state.voice_tutor.is_voice_input_available():
            # Voice input interface
            st.markdown(get_microphone_html(), unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                user_question = st.text_input(
                    "Ask anything about your document:",
                    placeholder="e.g., What is photosynthesis? Explain gravity in simple terms...",
                    key="chat_input"
                )
            
            with col2:
                if st.button("🎤 Voice", help="Click and speak your question"):
                    with st.spinner("🎤 Listening..."):
                        voice_text = st.session_state.voice_tutor.listen_for_question(timeout=10)
                        if voice_text:
                            st.success(f"Heard: {voice_text}")
                            # Set the voice text as the question and process it
                            self.handle_user_question(voice_text, use_voice=True)
                        else:
                            st.error("Could not understand speech. Please try again.")
            
            with col3:
                if st.button("Send 📤", type="primary"):
                    if user_question:
                        self.handle_user_question(user_question, use_voice=st.session_state.voice_enabled)
        else:
            # Regular text input interface
            col1, col2 = st.columns([4, 1])
            
            with col1:
                user_question = st.text_input(
                    "Ask anything about your document:",
                    placeholder="e.g., What is photosynthesis? Explain gravity in simple terms...",
                    key="chat_input"
                )
            
            with col2:
                if st.button("Send 📤", type="primary"):
                    if user_question:
                        self.handle_user_question(user_question)
        
        # Quick question buttons
        st.markdown("### 🚀 Quick Questions")
        st.info("💡 Click any button below to get instant answers about your document!")
        
        quick_questions = [
            "Summarize the main concept",
            "What are the key formulas?", 
            "Give me practice questions",
            "Explain in simple terms",
            "What should I remember?",
            "How does this work?"
        ]
        
        # Create two rows of buttons for better layout
        col1, col2, col3 = st.columns(3)
        
        for i, question in enumerate(quick_questions):
            with [col1, col2, col3][i % 3]:
                if st.button(
                    f"🔥 {question}", 
                    key=f"quick_{i}",
                    help=f"Click to ask: {question}",
                    use_container_width=True
                ):
                    st.info(f"🤖 Processing: {question}")
                    self.handle_user_question(question, use_voice=st.session_state.voice_enabled)

    def handle_user_question(self, question, use_voice=False):
        """Handle user questions with adaptive difficulty"""
        # Check if we have all required components
        if not st.session_state.get('services_initialized'):
            st.error("Please wait for services to initialize...")
            return
            
        if not st.session_state.get('processed_content'):
            st.error("Please upload and process a document first!")
            return
        
        try:
            # Add user message
            st.session_state.messages.append({
                "role": "user", 
                "content": question,
                "timestamp": datetime.now()
            })
            
            with st.spinner("🤖 AI Tutor is thinking..."):
                # Generate response based on document content
                context = st.session_state.processed_content['text'][:3000]
                
                # Create more specific prompts for different question types
                if "summarize" in question.lower() or "main concept" in question.lower():
                    prompt = f"""
                    Based on this educational content, provide a clear summary of the main concepts:
                    
                    Content: {context}
                    
                    Provide a concise summary highlighting the most important concepts and ideas.
                    """
                elif "formula" in question.lower():
                    prompt = f"""
                    Based on this educational content, identify and list the key formulas, equations, or important facts:
                    
                    Content: {context}
                    
                    List any formulas, equations, or key facts that students should remember.
                    """
                elif "practice questions" in question.lower():
                    prompt = f"""
                    Based on this educational content, suggest 3-5 practice questions that would help test understanding:
                    
                    Content: {context}
                    
                    Create practice questions that cover the main topics in this material.
                    """
                elif "remember" in question.lower():
                    prompt = f"""
                    Based on this educational content, list the most important points that a student should remember:
                    
                    Content: {context}
                    
                    Provide a list of key points, facts, or concepts that are essential to remember.
                    """
                elif "how does this work" in question.lower():
                    prompt = f"""
                    Based on this educational content, explain how the main processes or concepts work:
                    
                    Content: {context}
                    
                    Explain the mechanisms, processes, or how things work in this material.
                    """
                elif "simple terms" in question.lower():
                    prompt = f"""
                    Based on this educational content, explain the concepts in simple, easy-to-understand terms:
                    
                    Content: {context}
                    
                    Break down complex concepts into simple, clear explanations that anyone can understand.
                    """
                else:
                    # Generic question handling
                    prompt = f"""
                    Based on this educational content, answer the student's question: {question}
                    
                    Content: {context}
                    
                    Provide a helpful, accurate answer based on the content. Be educational and encouraging.
                    """
                
                try:
                    # Try to get AI response using the correct method
                    raw_response = self.ai_engine.answer_question(question, context)
                    
                    if not raw_response or raw_response.strip() == "":
                        raise Exception("Empty response from AI")
                    
                    # Adapt response to difficulty level
                    try:
                        adapted_response = self.difficulty_adapter.adapt_explanation(
                            raw_response,
                            st.session_state.difficulty_level,
                            question
                        )
                        final_response = adapted_response.adapted_response
                    except Exception as adapt_error:
                        print(f"Difficulty adaptation failed for level {st.session_state.difficulty_level.value}: {adapt_error}")
                        # Use raw response if adaptation fails
                        final_response = raw_response
                    
                except Exception as ai_error:
                    print(f"AI response generation failed: {ai_error}")
                    # Provide a fallback response
                    final_response = self.generate_fallback_response(question, context)
                
                # Add AI response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response,
                    "timestamp": datetime.now()
                })
                
                # Voice output if enabled
                if use_voice and st.session_state.voice_enabled and st.session_state.voice_tutor.is_voice_output_available():
                    try:
                        with st.spinner("🔊 Speaking response..."):
                            # Use local TTS for immediate response
                            audio_result = st.session_state.voice_tutor.speak_text(final_response, use_gtts=False)
                            if audio_result and audio_result.endswith('.mp3'):
                                # If Google TTS was used, display audio player
                                st.markdown("### 🔊 Audio Response")
                                st.markdown(create_audio_player_html(audio_result), unsafe_allow_html=True)
                                # Clean up temp file
                                try:
                                    os.unlink(audio_result)
                                except:
                                    pass
                            elif audio_result:
                                # Local TTS was used successfully
                                st.success("🔊 Response spoken aloud!")
                    except Exception as voice_error:
                        st.warning(f"Voice output failed: {voice_error}")
                        print(f"Voice error details: {voice_error}")
                
                st.success("✅ Response generated! Check the chat above.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Error generating response: {e}")
            # Add a fallback message
            fallback_message = f"I understand you asked: '{question}'. While I'm having technical difficulties, I can tell you that your document has been processed and contains valuable educational content. Please try asking your question again or use the text input to ask specific questions about the material."
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": fallback_message,
                "timestamp": datetime.now()
            })
            st.rerun()
    
    def generate_fallback_response(self, question, context):
        """Generate a basic response when AI fails"""
        question_lower = question.lower()
        
        if "summarize" in question_lower or "main concept" in question_lower:
            return f"This document contains educational content with key concepts and information. The main ideas revolve around the topics covered in your uploaded material. Based on the content, there are several important concepts that are explained in detail."
        
        elif "formula" in question_lower:
            return "This document may contain important formulas, equations, or key facts. Please review the document content for any mathematical expressions, scientific formulas, or important factual information that should be memorized."
        
        elif "practice questions" in question_lower:
            return """Here are some general practice questions you can consider:
            1. What are the main concepts explained in this material?
            2. How do the different topics relate to each other?
            3. What are the key facts or formulas mentioned?
            4. Can you explain the main processes described?
            5. What real-world applications are mentioned?"""
        
        elif "remember" in question_lower:
            return "The most important things to remember from this document include the main concepts, key terminology, important facts or formulas, and how different ideas connect together. Focus on understanding the core principles rather than memorizing everything."
        
        elif "how does this work" in question_lower:
            return "The document explains various processes and mechanisms. To understand how things work, look for step-by-step explanations, cause-and-effect relationships, and examples that illustrate the concepts in action."
        
        elif "simple terms" in question_lower:
            return "In simple terms, this document covers educational content that can be broken down into basic concepts. Think of the main ideas as building blocks - each concept builds on the previous ones to create a complete understanding of the topic."
        
        else:
            return f"I understand your question about '{question}'. While I'm having some technical difficulties accessing the AI engine right now, your document has been successfully processed and contains valuable information. Please try rephrasing your question or ask about specific topics you'd like to understand better."

    def render_quiz_tab(self):
        """Render the Quiz tab - Phase 2 functionality"""
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        
        if not st.session_state.current_document:
            st.warning("📚 Please upload and process a document in the **Learn** tab first!")
            st.info("Once you have a document loaded, you can generate custom quizzes to test your understanding.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        
        st.markdown("### 🎯 Test Your Knowledge")
        st.markdown(f"**Current Document**: {st.session_state.current_document.title}")
        st.markdown(f"**Difficulty Level**: {st.session_state.difficulty_level.value.title()}")
        
        # Quiz generation options
        col1, col2 = st.columns(2)
        
        with col1:
            num_questions = st.slider("Number of questions:", 3, 10, 5)
            
        with col2:
            question_types = st.multiselect(
                "Question types:",
                ["Multiple Choice", "True/False", "Fill in the Blank", "Short Answer"],
                default=["Multiple Choice", "True/False"]
            )
        
        # Convert to enum types
        type_mapping = {
            "Multiple Choice": QuestionType.MULTIPLE_CHOICE,
            "True/False": QuestionType.TRUE_FALSE,
            "Fill in the Blank": QuestionType.FILL_BLANK,
            "Short Answer": QuestionType.SHORT_ANSWER
        }
        selected_types = [type_mapping[t] for t in question_types]
        
        if st.button("🎲 Generate Personalized Quiz", type="primary"):
            if not selected_types:
                st.warning("Please select at least one question type!")
            else:
                with st.spinner("🤖 Creating your personalized quiz..."):
                    try:
                        quiz = self.quiz_generator.generate_quiz(
                            st.session_state.current_document.content,
                            st.session_state.difficulty_level,
                            num_questions,
                            selected_types
                        )
                        
                        st.session_state.current_quiz = quiz
                        st.session_state.quiz_answers = {}
                        st.session_state.quiz_submitted = False
                        
                        st.success(f"✅ Generated {len(quiz.questions)} questions tailored to your level!")
                        
                    except Exception as e:
                        st.error(f"Error generating quiz: {e}")
        
        # Display quiz
        if st.session_state.current_quiz and not st.session_state.get('quiz_submitted', False):
            self.render_quiz_questions()
        
        # Show quiz results
        if st.session_state.get('quiz_submitted', False):
            self.render_quiz_results()
        
        st.markdown("</div>", unsafe_allow_html=True)

    def render_quiz_questions(self):
        """Render quiz questions"""
        quiz = st.session_state.current_quiz
        
        st.markdown("---")
        st.markdown(f"### 📝 {quiz.title}")
        
        st.markdown('<div class="quiz-card">', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", len(quiz.questions))
        with col2:
            st.metric("Estimated Time", f"{quiz.estimated_time} min")
        with col3:
            st.metric("Difficulty", quiz.difficulty.value.title())
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quiz questions
        for i, question in enumerate(quiz.questions):
            st.markdown(f"#### Question {i+1}")
            st.write(question.question)
            
            if question.question_type == QuestionType.MULTIPLE_CHOICE:
                answer = st.radio(
                    "Select your answer:",
                    question.options,
                    key=f"q_{question.id}",
                    index=None
                )
                st.session_state.quiz_answers[question.id] = answer
                
            elif question.question_type == QuestionType.TRUE_FALSE:
                answer = st.radio(
                    "Select your answer:",
                    ["True", "False"],
                    key=f"q_{question.id}",
                    index=None
                )
                st.session_state.quiz_answers[question.id] = answer
                
            else:  # Fill blank or short answer
                answer = st.text_input(
                    "Your answer:",
                    key=f"q_{question.id}"
                )
                st.session_state.quiz_answers[question.id] = answer
            
            st.markdown("---")
        
        # Submit quiz
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                self.evaluate_quiz()
                st.session_state.quiz_submitted = True
                st.rerun()

    def evaluate_quiz(self):
        """Evaluate the current quiz and record results"""
        quiz = st.session_state.current_quiz
        answers = st.session_state.quiz_answers
        
        total_score = 0
        results = []
        
        for question in quiz.questions:
            user_answer = answers.get(question.id, "")
            evaluation = self.quiz_generator.evaluate_answer(question, user_answer)
            results.append(evaluation)
            total_score += evaluation["score"]
        
        # Calculate percentage
        percentage = (total_score / len(quiz.questions)) * 100
        
        # Identify weak areas
        weak_areas = [
            quiz.questions[i].topic for i, result in enumerate(results) 
            if not result["correct"] and quiz.questions[i].topic
        ]
        
        # Record results in progress tracker
        quiz_result = QuizResult(
            quiz_id=quiz.id,
            user_id=st.session_state.user_id,
            quiz_title=quiz.title,
            score=int(percentage),
            total_questions=len(quiz.questions),
            correct_answers=total_score,
            difficulty_level=quiz.difficulty.value,
            time_taken_minutes=quiz.estimated_time,  # TODO: Track actual time
            completion_date=datetime.now(),
            weak_areas=weak_areas
        )
        
        self.progress_tracker.record_quiz_result(quiz_result)
        
        # Store results in session state
        st.session_state.quiz_results = results
        st.session_state.quiz_score = percentage

    def render_quiz_results(self):
        """Display quiz results with detailed feedback"""
        score = st.session_state.quiz_score
        results = st.session_state.quiz_results
        
        st.markdown("### 🎉 Quiz Results")
        
        # Score display with color coding
        if score >= 90:
            score_color = "#28a745"
            message = "🏆 Outstanding! You've mastered this topic!"
            emoji = "🎉"
        elif score >= 75:
            score_color = "#ffc107"
            message = "🎯 Great job! You have a solid understanding."
            emoji = "👏"
        elif score >= 60:
            score_color = "#fd7e14"
            message = "📚 Good effort! Review the missed topics and try again."
            emoji = "📖"
        else:
            score_color = "#dc3545"
            message = "🔄 Keep studying! Practice makes perfect."
            emoji = "💪"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, {score_color}20 0%, {score_color}40 100%); border-radius: 10px; margin: 1rem 0;'>
            <h1 style='color: {score_color}; margin: 0;'>{emoji} {score:.1f}%</h1>
            <p style='font-size: 1.2rem; margin: 0.5rem 0;'>{message}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Performance breakdown
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Correct Answers", f"{sum(1 for r in results if r['correct'])}/{len(results)}")
        with col2:
            st.metric("Accuracy", f"{score:.1f}%")
        with col3:
            difficulty_bonus = {"kid": 1, "teen": 1.2, "college": 1.5}[st.session_state.difficulty_level.value]
            adjusted_score = min(100, score * difficulty_bonus)
            st.metric("Level-Adjusted Score", f"{adjusted_score:.1f}%")
        
        # Detailed results
        with st.expander("📋 View Detailed Results", expanded=False):
            for i, (question, result) in enumerate(zip(st.session_state.current_quiz.questions, results)):
                icon = "✅" if result['correct'] else "❌"
                st.markdown(f"**Question {i+1}** {icon}")
                st.write(f"**Q**: {question.question}")
                st.write(f"**Your answer**: {result['user_answer']}")
                st.write(f"**Correct answer**: {result['correct_answer']}")
                if result['explanation']:
                    st.write(f"**Explanation**: {result['explanation']}")
                st.markdown("---")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Retake Quiz"):
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.rerun()
        
        with col2:
            if st.button("🎲 New Quiz"):
                st.session_state.current_quiz = None
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.rerun()
        
        with col3:
            if st.button("📚 Back to Learn"):
                st.session_state.quiz_submitted = False
                # Switch to Learn tab (this would need tab state management)

    def render_progress_tab(self):
        """Render the Progress tab - Phase 2 analytics"""
        st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
        
        # Get user statistics
        stats = self.progress_tracker.get_user_stats(st.session_state.user_id)
        achievements = self.progress_tracker.get_user_achievements(st.session_state.user_id)
        
        st.markdown("### 📊 Your Learning Journey")
        
        # Main stats dashboard
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='progress-card'>
                <h2>📚 {stats.documents_studied}</h2>
                <p>Documents<br>Studied</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='progress-card'>
                <h2>🎯 {stats.quizzes_completed}</h2>
                <p>Quizzes<br>Completed</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class='progress-card'>
                <h2>⏱️ {stats.total_study_time}</h2>
                <p>Minutes<br>Studied</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='progress-card'>
                <h2>🔥 {stats.current_streak}</h2>
                <p>Day<br>Streak</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Performance Overview")
            if stats.quizzes_completed > 0:
                st.metric("Average Quiz Score", f"{stats.average_quiz_score}%", 
                         delta=f"+{stats.average_quiz_score - 70:.1f}%" if stats.average_quiz_score > 70 else None)
            st.metric("Longest Study Streak", f"{stats.longest_streak} days")
            st.metric("Learning Level", st.session_state.difficulty_level.value.title())
            
            if stats.favorite_subjects:
                st.markdown("#### 📖 Most Studied Topics")
                for i, subject in enumerate(stats.favorite_subjects[:3], 1):
                    st.write(f"{i}. {subject}")
        
        with col2:
            st.markdown("#### 🎯 Growth Areas")
            if stats.improvement_areas:
                st.write("Focus on these topics for better performance:")
                for area in stats.improvement_areas[:3]:
                    st.write(f"• {area}")
            else:
                st.success("🌟 Great job! Keep up the excellent work!")
            
            # Study recommendations
            st.markdown("#### 💡 Recommendations")
            if stats.current_streak == 0:
                st.write("📅 Start a daily study streak!")
            elif stats.average_quiz_score < 80:
                st.write("📚 Focus on review before taking quizzes")
            elif stats.quizzes_completed < 5:
                st.write("🎯 Take more quizzes to track progress")
            else:
                st.write("🚀 You're doing amazing! Try harder difficulty levels")
        
        # Achievements section
        st.markdown("### 🏆 Achievements & Badges")
        
        unlocked = [a for a in achievements if a.unlocked_date]
        locked = [a for a in achievements if not a.unlocked_date]
        
        if unlocked:
            st.markdown("#### ✨ Unlocked Achievements")
            cols = st.columns(min(4, len(unlocked)))
            for i, achievement in enumerate(unlocked):
                with cols[i % 4]:
                    st.markdown(f"""
                    <div class='achievement-badge'>
                        {achievement.icon} {achievement.title}
                    </div>
                    """, unsafe_allow_html=True)
                    st.write(f"*{achievement.description}*")
        
        if locked:
            st.markdown("#### 🔒 Locked Achievements")
            for achievement in locked[:3]:  # Show top 3 locked
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.write(f"{achievement.icon}")
                with col2:
                    st.write(f"**{achievement.title}** - {achievement.description}")
                    # Calculate progress
                    if achievement.id == "quiz_master":
                        progress = min(100, (stats.quizzes_completed / 10) * 100)
                    elif achievement.id == "time_scholar":
                        progress = min(100, (stats.total_study_time / 600) * 100)
                    elif achievement.id == "study_streak_7":
                        progress = min(100, (stats.current_streak / 7) * 100)
                    else:
                        progress = 0
                    
                    st.progress(progress / 100)
                    st.write(f"Progress: {progress:.0f}%")
        
        st.markdown("</div>", unsafe_allow_html=True)

    def render_sidebar(self):
        """Enhanced sidebar with controls and quick stats"""
        with st.sidebar:
            st.markdown("### 🎛️ Learning Dashboard")
            
            # Current document info
            if st.session_state.current_document:
                st.markdown("#### 📖 Current Document")
                st.write(f"**{st.session_state.current_document.title}**")
                st.write(f"Level: {st.session_state.difficulty_level.value.title()}")
                
                # Study session controls
                if st.session_state.study_session_id:
                    if st.button("🏁 End Study Session"):
                        self.progress_tracker.end_study_session(
                            st.session_state.study_session_id,
                            pages_studied=1,  # TODO: Track actual pages
                            questions_asked=len(st.session_state.messages) // 2  # Approximate questions
                        )
                        st.session_state.study_session_id = None
                        st.success("Study session ended!")
                        st.rerun()
            
            st.markdown("---")
            
            # Voice Tutor Settings
            st.markdown("#### 🎤 Voice Tutor")
            voice_settings = st.session_state.voice_tutor.get_voice_settings()
            
            if voice_settings["input_available"] or voice_settings["output_available"]:
                st.session_state.voice_enabled = st.checkbox(
                    "Enable Voice Tutor", 
                    value=st.session_state.voice_enabled,
                    help="Turn on voice input/output features"
                )
                
                if st.session_state.voice_enabled:
                    if voice_settings["output_available"]:
                        st.write("🔊 Voice Output: Available")
                        
                        # Voice preference
                        use_local_tts = st.checkbox(
                            "Use Local Voice (Recommended)", 
                            value=True,
                            help="Local voice works offline and is more reliable"
                        )
                        st.session_state.use_local_tts = use_local_tts
                        
                        # Voice settings
                        if st.session_state.voice_tutor.tts_engine:
                            voice_rate = st.slider(
                                "Speech Rate", 
                                min_value=50, 
                                max_value=300, 
                                value=150,
                                help="Words per minute"
                            )
                            st.session_state.voice_tutor.set_voice_rate(voice_rate)
                            
                            voice_volume = st.slider(
                                "Speech Volume", 
                                min_value=0.0, 
                                max_value=1.0, 
                                value=0.8,
                                step=0.1
                            )
                            st.session_state.voice_tutor.set_voice_volume(voice_volume)
                    else:
                        st.write("🔇 Voice Output: Not Available")
                    
                    if voice_settings["input_available"]:
                        st.write("🎤 Voice Input: Available")
                    else:
                        st.write("🎤 Voice Input: Not Available")
            else:
                st.warning("Voice features require additional packages")
                if st.button("📋 Show Installation Instructions"):
                    st.code("""
pip install speechrecognition
pip install pyttsx3
pip install gtts
pip install pyaudio  # For microphone access
                    """)
            
            st.markdown("---")
            
            # Quick stats
            if st.session_state.get('services_initialized'):
                stats = self.progress_tracker.get_user_stats(st.session_state.user_id)
                st.markdown("#### 📊 Quick Stats")
                st.metric("Study Time Today", f"{stats.total_study_time} min")
                st.metric("Current Streak", f"{stats.current_streak} days")
                if stats.quizzes_completed > 0:
                    st.metric("Quiz Average", f"{stats.average_quiz_score}%")
            
            st.markdown("---")
            
            # Feature status
            st.markdown("#### ✨ Features")
            st.markdown("✅ PDF Processing")
            st.markdown("✅ Adaptive Q&A")
            st.markdown("✅ Smart Quizzes")
            st.markdown("✅ Progress Tracking")
            st.markdown("✅ Achievements")
            st.markdown("🔄 Voice Features (Soon)")
            
            st.markdown("---")
            
            # Tips
            st.markdown("#### 💡 Study Tips")
            tips = [
                "📚 Upload PDFs in the Learn tab",
                "🎯 Take quizzes to test knowledge", 
                "🔥 Maintain daily study streaks",
                "📈 Check progress regularly",
                "🎓 Adjust difficulty as you learn"
            ]
            
            for tip in tips:
                st.write(tip)

def main():
    """Main application entry point"""
    app = UnifiedStudyAssistant()
    
    # Render header
    app.render_header()
    
    # Main navigation tabs
    tab1, tab2, tab3 = st.tabs(["📚 Learn & Study", "🎯 Take Quiz", "📊 Track Progress"])
    
    with tab1:
        app.render_learn_tab()
    
    with tab2:
        app.render_quiz_tab()
    
    with tab3:
        app.render_progress_tab()
    
    # Render sidebar
    app.render_sidebar()

if __name__ == "__main__":
    main()
