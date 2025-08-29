# AI Study Assistant 📚🤖

An intelligent study companion that extracts, summarizes, and enables interactive Q&A with PDF educational content, specifically designed for NCERT textbooks and academic materials.

## 🎯 Features

### Phase 1 (Current)
- **PDF Processing**: Extract text from NCERT PDFs and educational documents
- **AI Summarization**: Generate chapter summaries and key points
- **Interactive Q&A**: Chat-based questions about uploaded content
- **Student-Friendly**: Age-appropriate explanations for different grades
- **Multi-Model Support**: OpenAI API + Hugging Face free models

### Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Streamlit (Phase 1) → React (Phase 2)
- **AI Engine**: OpenAI GPT + Hugging Face Transformers
- **PDF Processing**: PyPDF2, pdfplumber, PyMuPDF + OCR
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
# Start Streamlit UI
streamlit run app.py

# Or start FastAPI backend (optional)
python backend/main.py
```

## 📋 Usage Example

### Upload NCERT PDF
1. **Upload**: "Class 9 Science Chapter 1: Matter in Our Surroundings"
2. **AI Processing**: Automatic text extraction and analysis
3. **Get Summary**: 
   - Short chapter explanation
   - Key points in bullet form
   - Important concepts highlighted

### Interactive Q&A
- **Student**: "What is diffusion?"
- **AI**: "Diffusion is when particles of one substance mix with particles of another substance on their own, without any external force. Think of it like when you spray perfume in one corner of a room - after some time, you can smell it everywhere because the perfume particles have mixed with air particles and spread throughout the room!"

## 📁 Project Structure

```
ai-study-assistant/
├── app.py                 # Main Streamlit application
├── backend/
│   ├── main.py           # FastAPI server
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   └── utils/            # Helper functions
├── frontend/             # Future React app
├── data/
│   ├── uploads/          # Uploaded PDFs
│   ├── processed/        # Processed content
│   └── database/         # SQLite database
├── models/               # Downloaded AI models
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
- [x] AI model integration
- [x] Basic text summarization

### Week 3-4: UI Development 🚧
- [ ] Streamlit interface
- [ ] File upload system
- [ ] Summary display

### Week 5-6: Interactive Features
- [ ] Q&A chat implementation
- [ ] Context-aware responses
- [ ] NCERT demo preparation

### Month 2: Enhancement & Demo
- [ ] Performance optimization
- [ ] User feedback integration
- [ ] Classmate demonstration

## 🤖 AI Models

### Primary Models
1. **OpenAI GPT-3.5/4**: High-quality summaries and explanations
2. **Hugging Face BERT**: Free text understanding
3. **Sentence-BERT**: Document similarity and search

### Local Models (Offline Support)
- **TinyLlama**: Lightweight local inference
- **DistilBERT**: Fast local processing
- **T5-Small**: Text summarization

## 🛠️ Advanced Features (Future)

### Phase 2 Enhancements
- **Multi-Language Support**: Hindi, regional languages
- **Voice Integration**: Audio Q&A capabilities
- **Visual Learning**: Diagram extraction and explanation
- **Practice Tests**: Auto-generated quizzes from content
- **Progress Tracking**: Learning analytics and insights

### Phase 3 Scaling
- **Collaborative Learning**: Study groups and sharing
- **Teacher Dashboard**: Educator tools and insights
- **Mobile App**: Cross-platform accessibility
- **Cloud Deployment**: Scalable infrastructure

## 📊 Performance Metrics

### Processing Speed
- **PDF Extraction**: ~2-5 seconds per page
- **AI Summarization**: ~10-30 seconds per chapter
- **Q&A Response**: ~2-8 seconds per question

### Accuracy Targets
- **Text Extraction**: >95% accuracy
- **Summary Quality**: Educational expert validation
- **Q&A Relevance**: Context-aware responses

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
- **OpenAI**: For powerful AI capabilities
- **Hugging Face**: For open-source AI models
- **Streamlit**: For rapid UI development

---

**Built with ❤️ for students by students**

*Empowering education through AI - making learning accessible, interactive, and fun!*
