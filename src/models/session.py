from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from bson import ObjectId

class SessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Answer(BaseModel):
    question_index: int = Field(..., description="Index of the question in the quiz")
    user_answer: str = Field(..., description="User's answer")
    is_correct: bool = Field(..., description="Whether the answer is correct")
    answered_at: datetime = Field(default_factory=datetime.utcnow, description="When the answer was submitted")

class QuizSession(BaseModel):
    id: Optional[str] = Field(None, alias="_id", description="Session ID")
    user_id: str = Field(..., description="User ID")
    quiz_id: str = Field(..., description="Quiz ID from quiz-generator")
    book_id: str = Field(..., description="Book ID")
    answers: List[Answer] = Field(default_factory=list, description="User answers")
    score: Optional[float] = Field(None, description="Final score (0-100)")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")
    status: SessionStatus = Field(default=SessionStatus.IN_PROGRESS, description="Session status")
    
    model_config = ConfigDict(populate_by_name=True)

# Request/Response models for API endpoints
class StartSessionRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    quiz_id: str = Field(..., description="Quiz ID")

class StartSessionResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    quiz_id: str = Field(..., description="Quiz ID")
    total_questions: int = Field(..., description="Total number of questions")
    status: SessionStatus = Field(..., description="Session status")
    started_at: datetime = Field(..., description="Session start time")

class SubmitAnswerRequest(BaseModel):
    question_index: int = Field(..., description="Index of the question")
    user_answer: str = Field(..., description="User's answer")

class SubmitAnswerResponse(BaseModel):
    is_correct: bool = Field(..., description="Whether the answer is correct")
    correct_answer: str = Field(..., description="The correct answer")
    explanation: str = Field(..., description="Explanation of the answer")
    current_score: float = Field(..., description="Current score percentage")
    questions_answered: int = Field(..., description="Number of questions answered")
    total_questions: int = Field(..., description="Total number of questions")

class SessionStatusResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    quiz_id: str = Field(..., description="Quiz ID")
    book_id: str = Field(..., description="Book ID")
    status: SessionStatus = Field(..., description="Session status")
    score: Optional[float] = Field(None, description="Current/final score")
    questions_answered: int = Field(..., description="Number of questions answered")
    total_questions: int = Field(..., description="Total number of questions")
    started_at: datetime = Field(..., description="Session start time")
    completed_at: Optional[datetime] = Field(None, description="Session completion time")

class CompleteSessionResponse(BaseModel):
    session_id: str = Field(..., description="Session ID")
    final_score: float = Field(..., description="Final score percentage")
    questions_answered: int = Field(..., description="Number of questions answered")
    total_questions: int = Field(..., description="Total number of questions")
    completed_at: datetime = Field(..., description="Session completion time")
    status: SessionStatus = Field(..., description="Session status")