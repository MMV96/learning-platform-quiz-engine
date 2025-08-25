from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    BOOLEAN = "boolean"  
    OPEN = "open"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(BaseModel):
    question: str = Field(..., description="Quiz question text")
    type: QuestionType = Field(..., description="Type of question")
    correct_answer: Union[str, bool] = Field(..., description="Correct answer")
    options: Optional[List[str]] = Field(None, description="Options for multiple choice")
    explanation: str = Field(..., description="Detailed explanation")
    difficulty: DifficultyLevel = Field(..., description="Question difficulty")
    topic: str = Field(..., description="Specific topic/subject")
    concepts_tested: List[str] = Field(..., description="Concepts being tested")

class Quiz(BaseModel):
    id: str = Field(..., description="Quiz ID")
    book_id: str = Field(..., description="Reference to source book")
    questions: List[Question] = Field(..., description="List of quiz questions")
    questions_count: int = Field(..., description="Number of questions")
    created_at: datetime = Field(..., description="Creation timestamp")
    ai_model: Optional[str] = Field(None, description="AI model used for generation")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class QuizListItem(BaseModel):
    id: str = Field(..., description="Quiz ID")
    book_id: str = Field(..., description="Reference to source book")
    questions_count: int = Field(..., description="Number of questions")
    created_at: datetime = Field(..., description="Creation timestamp")

class QuizListResponse(BaseModel):
    quizzes: List[QuizListItem] = Field(..., description="List of quizzes")
    total: int = Field(..., description="Total number of quizzes")
    limit: int = Field(..., description="Number of results per page")
    offset: int = Field(..., description="Pagination offset")