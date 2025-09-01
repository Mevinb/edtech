# AI Study Assistant 📚🤖

An intelligent study companion that extracts, summarizes, and enables interactive Q&A with PDF educational content, specifically designed for NCERT textbooks and academic materials.

## 🎯 Features

### Phase 1 (Current) ✅
- **PDF Processing**: Extract text from NCERT PDFs and educational documents
- **AI Summarization**: Generate chapter summaries and key points
- **Interactive Q&A**: Chat-based questions about uploaded content
- **🗣️ Interactive Voice Tutor**: Natural voice conversations with AI (NEW!)
- **📊 Audio Visualization**: Real-time microphone and speech level bars (NEW!)
- **🎤 Voice Commands**: Speak naturally with the AI tutor (NEW!)
- **Student-Friendly**: Age-appropriate explanations for different grades
- **Multi-Model Support**: Custom AI engine with rule-based processing

### 🗣️ Voice Tutor Features (NEW!)
- **Natural Conversation**: Talk with AI like ChatGPT/Gemini but with voice
- **Real-time Audio Bars**: Visual feedback for microphone input and AI speech
- **Voice Commands**: "Start conversation", "goodbye", "repeat", "help"
- **Text + Voice**: Switch between typing and speaking seamlessly
- **Conversation History**: Track all your voice interactions
- **Audio Testing**: Built-in microphone and speaker testing tools

### Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit with tabbed interface (Phase 1) → React (Phase 2)
- **AI Engine**: Custom rule-based processing with educational vocabulary
- **PDF Processing**: PyPDF2, pdfplumber, PyMuPDF + OCR
- **🎤 Voice Processing**: SpeechRecognition, pyttsx3, Google TTS (NEW!)
- **📊 Audio Visualization**: PyAudio, NumPy for real-time audio levels (NEW!)
- **Storage**: SQLite + ChromaDB for vector storage
- **Deployment**: Local development → Cloud deployment

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Create .env file with your API keys
cp .env.example .env
# Edit .env with your OpenAI API key (optional for Hugging Face only)
```

### 3. Run the Application
```bash
# Start Streamlit UI with voice features
streamlit run app_simple.py

# The app will open with three tabs:
# 📄 Document Processing - Upload and analyze PDFs
# 🗣️ Voice Tutor - Interactive voice conversations
# 📋 Study History - Track your learning progress

# Or start FastAPI backend (optional)
python backend/main.py
```

### 4. Using Voice Features 🎤
```bash
# Install voice dependencies (if not already installed)
pip install speechrecognition pyttsx3 gtts pyaudio

# Test your setup:
# 1. Go to 🗣️ Voice Tutor tab
# 2. Click "🎤 Start Mic Test" to test microphone
# 3. Click "🚀 Start Conversation" to begin voice chat
# 4. Click "🎤 Listen & Respond" and speak your question
```

## 📋 Usage Example

### Upload NCERT PDF
1. **Upload**: "Class 9 Science Chapter 1: Matter in Our Surroundings"
2. **AI Processing**: Automatic text extraction and analysis
3. **Get Summary**: 
   - Short chapter explanation
   - Key points in bullet form
   - Important concepts highlighted

### Interactive Q&A (Text)
- **Student**: "What is diffusion?"
- **AI**: "Diffusion is when particles of one substance mix with particles of another substance on their own, without any external force. Think of it like when you spray perfume in one corner of a room - after some time, you can smell it everywhere because the perfume particles have mixed with air particles and spread throughout the room!"

### 🗣️ Voice Conversation (NEW!)
1. **Start Voice Chat**: Click "🚀 Start Conversation" in Voice Tutor tab
2. **Speak Your Question**: Click "🎤 Listen & Respond" and say "What is photosynthesis?"
3. **AI Responds**: Hear the AI explain concepts in natural speech
4. **Continue Conversation**: Keep asking follow-up questions naturally
5. **Visual Feedback**: Watch audio level bars show your mic input and AI speech

### 📊 Audio Visualization Features
- **🎤 Microphone Bar**: Blue progress bar shows your voice level in real-time
- **🔊 AI Speech Bar**: Orange progress bar shows when AI is speaking
- **Color Coding**: Green (quiet) → Yellow (moderate) → Red (loud)
- **Test Buttons**: Built-in tools to test microphone and speaker functionality

## 📁 Project Structure

```
ai-study-assistant/
├── app_simple.py          # Main Streamlit application with voice features
├── backend/
│   ├── main.py           # FastAPI server
│   ├── models/           # Data models
│   │   └── document.py   # Document processing models
│   ├── services/         # Business logic
│   │   ├── ai_engine.py           # Custom AI processing engine
│   │   ├── pdf_processor.py       # PDF text extraction
│   │   ├── voice_tutor.py         # Voice input/output (NEW!)
│   │   ├── voice_conversation.py  # Conversation management (NEW!)
│   │   └── audio_visualizer.py    # Real-time audio visualization (NEW!)
│   └── utils/            # Helper functions
│       └── database.py   # Database management
├── frontend/             # Future React app
├── data/
│   ├── uploads/          # Uploaded PDFs
│   ├── processed/        # Processed content
│   └── database/         # SQLite database
├── tests/                # Unit tests
└── docs/                 # Documentation
```

## 🎓 Educational Focus

### NCERT Support
- **Optimized for NCERT**: Special handling for Indian educational content
- **Grade-Level Adaptation**: Responses tailored to student age/grade
- **Curriculum Alignment**: Follows NCERT chapter structure and learning objectives

### Subject Coverage
- **Science**: Physics, Chemistry, Biology
- **Mathematics**: All grade levels
- **Social Science**: History, Geography, Civics
- **Languages**: English, Hindi literature support

## 🔧 Development Timeline

### Week 1-2: Core Foundation ✅
- [x] PDF extraction and processing
- [x] Custom AI model integration
- [x] Basic text summarization
- [x] CPU-based processing for speed

### Week 3-4: UI Development ✅
- [x] Streamlit tabbed interface
- [x] File upload system
- [x] Summary display
- [x] Real-time document processing

### Week 5-6: Interactive Features ✅
- [x] Q&A chat implementation
- [x] Context-aware responses
- [x] 🗣️ Voice tutor integration (NEW!)
- [x] 📊 Audio level visualization (NEW!)
- [x] Real-time conversation history

### Recent Additions (Current Week) 🆕
- [x] **Interactive Voice Tutor**: Natural voice conversations like ChatGPT/Gemini
- [x] **Audio Visualization**: Real-time microphone and AI speech level bars
- [x] **Voice Commands**: Start, stop, repeat, help voice commands
- [x] **Conversation Management**: Persistent chat history and context
- [x] **Audio Testing Tools**: Built-in microphone and speaker testing

### Month 2: Enhancement & Demo 🚧
- [ ] Microphone integration optimization
- [ ] Voice recognition accuracy improvements
- [ ] Performance optimization
- [ ] User feedback integration
- [ ] Classmate demonstration

## 🤖 AI Models

### Current Implementation
1. **Custom AI Engine**: Rule-based processing with 114-word educational vocabulary
2. **CPU-Optimized**: Fast processing without GPU requirements
3. **Context-Aware**: Maintains conversation history and document context

### Voice Processing Models
1. **Speech Recognition**: Google Speech Recognition + Sphinx (offline backup)
2. **Text-to-Speech**: pyttsx3 (local) + Google TTS (cloud backup)
3. **Audio Processing**: PyAudio for real-time microphone monitoring

### Previous Models (Archived)
- **OpenAI GPT-3.5/4**: High-quality summaries (removed for custom training)
- **Hugging Face BERT**: Free text understanding (replaced with custom engine)
- **Sentence-BERT**: Document similarity (integrated into custom engine)

## 🛠️ Advanced Features (Current & Future)

### Phase 2 Enhancements (Partially Implemented) 🚧
- [x] **🗣️ Voice Integration**: Audio Q&A capabilities with natural conversation
- [x] **📊 Audio Visualization**: Real-time speech and microphone level monitoring
- [ ] **Multi-Language Support**: Hindi, regional languages
- [ ] **Visual Learning**: Diagram extraction and explanation
- [ ] **Practice Tests**: Auto-generated quizzes from content
- [ ] **Progress Tracking**: Learning analytics and insights

### Phase 3 Scaling
- [ ] **Collaborative Learning**: Study groups and sharing
- [ ] **Teacher Dashboard**: Educator tools and insights
- [ ] **Mobile App**: Cross-platform accessibility
- [ ] **Cloud Deployment**: Scalable infrastructure
- [ ] **Advanced Voice**: Multiple voice personalities and accents

### 🎤 Voice Features In Development
- [ ] **Real-time Microphone Integration**: Direct hardware access for audio levels
- [ ] **Voice Training**: Custom voice models for better recognition
- [ ] **Noise Cancellation**: Background noise filtering
- [ ] **Multiple Language Voice**: Hindi and regional language voice support

## 📊 Performance Metrics

### Processing Speed
- **PDF Extraction**: ~2-5 seconds per page
- **AI Summarization**: ~5-15 seconds per chapter (CPU-optimized)
- **Q&A Response**: ~1-3 seconds per question (custom engine)
- **🎤 Voice Recognition**: ~2-5 seconds per spoken question
- **🔊 Voice Output**: ~1-3 seconds speech generation

### Accuracy Targets
- **Text Extraction**: >95% accuracy
- **Summary Quality**: Educational expert validation with custom vocabulary
- **Q&A Relevance**: Context-aware responses with conversation history
- **🗣️ Voice Recognition**: >90% accuracy for clear speech
- **📊 Audio Visualization**: Real-time level detection with <100ms latency

### System Requirements
- **RAM**: 4GB minimum, 8GB recommended
- **Processing**: CPU-based (no GPU required)
- **🎤 Audio**: Microphone and speakers/headphones for voice features
- **Storage**: 2GB for application and dependencies

## 🎤 Voice Tutor Setup Guide

### Quick Setup
```bash
# Install voice dependencies
pip install speechrecognition pyttsx3 gtts pyaudio numpy

# Test your microphone
python -c "import speech_recognition as sr; print('Microphone test:', sr.Microphone.list_microphone_names())"

# Run the app
streamlit run app_simple.py
```

### Voice Features Usage
1. **🗣️ Go to Voice Tutor Tab**: Click the "🗣️ Voice Tutor" tab in the app
2. **📊 Test Audio Levels**: Click "🎤 Start Mic Test" to see audio visualization bars
3. **🚀 Start Conversation**: Click "🚀 Start Conversation" to begin voice chat
4. **🎤 Speak**: Click "🎤 Listen & Respond" and speak your question clearly
5. **👂 Listen**: The AI will respond with voice and you'll see the audio bars move

### Voice Commands
- **"Hello"** or **"Hi"**: Start a conversation
- **"What is [topic]?"**: Ask educational questions
- **"Explain [concept]"**: Get detailed explanations
- **"Repeat"** or **"Say again"**: Repeat the last response
- **"Help"**: Get usage instructions
- **"Goodbye"** or **"Bye"**: End the conversation

### Troubleshooting Voice Issues
- **Microphone not working**: Check browser permissions for microphone access
- **Audio bars not moving**: Restart the app and test again
- **No voice output**: Check speakers/headphones and system volume
- **Recognition problems**: Speak clearly and at normal pace, avoid background noise
- **TTS errors**: The app will fallback to Google TTS automatically

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **NCERT**: For providing open educational resources
- **OpenAI**: For AI capabilities inspiration (now using custom engine)
- **Hugging Face**: For open-source AI model concepts
- **Streamlit**: For rapid UI development and excellent audio widget support
- **🎤 Voice Tech Community**: For speech recognition and TTS libraries
- **📊 PyAudio Contributors**: For real-time audio processing capabilities

---

**Built with ❤️ for students by students**

*Empowering education through AI - making learning accessible, interactive, and fun!*

🗣️ **Now with Voice**: Talk naturally with your AI tutor just like ChatGPT and Gemini!
