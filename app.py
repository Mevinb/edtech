import streamlit as st
import os
import tempfile
from datetime import datetime
import pandas as pd
from pathlib import Path

# Import our custom modules
from backend.services.pdf_processor import PDFProcessor
from backend.services.ai_engine import AIEngine
from backend.models.document import Document
from backend.utils.database import DatabaseManager

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
</style>
""", unsafe_allow_html=True)

class StudyAssistantApp:
    def __init__(self):
        self.pdf_processor = PDFProcessor()
        self.ai_engine = AIEngine()
        self.db_manager = DatabaseManager()
        
        # Initialize session state
        if 'messages' not in st.session_state:
            st.session_state.messages = []
        if 'current_document' not in st.session_state:
            st.session_state.current_document = None
        if 'processed_content' not in st.session_state:
            st.session_state.processed_content = None

    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">📚 AI Study Assistant 🤖</h1>', unsafe_allow_html=True)
        st.markdown("---")
        
        # Quick stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents Processed", "12", "3")
        with col2:
            st.metric("Questions Answered", "48", "8")
        with col3:
            st.metric("Study Sessions", "6", "1")
        with col4:
            st.metric("Success Rate", "94%", "2%")

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
            
            # AI Model selection
            st.subheader("🤖 AI Settings")
            model_choice = st.radio(
                "Choose AI Model",
                ["OpenAI GPT (High Quality)", "Hugging Face (Free)", "Local Model (Offline)"],
                index=1
            )
            
            # Language preference
            language = st.selectbox(
                "Response Language",
                ["English", "Hindi", "Hinglish (Mix)"],
                index=0
            )
            
            st.markdown("---")
            
            # Document history
            st.subheader("📖 Recent Documents")
            recent_docs = self.db_manager.get_recent_documents(limit=5)
            
            if recent_docs:
                for doc in recent_docs:
                    if st.button(f"📄 {doc['title'][:30]}...", key=f"doc_{doc['id']}"):
                        self.load_document(doc['id'])
            else:
                st.info("No documents uploaded yet")
            
            return {
                'grade': grade,
                'subject': subject,
                'model': model_choice,
                'language': language
            }

    def render_upload_section(self):
        """Render the file upload section"""
        st.header("📎 Upload Your Study Material")
        
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
                
                # Generate summary
                st.text("🤖 Generating AI summary...")
                summary = self.ai_engine.generate_summary(extracted_text)
                progress_bar.progress(75)
                
                # Save to database
                st.text("💾 Saving processed content...")
                document = Document(
                    title=uploaded_file.name,
                    content=extracted_text,
                    summary=summary,
                    file_path=tmp_file_path,
                    upload_date=datetime.now()
                )
                
                doc_id = self.db_manager.save_document(document)
                progress_bar.progress(100)
                
                # Update session state
                st.session_state.current_document = document
                st.session_state.processed_content = {
                    'text': extracted_text,
                    'summary': summary,
                    'doc_id': doc_id
                }
                
                # Clean up
                os.unlink(tmp_file_path)
                
                st.success("✅ Document processed successfully!")
                st.balloons()
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")

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
                        st.metric("Reading Time", f"{len(st.session_state.processed_content['text']) // 200} min")
                        st.metric("Complexity Level", "Intermediate")
                    with col2:
                        st.metric("Key Concepts", len(key_points))
                        st.metric("Grade Level", "Class 9")
                
                st.markdown('</div>', unsafe_allow_html=True)

    def render_chat_section(self):
        """Render the Q&A chat section"""
        if st.session_state.processed_content:
            st.header("💬 Ask Questions About Your Document")
            
            # Chat history
            chat_container = st.container()
            
            with chat_container:
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
            
            # Quick question buttons
            st.markdown("### 🚀 Quick Questions")
            quick_questions = [
                "Summarize the main concept",
                "What are the key formulas?",
                "Give me practice questions",
                "Explain in simple terms"
            ]
            
            cols = st.columns(len(quick_questions))
            for i, question in enumerate(quick_questions):
                with cols[i]:
                    if st.button(question, key=f"quick_{i}"):
                        self.handle_user_question(question)

    def handle_user_question(self, question):
        """Handle user question and generate AI response"""
        try:
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            
            # Generate AI response
            with st.spinner("🤖 AI is thinking..."):
                context = st.session_state.processed_content['text']
                response = self.ai_engine.answer_question(question, context)
            
            # Add AI response
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Clear input
            st.session_state.chat_input = ""
            
            # Rerun to update chat
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating response: {str(e)}")

    def load_document(self, doc_id):
        """Load a document from database"""
        try:
            document = self.db_manager.get_document(doc_id)
            if document:
                st.session_state.current_document = document
                st.session_state.processed_content = {
                    'text': document.content,
                    'summary': document.summary,
                    'doc_id': doc_id
                }
                st.success(f"✅ Loaded document: {document.title}")
                st.rerun()
        except Exception as e:
            st.error(f"❌ Error loading document: {str(e)}")

    def render_demo_section(self):
        """Render demo section with sample content"""
        if not st.session_state.processed_content:
            st.header("🎯 Try Our Demo")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                ### 📖 Sample: NCERT Class 9 Science
                **Chapter 1: Matter in Our Surroundings**
                
                Experience how our AI assistant works with educational content:
                - ✅ Instant PDF processing
                - ✅ Smart summarization
                - ✅ Interactive Q&A
                - ✅ Student-friendly explanations
                """)
                
                if st.button("🚀 Load Demo Content", type="primary"):
                    self.load_demo_content()
            
            with col2:
                st.markdown("""
                ### 🎓 Perfect For:
                - **NCERT Textbooks** - All subjects and grades
                - **Reference Materials** - Additional study resources
                - **Notes & Handouts** - Teacher-provided materials
                - **Practice Papers** - Previous year questions
                
                ### 🔥 Key Features:
                - **Multi-language Support** - English, Hindi, Hinglish
                - **Grade-appropriate Responses** - Tailored explanations
                - **Offline Capability** - Works without internet
                - **Fast Processing** - Get answers in seconds
                """)

    def load_demo_content(self):
        """Load demo content for testing"""
        demo_content = {
            'text': """
            Matter in Our Surroundings
            
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
            1. Solid State
            2. Liquid State  
            3. Gaseous State
            
            Diffusion:
            The mixing of particles of two different types of matter on their own is called diffusion.
            For example, when we light an incense stick in one corner of our room, we can smell it sitting in the other corner. This is due to diffusion.
            """,
            'summary': {
                'overview': 'This chapter introduces the basic concept of matter and its physical nature. It explains that everything around us is made of matter, which consists of tiny particles that are constantly moving and have spaces between them.',
                'key_points': [
                    'Matter is anything that has mass and occupies space',
                    'All matter is made up of very small particles',
                    'Particles have spaces between them and are in continuous motion',
                    'Matter exists in three states: solid, liquid, and gas',
                    'Diffusion is the mixing of particles of different substances',
                    'Particles of matter attract each other'
                ]
            }
        }
        
        st.session_state.processed_content = demo_content
        st.session_state.current_document = "Demo: NCERT Class 9 Science - Matter"
        st.success("✅ Demo content loaded! Try asking questions below.")
        st.rerun()

    def run(self):
        """Main application runner"""
        # Render header
        self.render_header()
        
        # Render sidebar and get settings
        settings = self.render_sidebar()
        
        # Main content area
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
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; padding: 2rem;'>
            <p>📚 AI Study Assistant - Empowering Education Through AI</p>
            <p>Built with ❤️ for students • <a href='#'>Documentation</a> • <a href='#'>Support</a></p>
        </div>
        """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    app = StudyAssistantApp()
    app.run()
