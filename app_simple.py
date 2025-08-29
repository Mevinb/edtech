import streamlit as st
import os
import tempfile
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
</style>
""", unsafe_allow_html=True)

class SimplifiedStudyAssistant:
    def __init__(self):
        # Initialize components that are available
        self.pdf_processor = PDFProcessor() if PDF_AVAILABLE else None
        self.ai_engine = AIEngine() if AI_AVAILABLE else None
        self.db_manager = DatabaseManager() if DB_AVAILABLE else None
        
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
        
        # Status indicators
        col1, col2, col3, col4 = st.columns(4)
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
                
        except Exception as e:
            st.error(f"❌ Error processing document: {str(e)}")

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
            <p>🎯 Week 1-2 Progress: Core PDF processing ✅ | AI integration ✅ | Basic UI ✅</p>
            <p>Built with ❤️ for students • <a href='#'>GitHub</a> • <a href='#'>Documentation</a></p>
        </div>
        """, unsafe_allow_html=True)

# Run the application
if __name__ == "__main__":
    app = SimplifiedStudyAssistant()
    app.run()
