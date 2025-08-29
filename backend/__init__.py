# Backend package initialization
from .services.pdf_processor import PDFProcessor
from .services.ai_engine import AIEngine
from .utils.database import DatabaseManager
from .models.document import Document, ChatMessage, ProcessingResult

__all__ = [
    'PDFProcessor',
    'AIEngine', 
    'DatabaseManager',
    'Document',
    'ChatMessage',
    'ProcessingResult'
]
