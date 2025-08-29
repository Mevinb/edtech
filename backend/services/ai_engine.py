import os
from typing import Optional, Dict, Any, List
import logging
from datetime import datetime
import json

# AI/ML imports (will handle import errors gracefully)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available. Install with: pip install openai")

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. Install with: pip install transformers sentence-transformers")

logger = logging.getLogger(__name__)

class AIEngine:
    """AI Engine supporting multiple models for text processing"""
    
    def __init__(self):
        self.openai_client = None
        self.local_summarizer = None
        self.local_qa_model = None
        self.embedding_model = None
        
        # Initialize available models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize available AI models"""
        # Initialize OpenAI if API key is available
        if OPENAI_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    openai.api_key = api_key
                    self.openai_client = openai
                    logger.info("OpenAI API initialized successfully")
                except Exception as e:
                    logger.error(f"Error initializing OpenAI: {str(e)}")
        
        # Initialize local models if transformers is available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Load lightweight models for local processing
                self.local_summarizer = pipeline(
                    "summarization",
                    model="facebook/bart-large-cnn",
                    device=-1  # CPU
                )
                
                self.local_qa_model = pipeline(
                    "question-answering",
                    model="distilbert-base-cased-distilled-squad",
                    device=-1  # CPU
                )
                
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("Local AI models initialized successfully")
                
            except Exception as e:
                logger.error(f"Error initializing local models: {str(e)}")
    
    def generate_summary(self, text: str, max_length: int = 500) -> Dict[str, Any]:
        """
        Generate comprehensive summary of the text
        """
        try:
            # Try OpenAI first if available
            if self.openai_client:
                return self._generate_openai_summary(text, max_length)
            
            # Fall back to local models
            elif self.local_summarizer:
                return self._generate_local_summary(text, max_length)
            
            # Fallback to rule-based summary
            else:
                return self._generate_simple_summary(text, max_length)
                
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return self._generate_simple_summary(text, max_length)
    
    def _generate_openai_summary(self, text: str, max_length: int) -> Dict[str, Any]:
        """Generate summary using OpenAI API"""
        try:
            # Chunk text if too long
            chunks = self._chunk_text(text, 3000)
            
            summaries = []
            key_points = []
            
            for chunk in chunks:
                response = self.openai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are an AI tutor specializing in explaining educational content to students. 
                            Create a comprehensive summary that includes:
                            1. A brief overview of the main topic
                            2. Key points in bullet format
                            3. Important concepts that students should remember
                            
                            Make your explanations clear and appropriate for the grade level mentioned in the content."""
                        },
                        {
                            "role": "user",
                            "content": f"Please summarize this educational content:\n\n{chunk}"
                        }
                    ],
                    max_tokens=max_length,
                    temperature=0.7
                )
                
                content = response.choices[0].message.content
                summaries.append(content)
                
                # Extract key points
                key_points_response = self.openai_client.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Extract the most important points from this educational content as a numbered list. Focus on key concepts, definitions, and facts that students need to remember."
                        },
                        {
                            "role": "user",
                            "content": chunk
                        }
                    ],
                    max_tokens=200,
                    temperature=0.5
                )
                
                points = key_points_response.choices[0].message.content
                key_points.extend(self._parse_key_points(points))
            
            return {
                'overview': ' '.join(summaries),
                'key_points': key_points[:10],  # Limit to top 10 points
                'word_count': len(text.split()),
                'summary_length': len(' '.join(summaries).split()),
                'generated_by': 'OpenAI GPT'
            }
            
        except Exception as e:
            logger.error(f"OpenAI summary generation failed: {str(e)}")
            raise
    
    def _generate_local_summary(self, text: str, max_length: int) -> Dict[str, Any]:
        """Generate summary using local transformer models"""
        try:
            # Chunk text for processing
            chunks = self._chunk_text(text, 1000)
            summaries = []
            
            for chunk in chunks:
                if len(chunk.split()) > 50:  # Only summarize substantial chunks
                    summary = self.local_summarizer(
                        chunk,
                        max_length=min(max_length // len(chunks), 150),
                        min_length=30,
                        do_sample=False
                    )
                    summaries.append(summary[0]['summary_text'])
            
            # Extract key points using simple NLP
            key_points = self._extract_key_sentences(text, top_k=8)
            
            return {
                'overview': ' '.join(summaries),
                'key_points': key_points,
                'word_count': len(text.split()),
                'summary_length': len(' '.join(summaries).split()),
                'generated_by': 'Local Transformer'
            }
            
        except Exception as e:
            logger.error(f"Local summary generation failed: {str(e)}")
            raise
    
    def _generate_simple_summary(self, text: str, max_length: int) -> Dict[str, Any]:
        """Generate basic summary using rule-based approach"""
        sentences = text.split('.')
        
        # Take first few sentences and some from middle and end
        num_sentences = min(len(sentences), max_length // 20)
        selected_sentences = []
        
        if len(sentences) > 3:
            selected_sentences.extend(sentences[:2])  # First 2
            selected_sentences.extend(sentences[len(sentences)//2:len(sentences)//2+2])  # Middle 2
            selected_sentences.extend(sentences[-2:])  # Last 2
        else:
            selected_sentences = sentences
        
        overview = '. '.join(s.strip() for s in selected_sentences if s.strip())
        
        # Extract key points (sentences with important keywords)
        key_points = self._extract_key_sentences(text, top_k=6)
        
        return {
            'overview': overview,
            'key_points': key_points,
            'word_count': len(text.split()),
            'summary_length': len(overview.split()),
            'generated_by': 'Rule-based'
        }
    
    def answer_question(self, question: str, context: str) -> str:
        """
        Answer question based on provided context
        """
        try:
            # Try OpenAI first
            if self.openai_client:
                return self._answer_with_openai(question, context)
            
            # Fall back to local QA model
            elif self.local_qa_model:
                return self._answer_with_local_model(question, context)
            
            # Simple fallback
            else:
                return self._answer_with_simple_search(question, context)
                
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return "I'm sorry, I encountered an error while processing your question. Please try rephrasing it or check if the document contains relevant information."
    
    def _answer_with_openai(self, question: str, context: str) -> str:
        """Answer question using OpenAI"""
        try:
            # Limit context length
            context_chunks = self._chunk_text(context, 2000)
            relevant_context = context_chunks[0]  # Use first chunk for now
            
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful AI tutor. Answer the student's question based on the provided educational content. 
                        Make your explanation clear, accurate, and appropriate for the student's level. 
                        If the answer isn't in the provided content, politely say so and offer to help with related topics that are covered."""
                    },
                    {
                        "role": "user",
                        "content": f"Context: {relevant_context}\n\nQuestion: {question}"
                    }
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI QA failed: {str(e)}")
            raise
    
    def _answer_with_local_model(self, question: str, context: str) -> str:
        """Answer question using local QA model"""
        try:
            # Limit context length for local model
            if len(context) > 2000:
                context = context[:2000]
            
            result = self.local_qa_model(
                question=question,
                context=context
            )
            
            confidence = result['score']
            answer = result['answer']
            
            if confidence > 0.3:
                return f"{answer}\n\n(Confidence: {confidence:.1%})"
            else:
                return "I couldn't find a confident answer to your question in the provided text. Could you try rephrasing your question or asking about a different topic covered in the document?"
                
        except Exception as e:
            logger.error(f"Local QA failed: {str(e)}")
            raise
    
    def _answer_with_simple_search(self, question: str, context: str) -> str:
        """Simple keyword-based answer extraction"""
        question_words = question.lower().split()
        sentences = context.split('.')
        
        # Find sentences containing question keywords
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            matches = sum(1 for word in question_words if word in sentence_lower)
            if matches >= 2:  # At least 2 keyword matches
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            return '. '.join(relevant_sentences[:3])  # Return top 3 relevant sentences
        else:
            return "I couldn't find specific information about your question in the provided text. Please try asking about topics that are covered in the document."
    
    def _chunk_text(self, text: str, max_length: int) -> List[str]:
        """Split text into chunks of specified maximum length"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) > max_length and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1  # +1 for space
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _extract_key_sentences(self, text: str, top_k: int = 8) -> List[str]:
        """Extract key sentences using simple heuristics"""
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        # Score sentences based on:
        # - Length (not too short, not too long)
        # - Position (first few sentences are often important)
        # - Keywords (educational terms)
        
        educational_keywords = [
            'definition', 'important', 'key', 'main', 'concept', 'principle',
            'example', 'formula', 'equation', 'theory', 'law', 'rule',
            'process', 'method', 'step', 'characteristic', 'property'
        ]
        
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0
            words = sentence.lower().split()
            
            # Length score
            if 5 <= len(words) <= 25:
                score += 1
            
            # Position score (first sentences often important)
            if i < 3:
                score += 1
            
            # Keyword score
            keyword_count = sum(1 for keyword in educational_keywords if keyword in sentence.lower())
            score += keyword_count * 0.5
            
            scored_sentences.append((score, sentence))
        
        # Sort by score and return top sentences
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        return [sentence for score, sentence in scored_sentences[:top_k]]
    
    def _parse_key_points(self, points_text: str) -> List[str]:
        """Parse numbered list of key points"""
        lines = points_text.split('\n')
        points = []
        
        for line in lines:
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith('•') or line.startswith('-')):
                # Remove numbering and bullet points
                clean_point = line.lstrip('0123456789.•- ').strip()
                if clean_point:
                    points.append(clean_point)
        
        return points
