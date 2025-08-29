from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class Document:
    """Document model for storing PDF content and metadata"""
    title: str
    content: str
    summary: Dict[str, Any]
    file_path: str
    upload_date: datetime
    id: Optional[int] = None
    grade_level: Optional[str] = None
    subject: Optional[str] = None
    language: Optional[str] = "English"
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    
    def __post_init__(self):
        if self.word_count is None:
            self.word_count = len(self.content.split())

@dataclass
class ChatMessage:
    """Chat message model for Q&A interactions"""
    content: str
    role: str  # 'user' or 'assistant'
    timestamp: datetime
    document_id: Optional[int] = None
    confidence_score: Optional[float] = None
    
@dataclass
class ProcessingResult:
    """Result of document processing"""
    success: bool
    document: Optional[Document] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
