import sqlite3
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import logging

from ..models.document import Document, ChatMessage

logger = logging.getLogger(__name__)

class DatabaseManager:
    """SQLite database manager for storing documents and chat history"""
    
    def __init__(self, db_path: str = "./data/database/study_assistant.db"):
        self.db_path = db_path
        self._ensure_directory_exists()
        self._initialize_database()
    
    def _ensure_directory_exists(self):
        """Create database directory if it doesn't exist"""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Documents table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        summary TEXT,
                        file_path TEXT,
                        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        grade_level TEXT,
                        subject TEXT,
                        language TEXT DEFAULT 'English',
                        word_count INTEGER,
                        page_count INTEGER
                    )
                """)
                
                # Chat messages table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS chat_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER,
                        content TEXT NOT NULL,
                        role TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confidence_score REAL,
                        FOREIGN KEY (document_id) REFERENCES documents (id)
                    )
                """)
                
                # User sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id TEXT UNIQUE,
                        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        end_time TIMESTAMP,
                        documents_processed INTEGER DEFAULT 0,
                        questions_asked INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def save_document(self, document: Document) -> int:
        """Save document to database and return document ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert summary dict to JSON string
                summary_json = json.dumps(document.summary) if document.summary else None
                
                cursor.execute("""
                    INSERT INTO documents 
                    (title, content, summary, file_path, upload_date, grade_level, 
                     subject, language, word_count, page_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    document.title,
                    document.content,
                    summary_json,
                    document.file_path,
                    document.upload_date,
                    document.grade_level,
                    document.subject,
                    document.language,
                    document.word_count,
                    document.page_count
                ))
                
                doc_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Document saved with ID: {doc_id}")
                return doc_id
                
        except Exception as e:
            logger.error(f"Error saving document: {str(e)}")
            raise
    
    def get_document(self, doc_id: int) -> Optional[Document]:
        """Retrieve document by ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, content, summary, file_path, upload_date,
                           grade_level, subject, language, word_count, page_count
                    FROM documents WHERE id = ?
                """, (doc_id,))
                
                row = cursor.fetchone()
                if row:
                    summary = json.loads(row[3]) if row[3] else {}
                    
                    return Document(
                        id=row[0],
                        title=row[1],
                        content=row[2],
                        summary=summary,
                        file_path=row[4],
                        upload_date=datetime.fromisoformat(row[5]),
                        grade_level=row[6],
                        subject=row[7],
                        language=row[8],
                        word_count=row[9],
                        page_count=row[10]
                    )
                
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving document: {str(e)}")
            return None
    
    def get_recent_documents(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent documents with basic info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, title, upload_date, subject, grade_level, word_count
                    FROM documents 
                    ORDER BY upload_date DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                documents = []
                
                for row in rows:
                    documents.append({
                        'id': row[0],
                        'title': row[1],
                        'upload_date': row[2],
                        'subject': row[3],
                        'grade_level': row[4],
                        'word_count': row[5]
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error retrieving recent documents: {str(e)}")
            return []
    
    def save_chat_message(self, message: ChatMessage) -> int:
        """Save chat message to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO chat_messages 
                    (document_id, content, role, timestamp, confidence_score)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    message.document_id,
                    message.content,
                    message.role,
                    message.timestamp,
                    message.confidence_score
                ))
                
                message_id = cursor.lastrowid
                conn.commit()
                
                return message_id
                
        except Exception as e:
            logger.error(f"Error saving chat message: {str(e)}")
            raise
    
    def get_chat_history(self, document_id: int, limit: int = 50) -> List[ChatMessage]:
        """Get chat history for a document"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT document_id, content, role, timestamp, confidence_score
                    FROM chat_messages 
                    WHERE document_id = ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                """, (document_id, limit))
                
                rows = cursor.fetchall()
                messages = []
                
                for row in rows:
                    messages.append(ChatMessage(
                        document_id=row[0],
                        content=row[1],
                        role=row[2],
                        timestamp=datetime.fromisoformat(row[3]),
                        confidence_score=row[4]
                    ))
                
                return messages
                
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return []
    
    def search_documents(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents by title or content"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Simple text search (can be improved with FTS)
                cursor.execute("""
                    SELECT id, title, upload_date, subject, grade_level
                    FROM documents 
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY upload_date DESC
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                rows = cursor.fetchall()
                documents = []
                
                for row in rows:
                    documents.append({
                        'id': row[0],
                        'title': row[1],
                        'upload_date': row[2],
                        'subject': row[3],
                        'grade_level': row[4]
                    })
                
                return documents
                
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get usage statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Document count
                cursor.execute("SELECT COUNT(*) FROM documents")
                doc_count = cursor.fetchone()[0]
                
                # Message count
                cursor.execute("SELECT COUNT(*) FROM chat_messages")
                message_count = cursor.fetchone()[0]
                
                # Recent activity
                cursor.execute("""
                    SELECT COUNT(*) FROM documents 
                    WHERE upload_date > datetime('now', '-7 days')
                """)
                recent_docs = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT COUNT(*) FROM chat_messages 
                    WHERE timestamp > datetime('now', '-7 days')
                """)
                recent_messages = cursor.fetchone()[0]
                
                return {
                    'total_documents': doc_count,
                    'total_messages': message_count,
                    'documents_this_week': recent_docs,
                    'messages_this_week': recent_messages
                }
                
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old data older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete old chat messages
                cursor.execute("""
                    DELETE FROM chat_messages 
                    WHERE timestamp < datetime('now', '-{} days')
                """.format(days))
                
                # Delete old documents (optional - be careful!)
                # cursor.execute("""
                #     DELETE FROM documents 
                #     WHERE upload_date < datetime('now', '-{} days')
                # """.format(days))
                
                conn.commit()
                logger.info(f"Cleaned up data older than {days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up data: {str(e)}")
            raise
