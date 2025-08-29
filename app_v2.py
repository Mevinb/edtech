"""
Enhanced AI Study Assistant - Phase 2
Includes Quiz Generator, Difficulty Adapter, Progress Tracking, and Voice Features
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
import pandas as pd
from pathlib import Path
import uuid

# Import existing modules
from backend.services.pdf_processor import PDFProcessor
from backend.services.ai_engine import AIEngine
from backend.models.document import Document
from backend.utils.database import DatabaseManager

# Import new Phase 2 modules
from backend.services.quiz_generator import QuizGenerator, DifficultyLevel, QuestionType
from backend.services.difficulty_adapter import DifficultyAdapter
from backend.services.progress_tracker import ProgressTracker, QuizResult

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant v2.0",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())
if 'current_document' not in st.session_state:
    st.session_state.current_document = None
if 'difficulty_level' not in st.session_state:
    st.session_state.difficulty_level = DifficultyLevel.TEEN
if 'quiz_mode' not in st.session_state:
    st.session_state.quiz_mode = False
if 'current_quiz' not in st.session_state:
    st.session_state.current_quiz = None
if 'study_session_id' not in st.session_state:
    st.session_state.study_session_id = None

# Custom CSS for enhanced UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #2E86AB;
        font-size: 3rem;
        margin-bottom: 2rem;
    }
    .difficulty-selector {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .quiz-card {
        background: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .progress-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .achievement-badge {
        background: #ffd700;
        color: #333;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
        font-weight: bold;
    }
    .tab-content {
        padding: 2rem;
        min-height: 500px;
    }
</style>
""", unsafe_allow_html=True)

def initialize_services():
    """Initialize all services"""
    if 'services_initialized' not in st.session_state:
        try:
            st.session_state.pdf_processor = PDFProcessor()
            st.session_state.ai_engine = AIEngine()
            st.session_state.db_manager = DatabaseManager()
            st.session_state.quiz_generator = QuizGenerator(st.session_state.ai_engine)
            st.session_state.difficulty_adapter = DifficultyAdapter(st.session_state.ai_engine)
            st.session_state.progress_tracker = ProgressTracker()
            
            # Create user profile
            st.session_state.progress_tracker.create_user(
                st.session_state.user_id, 
                "Student", 
                st.session_state.difficulty_level.value
            )
            
            st.session_state.services_initialized = True
            return True
        except Exception as e:
            st.error(f"Error initializing services: {e}")
            return False
    return True

def render_difficulty_selector():
    """Render difficulty level selector"""
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
        "Select difficulty level:",
        options=list(difficulty_options.keys()),
        index=list(difficulty_options.keys()).index(current_option) if current_option else 1,
        help="Choose the explanation style that matches your learning level"
    )
    
    st.session_state.difficulty_level = difficulty_options[selected]
    
    # Show difficulty description
    descriptions = {
        DifficultyLevel.KID: "🌟 Simple explanations with fun examples and stories",
        DifficultyLevel.TEEN: "🎯 Clear explanations with relatable examples",
        DifficultyLevel.COLLEGE: "🔬 Technical depth with academic rigor"
    }
    
    st.info(descriptions[st.session_state.difficulty_level])

def render_learn_tab():
    """Render the Learn tab content"""
    st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
    
    # Difficulty selector
    render_difficulty_selector()
    
    # Document upload section
    st.markdown("### 📄 Upload Learning Material")
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload NCERT textbooks or any educational PDF"
    )
    
    if uploaded_file is not None:
        if st.button("📚 Process Document"):
            with st.spinner("Processing PDF..."):
                try:
                    # Save uploaded file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        temp_path = tmp_file.name
                    
                    # Process PDF
                    text_content = st.session_state.pdf_processor.extract_text(temp_path)
                    
                    if text_content:
                        # Create document
                        document = Document(
                            title=uploaded_file.name,
                            content=text_content,
                            file_path=temp_path,
                            upload_date=datetime.now()
                        )
                        
                        # Save to database
                        doc_id = st.session_state.db_manager.save_document(document)
                        st.session_state.current_document = document
                        
                        # Start study session
                        st.session_state.study_session_id = st.session_state.progress_tracker.start_study_session(
                            st.session_state.user_id,
                            uploaded_file.name,
                            st.session_state.difficulty_level.value
                        )
                        
                        st.success(f"✅ Document '{uploaded_file.name}' processed successfully!")
                        
                        # Clean up
                        os.unlink(temp_path)
                        
                    else:
                        st.error("Could not extract text from PDF. Please try a different file.")
                        
                except Exception as e:
                    st.error(f"Error processing document: {e}")
    
    # Q&A Section
    if st.session_state.current_document:
        st.markdown("### 💬 Ask Questions About Your Document")
        
        question = st.text_input(
            "What would you like to learn?",
            placeholder="e.g., What is photosynthesis? Explain gravity in simple terms."
        )
        
        if question and st.button("🔍 Get Answer"):
            with st.spinner("Generating adaptive answer..."):
                try:
                    # Get AI response
                    context = st.session_state.current_document.content[:3000]  # Limit context
                    prompt = f"""
                    Based on this educational content, answer the student's question: {question}
                    
                    Content: {context}
                    
                    Provide a helpful, accurate answer based on the content.
                    """
                    
                    raw_answer = st.session_state.ai_engine.generate_response(prompt)
                    
                    # Adapt answer to difficulty level
                    adapted_response = st.session_state.difficulty_adapter.adapt_explanation(
                        raw_answer,
                        st.session_state.difficulty_level,
                        question
                    )
                    
                    # Display answer
                    st.markdown("#### 🤖 AI Answer:")
                    st.markdown(f"**Level**: {st.session_state.difficulty_level.value.title()}")
                    st.write(adapted_response.adapted_response)
                    
                    if adapted_response.examples_used:
                        st.markdown("**Examples used:**")
                        for example in adapted_response.examples_used:
                            st.write(f"• {example}")
                    
                    # Update session stats
                    # TODO: Track questions asked
                    
                except Exception as e:
                    st.error(f"Error generating answer: {e}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_quiz_tab():
    """Render the Quiz tab content"""
    st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
    
    if not st.session_state.current_document:
        st.warning("📚 Please upload and process a document first to generate quizzes!")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    st.markdown("### 🎯 Test Your Knowledge")
    
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
    
    if st.button("🎲 Generate Quiz"):
        with st.spinner("Creating your personalized quiz..."):
            try:
                quiz = st.session_state.quiz_generator.generate_quiz(
                    st.session_state.current_document.content,
                    st.session_state.difficulty_level,
                    num_questions,
                    selected_types
                )
                
                st.session_state.current_quiz = quiz
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                
                st.success(f"✅ Generated {len(quiz.questions)} questions!")
                
            except Exception as e:
                st.error(f"Error generating quiz: {e}")
    
    # Display quiz
    if st.session_state.current_quiz and not st.session_state.get('quiz_submitted', False):
        st.markdown("---")
        st.markdown(f"### 📝 {st.session_state.current_quiz.title}")
        st.markdown(f"**Difficulty**: {st.session_state.difficulty_level.value.title()}")
        st.markdown(f"**Questions**: {len(st.session_state.current_quiz.questions)}")
        st.markdown(f"**Estimated time**: {st.session_state.current_quiz.estimated_time} minutes")
        
        # Quiz questions
        for i, question in enumerate(st.session_state.current_quiz.questions):
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
        if st.button("📊 Submit Quiz"):
            score, results = evaluate_quiz()
            st.session_state.quiz_submitted = True
            st.rerun()
    
    # Show quiz results
    if st.session_state.get('quiz_submitted', False):
        show_quiz_results()
    
    st.markdown("</div>", unsafe_allow_html=True)

def evaluate_quiz():
    """Evaluate the current quiz"""
    quiz = st.session_state.current_quiz
    answers = st.session_state.quiz_answers
    
    total_score = 0
    results = []
    
    for question in quiz.questions:
        user_answer = answers.get(question.id, "")
        evaluation = st.session_state.quiz_generator.evaluate_answer(question, user_answer)
        results.append(evaluation)
        total_score += evaluation["score"]
    
    # Calculate percentage
    percentage = (total_score / len(quiz.questions)) * 100
    
    # Record results
    weak_areas = [
        quiz.questions[i].topic for i, result in enumerate(results) 
        if not result["correct"]
    ]
    
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
    
    st.session_state.progress_tracker.record_quiz_result(quiz_result)
    st.session_state.quiz_results = results
    st.session_state.quiz_score = percentage
    
    return percentage, results

def show_quiz_results():
    """Display quiz results"""
    st.markdown("### 🎉 Quiz Results")
    
    score = st.session_state.quiz_score
    results = st.session_state.quiz_results
    
    # Score display
    score_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
    st.markdown(f"<h2 style='color: {score_color}'>Score: {score:.1f}%</h2>", unsafe_allow_html=True)
    
    # Performance message
    if score >= 90:
        st.success("🏆 Excellent! You've mastered this topic!")
    elif score >= 75:
        st.success("🎯 Great job! You have a solid understanding.")
    elif score >= 60:
        st.warning("📚 Good effort! Review the missed topics and try again.")
    else:
        st.error("🔄 Keep studying! Practice makes perfect.")
    
    # Detailed results
    st.markdown("### 📋 Detailed Results")
    
    for i, (question, result) in enumerate(zip(st.session_state.current_quiz.questions, results)):
        with st.expander(f"Question {i+1} {'✅' if result['correct'] else '❌'}"):
            st.write(f"**Question**: {question.question}")
            st.write(f"**Your answer**: {result['user_answer']}")
            st.write(f"**Correct answer**: {result['correct_answer']}")
            if result['explanation']:
                st.write(f"**Explanation**: {result['explanation']}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Again"):
            st.session_state.quiz_submitted = False
            st.rerun()
    
    with col2:
        if st.button("🎲 New Quiz"):
            st.session_state.current_quiz = None
            st.session_state.quiz_submitted = False
            st.rerun()

def render_progress_tab():
    """Render the Progress tab content"""
    st.markdown("<div class='tab-content'>", unsafe_allow_html=True)
    
    # Get user statistics
    stats = st.session_state.progress_tracker.get_user_stats(st.session_state.user_id)
    achievements = st.session_state.progress_tracker.get_user_achievements(st.session_state.user_id)
    
    st.markdown("### 📊 Your Learning Progress")
    
    # Key stats cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='progress-card'>
            <h3>⏱️ {stats.total_study_time}</h3>
            <p>Minutes Studied</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='progress-card'>
            <h3>📚 {stats.documents_studied}</h3>
            <p>Documents Read</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='progress-card'>
            <h3>🎯 {stats.quizzes_completed}</h3>
            <p>Quizzes Completed</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class='progress-card'>
            <h3>🔥 {stats.current_streak}</h3>
            <p>Day Streak</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional stats
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Performance")
        if stats.quizzes_completed > 0:
            st.metric("Average Quiz Score", f"{stats.average_quiz_score}%")
        st.metric("Longest Streak", f"{stats.longest_streak} days")
        
        if stats.favorite_subjects:
            st.markdown("#### 📖 Favorite Subjects")
            for subject in stats.favorite_subjects:
                st.write(f"• {subject}")
    
    with col2:
        st.markdown("#### 🎯 Areas for Improvement")
        if stats.improvement_areas:
            for area in stats.improvement_areas:
                st.write(f"• {area}")
        else:
            st.write("Keep up the great work! 🌟")
    
    # Achievements
    st.markdown("### 🏆 Achievements")
    
    unlocked_achievements = [a for a in achievements if a.unlocked_date]
    locked_achievements = [a for a in achievements if not a.unlocked_date]
    
    if unlocked_achievements:
        st.markdown("#### ✨ Unlocked")
        for achievement in unlocked_achievements:
            st.markdown(f"""
            <div class='achievement-badge'>
                {achievement.icon} {achievement.title}
            </div>
            """, unsafe_allow_html=True)
            st.write(f"*{achievement.description}*")
    
    if locked_achievements:
        st.markdown("#### 🔒 Locked")
        for achievement in locked_achievements:
            progress_percent = min(100, (achievement.current_value / achievement.target_value) * 100)
            st.write(f"{achievement.icon} **{achievement.title}** - {achievement.description}")
            st.progress(progress_percent / 100)
            st.write(f"Progress: {achievement.current_value}/{achievement.target_value}")
    
    st.markdown("</div>", unsafe_allow_html=True)

def main():
    """Main application"""
    # Header
    st.markdown("<h1 class='main-header'>🤖 AI Study Assistant v2.0</h1>", unsafe_allow_html=True)
    st.markdown("*Your intelligent learning companion with adaptive difficulty and progress tracking*")
    
    # Initialize services
    if not initialize_services():
        st.stop()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📚 Learn", "🎯 Quiz", "📊 Progress"])
    
    with tab1:
        render_learn_tab()
    
    with tab2:
        render_quiz_tab()
    
    with tab3:
        render_progress_tab()
    
    # Sidebar with additional features
    with st.sidebar:
        st.markdown("### 🎛️ Settings")
        
        # Quick stats
        if st.session_state.get('services_initialized'):
            stats = st.session_state.progress_tracker.get_user_stats(st.session_state.user_id)
            st.markdown(f"**Study Time**: {stats.total_study_time} min")
            st.markdown(f"**Current Streak**: {stats.current_streak} days")
            st.markdown(f"**Quiz Average**: {stats.average_quiz_score}%")
        
        st.markdown("---")
        
        # End study session
        if st.session_state.study_session_id:
            if st.button("🏁 End Study Session"):
                st.session_state.progress_tracker.end_study_session(
                    st.session_state.study_session_id,
                    pages_studied=1,  # TODO: Track actual pages
                    questions_asked=1  # TODO: Track actual questions
                )
                st.session_state.study_session_id = None
                st.success("Study session ended!")
        
        st.markdown("---")
        st.markdown("### 🚀 Phase 2 Features")
        st.markdown("✅ Adaptive Difficulty")
        st.markdown("✅ Quiz Generator") 
        st.markdown("✅ Progress Tracking")
        st.markdown("🔄 Voice Features (Coming Soon)")
        st.markdown("🔄 Mobile App (Coming Soon)")

if __name__ == "__main__":
    main()
