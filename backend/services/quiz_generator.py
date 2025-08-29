"""
Quiz Generator Service
Generates different types of quizzes from PDF content using AI
"""

import json
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class QuestionType(Enum):
    MULTIPLE_CHOICE = "mcq"
    TRUE_FALSE = "true_false"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"

class DifficultyLevel(Enum):
    KID = "kid"        # 👶 Simple explanations with examples
    TEEN = "teen"      # 🧑 Moderate difficulty
    COLLEGE = "college" # 🎓 Technical depth

@dataclass
class QuizQuestion:
    id: str
    question: str
    question_type: QuestionType
    difficulty: DifficultyLevel
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: str = ""
    explanation: str = ""
    topic: str = ""
    chapter: str = ""

@dataclass
class Quiz:
    id: str
    title: str
    description: str
    questions: List[QuizQuestion]
    difficulty: DifficultyLevel
    total_questions: int
    estimated_time: int  # minutes

class QuizGenerator:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine
        self.question_templates = self._load_question_templates()
    
    def _load_question_templates(self) -> Dict[str, Dict]:
        """Load question generation templates for different types and difficulties"""
        return {
            "mcq": {
                "kid": {
                    "prompt": "Create a simple multiple choice question about {topic} for kids (age 8-12). Use simple words and fun examples. Question should test basic understanding.",
                    "example": "What is water made of?\nA) Only hydrogen\nB) Only oxygen\nC) Hydrogen and oxygen\nD) Carbon and nitrogen"
                },
                "teen": {
                    "prompt": "Create a multiple choice question about {topic} for teenagers (age 13-17). Use moderate difficulty and clear explanations.",
                    "example": "Which process describes how plants make their own food?\nA) Respiration\nB) Photosynthesis\nC) Digestion\nD) Circulation"
                },
                "college": {
                    "prompt": "Create a technical multiple choice question about {topic} for college students. Include scientific terminology and complex concepts.",
                    "example": "In photosynthesis, the light-dependent reactions occur in:\nA) Stroma\nB) Thylakoid membranes\nC) Cytoplasm\nD) Nucleus"
                }
            },
            "true_false": {
                "kid": {
                    "prompt": "Create a simple true/false question about {topic} for kids. Use easy concepts they can understand.",
                    "example": "True or False: Fish breathe air like humans do."
                },
                "teen": {
                    "prompt": "Create a true/false question about {topic} for teenagers with moderate complexity.",
                    "example": "True or False: All chemical reactions release energy."
                },
                "college": {
                    "prompt": "Create a technical true/false question about {topic} for college students.",
                    "example": "True or False: ATP synthase uses chemiosmosis to produce ATP during oxidative phosphorylation."
                }
            },
            "fill_blank": {
                "kid": {
                    "prompt": "Create a fill-in-the-blank question about {topic} for kids using simple words.",
                    "example": "The _____ is the center of our solar system."
                },
                "teen": {
                    "prompt": "Create a fill-in-the-blank question about {topic} for teenagers.",
                    "example": "During _____, plants convert carbon dioxide and water into glucose using sunlight."
                },
                "college": {
                    "prompt": "Create a technical fill-in-the-blank question about {topic} for college students.",
                    "example": "The _____ hypothesis states that mitochondria and chloroplasts evolved from ancient bacteria."
                }
            },
            "short_answer": {
                "kid": {
                    "prompt": "Create a short answer question about {topic} for kids. Keep it simple and fun.",
                    "example": "Why do we need to drink water every day?"
                },
                "teen": {
                    "prompt": "Create a short answer question about {topic} for teenagers requiring 2-3 sentences.",
                    "example": "Explain how the water cycle helps distribute water around Earth."
                },
                "college": {
                    "prompt": "Create a detailed short answer question about {topic} for college students requiring technical explanation.",
                    "example": "Describe the molecular mechanism of enzyme catalysis and factors affecting enzyme activity."
                }
            }
        }
    
    def generate_quiz(self, 
                     content: str, 
                     difficulty: DifficultyLevel,
                     num_questions: int = 5,
                     question_types: List[QuestionType] = None) -> Quiz:
        """
        Generate a quiz from PDF content
        
        Args:
            content: Extracted text from PDF
            difficulty: Target difficulty level
            num_questions: Number of questions to generate
            question_types: Types of questions to include
        
        Returns:
            Quiz object with generated questions
        """
        if question_types is None:
            question_types = [QuestionType.MULTIPLE_CHOICE, QuestionType.TRUE_FALSE]
        
        # Extract key topics from content
        topics = self._extract_topics(content)
        
        questions = []
        for i in range(num_questions):
            # Randomly select question type and topic
            q_type = random.choice(question_types)
            topic = random.choice(topics) if topics else "general content"
            
            # Generate question
            question = self._generate_question(content, topic, q_type, difficulty)
            if question:
                questions.append(question)
        
        # Create quiz
        quiz = Quiz(
            id=f"quiz_{random.randint(1000, 9999)}",
            title=f"Quiz - {difficulty.value.title()} Level",
            description=f"Test your understanding with {len(questions)} questions",
            questions=questions,
            difficulty=difficulty,
            total_questions=len(questions),
            estimated_time=len(questions) * 2  # 2 minutes per question
        )
        
        return quiz
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract key topics from content using AI"""
        prompt = f"""
        Analyze this educational content and extract 5-10 key topics or concepts that could be used for quiz questions.
        Return only the topic names, one per line.
        
        Content: {content[:2000]}...
        """
        
        try:
            response = self.ai_engine.generate_response(prompt)
            topics = [topic.strip() for topic in response.split('\n') if topic.strip()]
            return topics[:10]  # Limit to 10 topics
        except Exception as e:
            print(f"Error extracting topics: {e}")
            return ["general content"]
    
    def _generate_question(self, 
                          content: str, 
                          topic: str, 
                          question_type: QuestionType, 
                          difficulty: DifficultyLevel) -> Optional[QuizQuestion]:
        """Generate a single question"""
        
        template = self.question_templates[question_type.value][difficulty.value]
        
        prompt = f"""
        Based on this educational content, {template['prompt'].format(topic=topic)}
        
        Content: {content[:1500]}...
        
        Return your response in this JSON format:
        {{
            "question": "your question here",
            "options": ["A) option1", "B) option2", "C) option3", "D) option4"],  // only for MCQ
            "correct_answer": "correct answer here",
            "explanation": "why this is correct"
        }}
        
        Example format: {template['example']}
        """
        
        try:
            response = self.ai_engine.generate_response(prompt)
            
            # Try to parse JSON response
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # Fallback: extract manually
                data = self._parse_question_response(response, question_type)
            
            question = QuizQuestion(
                id=f"q_{random.randint(10000, 99999)}",
                question=data.get("question", ""),
                question_type=question_type,
                difficulty=difficulty,
                options=data.get("options") if question_type == QuestionType.MULTIPLE_CHOICE else None,
                correct_answer=data.get("correct_answer", ""),
                explanation=data.get("explanation", ""),
                topic=topic
            )
            
            return question
            
        except Exception as e:
            print(f"Error generating question: {e}")
            return None
    
    def _parse_question_response(self, response: str, question_type: QuestionType) -> Dict:
        """Fallback parser for non-JSON responses"""
        lines = response.strip().split('\n')
        
        result = {
            "question": "",
            "correct_answer": "",
            "explanation": "",
            "options": []
        }
        
        # Simple parsing logic
        for i, line in enumerate(lines):
            if i == 0:  # First line is usually the question
                result["question"] = line.strip()
            elif question_type == QuestionType.MULTIPLE_CHOICE and line.strip().startswith(('A)', 'B)', 'C)', 'D)')):
                result["options"].append(line.strip())
            elif "answer" in line.lower():
                result["correct_answer"] = line.split(":")[-1].strip()
            elif "explanation" in line.lower():
                result["explanation"] = line.split(":")[-1].strip()
        
        return result
    
    def evaluate_answer(self, question: QuizQuestion, user_answer: str) -> Dict[str, Any]:
        """Evaluate user's answer and provide feedback"""
        is_correct = self._check_answer(question, user_answer)
        
        return {
            "correct": is_correct,
            "user_answer": user_answer,
            "correct_answer": question.correct_answer,
            "explanation": question.explanation,
            "score": 1 if is_correct else 0
        }
    
    def _check_answer(self, question: QuizQuestion, user_answer: str) -> bool:
        """Check if user answer is correct"""
        user_answer = user_answer.strip().lower()
        correct_answer = question.correct_answer.strip().lower()
        
        if question.question_type == QuestionType.MULTIPLE_CHOICE:
            # Extract option letter (A, B, C, D)
            if len(user_answer) == 1 and user_answer.isalpha():
                return user_answer == correct_answer.lower()
            # Or match full option text
            return user_answer in correct_answer.lower()
        
        elif question.question_type == QuestionType.TRUE_FALSE:
            user_bool = user_answer in ['true', 't', 'yes', 'y']
            correct_bool = correct_answer.lower() in ['true', 't', 'yes', 'y']
            return user_bool == correct_bool
        
        else:  # Fill blank or short answer
            # Simple keyword matching for now
            return any(word in correct_answer.lower() for word in user_answer.split())

# Example usage
if __name__ == "__main__":
    # This would be used with the actual AI engine
    pass
