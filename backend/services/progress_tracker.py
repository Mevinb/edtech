"""
Progress Tracking Service
Tracks user learning progress, quiz scores, and study analytics
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class StudySession:
    session_id: str
    user_id: str
    document_name: str
    start_time: datetime
    end_time: Optional[datetime]
    pages_studied: int
    questions_asked: int
    difficulty_level: str
    duration_minutes: int

@dataclass
class QuizResult:
    quiz_id: str
    user_id: str
    quiz_title: str
    score: int
    total_questions: int
    correct_answers: int
    difficulty_level: str
    time_taken_minutes: int
    completion_date: datetime
    weak_areas: List[str]

@dataclass
class LearningStats:
    total_study_time: int  # minutes
    documents_studied: int
    quizzes_completed: int
    average_quiz_score: float
    current_streak: int  # days
    longest_streak: int
    favorite_subjects: List[str]
    improvement_areas: List[str]
    last_activity: datetime

@dataclass
class Achievement:
    id: str
    title: str
    description: str
    icon: str
    unlocked_date: Optional[datetime]
    progress: int  # 0-100%
    target_value: int
    current_value: int

class ProgressTracker:
    def __init__(self, db_path: str = "data/database/progress.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self.achievements = self._load_achievements()
    
    def _init_database(self):
        """Initialize the progress tracking database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT,
                    created_date TEXT,
                    preferred_difficulty TEXT DEFAULT 'teen',
                    settings TEXT  -- JSON string for user preferences
                )
            """)
            
            # Study sessions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS study_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    document_name TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    pages_studied INTEGER DEFAULT 0,
                    questions_asked INTEGER DEFAULT 0,
                    difficulty_level TEXT,
                    duration_minutes INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Quiz results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS quiz_results (
                    quiz_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    quiz_title TEXT,
                    score INTEGER,
                    total_questions INTEGER,
                    correct_answers INTEGER,
                    difficulty_level TEXT,
                    time_taken_minutes INTEGER,
                    completion_date TEXT,
                    weak_areas TEXT,  -- JSON string
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Achievements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_achievements (
                    user_id TEXT,
                    achievement_id TEXT,
                    unlocked_date TEXT,
                    progress INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, achievement_id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Daily activity tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_activity (
                    user_id TEXT,
                    date TEXT,
                    study_minutes INTEGER DEFAULT 0,
                    quizzes_completed INTEGER DEFAULT 0,
                    questions_answered INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, date),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            conn.commit()
    
    def create_user(self, user_id: str, username: str = "Student", difficulty: str = "teen") -> bool:
        """Create a new user profile"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (user_id, username, created_date, preferred_difficulty, settings)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    username, 
                    datetime.now().isoformat(),
                    difficulty,
                    json.dumps({"notifications": True, "auto_difficulty": False})
                ))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def start_study_session(self, user_id: str, document_name: str, difficulty: str = "teen") -> str:
        """Start a new study session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}"
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO study_sessions 
                    (session_id, user_id, document_name, start_time, difficulty_level)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    session_id,
                    user_id,
                    document_name,
                    datetime.now().isoformat(),
                    difficulty
                ))
                conn.commit()
                return session_id
        except Exception as e:
            print(f"Error starting study session: {e}")
            return ""
    
    def end_study_session(self, session_id: str, pages_studied: int = 0, questions_asked: int = 0):
        """End a study session and calculate duration"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get session start time
                cursor.execute("SELECT start_time FROM study_sessions WHERE session_id = ?", (session_id,))
                result = cursor.fetchone()
                
                if result:
                    start_time = datetime.fromisoformat(result[0])
                    end_time = datetime.now()
                    duration = int((end_time - start_time).total_seconds() / 60)  # minutes
                    
                    cursor.execute("""
                        UPDATE study_sessions 
                        SET end_time = ?, pages_studied = ?, questions_asked = ?, duration_minutes = ?
                        WHERE session_id = ?
                    """, (
                        end_time.isoformat(),
                        pages_studied,
                        questions_asked,
                        duration,
                        session_id
                    ))
                    
                    # Update daily activity
                    self._update_daily_activity(session_id.split('_')[-1], end_time.date(), study_minutes=duration)
                    
                    conn.commit()
        except Exception as e:
            print(f"Error ending study session: {e}")
    
    def record_quiz_result(self, quiz_result: QuizResult):
        """Record quiz completion and results"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO quiz_results
                    (quiz_id, user_id, quiz_title, score, total_questions, correct_answers,
                     difficulty_level, time_taken_minutes, completion_date, weak_areas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    quiz_result.quiz_id,
                    quiz_result.user_id,
                    quiz_result.quiz_title,
                    quiz_result.score,
                    quiz_result.total_questions,
                    quiz_result.correct_answers,
                    quiz_result.difficulty_level,
                    quiz_result.time_taken_minutes,
                    quiz_result.completion_date.isoformat(),
                    json.dumps(quiz_result.weak_areas)
                ))
                
                # Update daily activity
                self._update_daily_activity(
                    quiz_result.user_id, 
                    quiz_result.completion_date.date(),
                    quizzes_completed=1,
                    questions_answered=quiz_result.total_questions
                )
                
                # Check for achievements
                self._check_achievements(quiz_result.user_id)
                
                conn.commit()
        except Exception as e:
            print(f"Error recording quiz result: {e}")
    
    def get_user_stats(self, user_id: str) -> LearningStats:
        """Get comprehensive learning statistics for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Total study time
                cursor.execute("""
                    SELECT SUM(duration_minutes) FROM study_sessions 
                    WHERE user_id = ? AND end_time IS NOT NULL
                """, (user_id,))
                total_study_time = cursor.fetchone()[0] or 0
                
                # Documents studied
                cursor.execute("""
                    SELECT COUNT(DISTINCT document_name) FROM study_sessions 
                    WHERE user_id = ? AND end_time IS NOT NULL
                """, (user_id,))
                documents_studied = cursor.fetchone()[0] or 0
                
                # Quiz stats
                cursor.execute("""
                    SELECT COUNT(*), AVG(score) FROM quiz_results WHERE user_id = ?
                """, (user_id,))
                quiz_stats = cursor.fetchone()
                quizzes_completed = quiz_stats[0] or 0
                average_quiz_score = quiz_stats[1] or 0.0
                
                # Streak calculation
                current_streak, longest_streak = self._calculate_streaks(user_id)
                
                # Last activity
                cursor.execute("""
                    SELECT MAX(date) FROM daily_activity WHERE user_id = ?
                """, (user_id,))
                last_activity_str = cursor.fetchone()[0]
                last_activity = datetime.fromisoformat(last_activity_str) if last_activity_str else datetime.now()
                
                return LearningStats(
                    total_study_time=total_study_time,
                    documents_studied=documents_studied,
                    quizzes_completed=quizzes_completed,
                    average_quiz_score=round(average_quiz_score, 1),
                    current_streak=current_streak,
                    longest_streak=longest_streak,
                    favorite_subjects=self._get_favorite_subjects(user_id),
                    improvement_areas=self._get_improvement_areas(user_id),
                    last_activity=last_activity
                )
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return LearningStats(0, 0, 0, 0.0, 0, 0, [], [], datetime.now())
    
    def _update_daily_activity(self, user_id: str, date, study_minutes: int = 0, 
                              quizzes_completed: int = 0, questions_answered: int = 0):
        """Update daily activity stats"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO daily_activity 
                    (user_id, date, study_minutes, quizzes_completed, questions_answered)
                    VALUES (?, ?, 0, 0, 0)
                """, (user_id, date_str))
                
                cursor.execute("""
                    UPDATE daily_activity 
                    SET study_minutes = study_minutes + ?,
                        quizzes_completed = quizzes_completed + ?,
                        questions_answered = questions_answered + ?
                    WHERE user_id = ? AND date = ?
                """, (study_minutes, quizzes_completed, questions_answered, user_id, date_str))
                
                conn.commit()
        except Exception as e:
            print(f"Error updating daily activity: {e}")
    
    def _calculate_streaks(self, user_id: str) -> tuple[int, int]:
        """Calculate current and longest study streaks"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date FROM daily_activity 
                    WHERE user_id = ? AND (study_minutes > 0 OR quizzes_completed > 0)
                    ORDER BY date DESC
                """, (user_id,))
                
                activity_dates = [datetime.fromisoformat(row[0]).date() for row in cursor.fetchall()]
                
                if not activity_dates:
                    return 0, 0
                
                # Calculate current streak
                current_streak = 0
                today = datetime.now().date()
                
                for i, date in enumerate(activity_dates):
                    expected_date = today - timedelta(days=i)
                    if date == expected_date:
                        current_streak += 1
                    else:
                        break
                
                # Calculate longest streak
                longest_streak = 0
                current_run = 1
                
                for i in range(1, len(activity_dates)):
                    if activity_dates[i-1] - activity_dates[i] == timedelta(days=1):
                        current_run += 1
                    else:
                        longest_streak = max(longest_streak, current_run)
                        current_run = 1
                
                longest_streak = max(longest_streak, current_run)
                
                return current_streak, longest_streak
                
        except Exception as e:
            print(f"Error calculating streaks: {e}")
            return 0, 0
    
    def _get_favorite_subjects(self, user_id: str) -> List[str]:
        """Get user's most studied subjects"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT document_name, COUNT(*) as frequency
                    FROM study_sessions 
                    WHERE user_id = ? AND end_time IS NOT NULL
                    GROUP BY document_name
                    ORDER BY frequency DESC
                    LIMIT 3
                """, (user_id,))
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting favorite subjects: {e}")
            return []
    
    def _get_improvement_areas(self, user_id: str) -> List[str]:
        """Get areas where user needs improvement based on quiz performance"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT weak_areas FROM quiz_results 
                    WHERE user_id = ? AND score < 70
                    ORDER BY completion_date DESC
                    LIMIT 5
                """, (user_id,))
                
                all_weak_areas = []
                for row in cursor.fetchall():
                    if row[0]:
                        weak_areas = json.loads(row[0])
                        all_weak_areas.extend(weak_areas)
                
                # Count frequency and return most common
                from collections import Counter
                if all_weak_areas:
                    area_counts = Counter(all_weak_areas)
                    return [area for area, count in area_counts.most_common(3)]
                
                return []
        except Exception as e:
            print(f"Error getting improvement areas: {e}")
            return []
    
    def _load_achievements(self) -> List[Achievement]:
        """Load achievement definitions"""
        return [
            Achievement("first_quiz", "Quiz Rookie", "Complete your first quiz", "🎯", None, 0, 1, 0),
            Achievement("quiz_master", "Quiz Master", "Complete 10 quizzes", "🏆", None, 0, 10, 0),
            Achievement("perfect_score", "Perfect Score", "Get 100% on a quiz", "⭐", None, 0, 1, 0),
            Achievement("study_streak_7", "Week Warrior", "Study for 7 days in a row", "🔥", None, 0, 7, 0),
            Achievement("study_streak_30", "Month Master", "Study for 30 days in a row", "📅", None, 0, 30, 0),
            Achievement("time_scholar", "Time Scholar", "Study for 10 hours total", "⏰", None, 0, 600, 0), # 600 minutes
            Achievement("improvement", "Getting Better", "Improve quiz score by 20%", "📈", None, 0, 1, 0),
        ]
    
    def _check_achievements(self, user_id: str):
        """Check and unlock achievements for user"""
        stats = self.get_user_stats(user_id)
        
        achievement_checks = {
            "first_quiz": stats.quizzes_completed >= 1,
            "quiz_master": stats.quizzes_completed >= 10,
            "study_streak_7": stats.current_streak >= 7,
            "study_streak_30": stats.current_streak >= 30,
            "time_scholar": stats.total_study_time >= 600,
        }
        
        # Check for perfect scores
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM quiz_results 
                    WHERE user_id = ? AND score = 100
                """, (user_id,))
                perfect_scores = cursor.fetchone()[0]
                achievement_checks["perfect_score"] = perfect_scores >= 1
        except:
            achievement_checks["perfect_score"] = False
        
        # Update achievements in database
        for achievement_id, unlocked in achievement_checks.items():
            if unlocked:
                self._unlock_achievement(user_id, achievement_id)
    
    def _unlock_achievement(self, user_id: str, achievement_id: str):
        """Unlock an achievement for user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR IGNORE INTO user_achievements 
                    (user_id, achievement_id, unlocked_date, progress)
                    VALUES (?, ?, ?, 100)
                """, (user_id, achievement_id, datetime.now().isoformat()))
                conn.commit()
        except Exception as e:
            print(f"Error unlocking achievement: {e}")
    
    def get_user_achievements(self, user_id: str) -> List[Achievement]:
        """Get all achievements for user with unlock status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT achievement_id, unlocked_date FROM user_achievements 
                    WHERE user_id = ?
                """, (user_id,))
                
                unlocked = {row[0]: datetime.fromisoformat(row[1]) for row in cursor.fetchall()}
                
                # Update achievement list with unlock status
                user_achievements = []
                for achievement in self.achievements:
                    if achievement.id in unlocked:
                        achievement.unlocked_date = unlocked[achievement.id]
                        achievement.progress = 100
                    user_achievements.append(achievement)
                
                return user_achievements
        except Exception as e:
            print(f"Error getting user achievements: {e}")
            return self.achievements

# Example usage
if __name__ == "__main__":
    tracker = ProgressTracker()
    
    # Example user creation and session
    user_id = "student_123"
    tracker.create_user(user_id, "Alice")
    
    session_id = tracker.start_study_session(user_id, "NCERT Physics Chapter 1")
    # ... study session happens ...
    tracker.end_study_session(session_id, pages_studied=5, questions_asked=3)
    
    # Get stats
    stats = tracker.get_user_stats(user_id)
    print(f"Study time: {stats.total_study_time} minutes")
    print(f"Current streak: {stats.current_streak} days")
