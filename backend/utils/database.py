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
                
                # Gamification stats table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_gamification_stats (
                        user_id TEXT PRIMARY KEY,
                        total_xp INTEGER DEFAULT 0,
                        current_level TEXT DEFAULT 'beginner',
                        badges_earned TEXT DEFAULT '[]',
                        current_streak INTEGER DEFAULT 0,
                        longest_streak INTEGER DEFAULT 0,
                        total_study_time INTEGER DEFAULT 0,
                        quizzes_completed INTEGER DEFAULT 0,
                        perfect_scores INTEGER DEFAULT 0,
                        questions_asked INTEGER DEFAULT 0,
                        voice_interactions INTEGER DEFAULT 0,
                        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Achievements table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS achievements (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        achievement_id TEXT UNIQUE NOT NULL,
                        user_id TEXT NOT NULL,
                        badge_type TEXT NOT NULL,
                        earned_date TIMESTAMP NOT NULL,
                        xp_earned INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Daily challenges table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS daily_challenges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        challenge_id TEXT NOT NULL,
                        challenge_date DATE NOT NULL,
                        target_value INTEGER NOT NULL,
                        current_progress INTEGER DEFAULT 0,
                        completed BOOLEAN DEFAULT FALSE,
                        xp_reward INTEGER NOT NULL,
                        completed_at TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, challenge_id, challenge_date)
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
    
    # Gamification Database Methods
    
    def get_user_gamification_stats(self, user_id: str) -> Optional[Dict]:
        """Get user's gamification statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM user_gamification_stats WHERE user_id = ?
                """, (user_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                columns = [col[0] for col in cursor.description]
                stats = dict(zip(columns, row))
                
                # Parse JSON fields
                stats['badges_earned'] = json.loads(stats['badges_earned'])
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting gamification stats: {str(e)}")
            return None
    
    def save_user_gamification_stats(self, user_id: str, stats: Dict):
        """Save or update user's gamification statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert badges to JSON
                badges_json = json.dumps(stats['badges_earned'])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO user_gamification_stats 
                    (user_id, total_xp, current_level, badges_earned, current_streak, 
                     longest_streak, total_study_time, quizzes_completed, perfect_scores,
                     questions_asked, voice_interactions, last_activity, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id,
                    stats['total_xp'],
                    stats['current_level'],
                    badges_json,
                    stats['current_streak'],
                    stats['longest_streak'],
                    stats['total_study_time'],
                    stats['quizzes_completed'],
                    stats['perfect_scores'],
                    stats.get('questions_asked', 0),
                    stats.get('voice_interactions', 0),
                    stats['last_activity'],
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                logger.info(f"Gamification stats saved for user: {user_id}")
                
        except Exception as e:
            logger.error(f"Error saving gamification stats: {str(e)}")
            raise
    
    def save_achievement(self, achievement: Dict):
        """Save a new achievement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR IGNORE INTO achievements 
                    (achievement_id, user_id, badge_type, earned_date, xp_earned)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    achievement['achievement_id'],
                    achievement['user_id'],
                    achievement['badge_type'],
                    achievement['earned_date'],
                    achievement['xp_earned']
                ))
                
                conn.commit()
                logger.info(f"Achievement saved: {achievement['badge_type']}")
                
        except Exception as e:
            logger.error(f"Error saving achievement: {str(e)}")
            raise
    
    def get_user_achievements(self, user_id: str) -> List[Dict]:
        """Get all achievements for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM achievements 
                    WHERE user_id = ? 
                    ORDER BY earned_date DESC
                """, (user_id,))
                
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                
                achievements = []
                for row in rows:
                    achievement = dict(zip(columns, row))
                    achievements.append(achievement)
                
                return achievements
                
        except Exception as e:
            logger.error(f"Error getting achievements: {str(e)}")
            return []
    
    def increment_user_activity(self, user_id: str, activity_type: str, increment: int = 1):
        """Increment activity counters for gamification"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current stats or create new record
                cursor.execute("""
                    INSERT OR IGNORE INTO user_gamification_stats (user_id) VALUES (?)
                """, (user_id,))
                
                # Update the specific activity counter
                if activity_type == 'questions_asked':
                    cursor.execute("""
                        UPDATE user_gamification_stats 
                        SET questions_asked = questions_asked + ?, updated_at = ?
                        WHERE user_id = ?
                    """, (increment, datetime.now().isoformat(), user_id))
                
                elif activity_type == 'voice_interactions':
                    cursor.execute("""
                        UPDATE user_gamification_stats 
                        SET voice_interactions = voice_interactions + ?, updated_at = ?
                        WHERE user_id = ?
                    """, (increment, datetime.now().isoformat(), user_id))
                
                elif activity_type == 'quizzes_completed':
                    cursor.execute("""
                        UPDATE user_gamification_stats 
                        SET quizzes_completed = quizzes_completed + ?, updated_at = ?
                        WHERE user_id = ?
                    """, (increment, datetime.now().isoformat(), user_id))
                
                elif activity_type == 'study_time':
                    cursor.execute("""
                        UPDATE user_gamification_stats 
                        SET total_study_time = total_study_time + ?, updated_at = ?
                        WHERE user_id = ?
                    """, (increment, datetime.now().isoformat(), user_id))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error incrementing activity: {str(e)}")
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users by XP for leaderboard"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT user_id, total_xp, current_level, current_streak 
                    FROM user_gamification_stats 
                    ORDER BY total_xp DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                columns = [col[0] for col in cursor.description]
                
                leaderboard = []
                for i, row in enumerate(rows, 1):
                    entry = dict(zip(columns, row))
                    entry['rank'] = i
                    # Anonymize user IDs for privacy
                    entry['username'] = f"User_{entry['user_id'][-4:]}"
                    leaderboard.append(entry)
                
                return leaderboard
                
        except Exception as e:
            logger.error(f"Error getting leaderboard: {str(e)}")
            return []
