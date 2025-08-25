import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.session import (
    SessionStatus, Answer, QuizSession, StartSessionRequest, StartSessionResponse,
    SubmitAnswerRequest, SubmitAnswerResponse, SessionStatusResponse, CompleteSessionResponse
)


class TestSessionModels:
    def test_session_status_enum(self):
        assert SessionStatus.IN_PROGRESS == "in_progress"
        assert SessionStatus.COMPLETED == "completed"
        assert SessionStatus.ABANDONED == "abandoned"

    def test_answer_creation(self):
        answer_data = {
            "question_index": 0,
            "user_answer": "Rome",
            "is_correct": True
        }
        
        answer = Answer(**answer_data)
        
        assert answer.question_index == 0
        assert answer.user_answer == "Rome"
        assert answer.is_correct is True
        assert isinstance(answer.answered_at, datetime)

    def test_answer_creation_with_timestamp(self):
        timestamp = datetime.utcnow()
        answer_data = {
            "question_index": 1,
            "user_answer": "Milan",
            "is_correct": False,
            "answered_at": timestamp
        }
        
        answer = Answer(**answer_data)
        
        assert answer.question_index == 1
        assert answer.user_answer == "Milan"
        assert answer.is_correct is False
        assert answer.answered_at == timestamp

    def test_answer_missing_required_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            Answer(
                question_index=0
                # Missing user_answer and is_correct
            )
        
        errors = exc_info.value.errors()
        required_fields = {"user_answer", "is_correct"}
        error_fields = {error["loc"][0] for error in errors}
        
        assert required_fields.issubset(error_fields)

    def test_quiz_session_creation(self):
        session_data = {
            "user_id": "user-123",
            "quiz_id": "quiz-456",
            "book_id": "book-789"
        }
        
        session = QuizSession(**session_data)
        
        assert session.user_id == "user-123"
        assert session.quiz_id == "quiz-456"
        assert session.book_id == "book-789"
        assert session.answers == []
        assert session.score is None
        assert isinstance(session.started_at, datetime)
        assert session.completed_at is None
        assert session.status == SessionStatus.IN_PROGRESS

    def test_quiz_session_with_answers(self):
        answer = Answer(
            question_index=0,
            user_answer="Rome",
            is_correct=True
        )
        
        session_data = {
            "user_id": "user-123",
            "quiz_id": "quiz-456",
            "book_id": "book-789",
            "answers": [answer],
            "score": 100.0,
            "status": SessionStatus.COMPLETED,
            "completed_at": datetime.utcnow()
        }
        
        session = QuizSession(**session_data)
        
        assert len(session.answers) == 1
        assert session.answers[0].user_answer == "Rome"
        assert session.score == 100.0
        assert session.status == SessionStatus.COMPLETED
        assert session.completed_at is not None

    def test_quiz_session_with_id(self):
        session_data = {
            "_id": "507f1f77bcf86cd799439011",
            "user_id": "user-123",
            "quiz_id": "quiz-456",
            "book_id": "book-789"
        }
        
        session = QuizSession(**session_data)
        
        assert session.id == "507f1f77bcf86cd799439011"
        assert session.user_id == "user-123"

    def test_start_session_request(self):
        request_data = {
            "user_id": "user-123",
            "quiz_id": "quiz-456"
        }
        
        request = StartSessionRequest(**request_data)
        
        assert request.user_id == "user-123"
        assert request.quiz_id == "quiz-456"

    def test_start_session_request_missing_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            StartSessionRequest(
                user_id="user-123"
                # Missing quiz_id
            )
        
        errors = exc_info.value.errors()
        assert "quiz_id" in [error["loc"][0] for error in errors]

    def test_start_session_response(self):
        timestamp = datetime.utcnow()
        response_data = {
            "session_id": "session-123",
            "quiz_id": "quiz-456",
            "total_questions": 10,
            "status": SessionStatus.IN_PROGRESS,
            "started_at": timestamp
        }
        
        response = StartSessionResponse(**response_data)
        
        assert response.session_id == "session-123"
        assert response.quiz_id == "quiz-456"
        assert response.total_questions == 10
        assert response.status == SessionStatus.IN_PROGRESS
        assert response.started_at == timestamp

    def test_submit_answer_request(self):
        request_data = {
            "question_index": 0,
            "user_answer": "Rome"
        }
        
        request = SubmitAnswerRequest(**request_data)
        
        assert request.question_index == 0
        assert request.user_answer == "Rome"

    def test_submit_answer_response(self):
        response_data = {
            "is_correct": True,
            "correct_answer": "Rome",
            "explanation": "Rome is the capital of Italy.",
            "current_score": 100.0,
            "questions_answered": 1,
            "total_questions": 1
        }
        
        response = SubmitAnswerResponse(**response_data)
        
        assert response.is_correct is True
        assert response.correct_answer == "Rome"
        assert response.explanation == "Rome is the capital of Italy."
        assert response.current_score == 100.0
        assert response.questions_answered == 1
        assert response.total_questions == 1

    def test_session_status_response(self):
        timestamp = datetime.utcnow()
        response_data = {
            "session_id": "session-123",
            "quiz_id": "quiz-456",
            "book_id": "book-789",
            "status": SessionStatus.IN_PROGRESS,
            "score": 50.0,
            "questions_answered": 1,
            "total_questions": 2,
            "started_at": timestamp
        }
        
        response = SessionStatusResponse(**response_data)
        
        assert response.session_id == "session-123"
        assert response.quiz_id == "quiz-456"
        assert response.book_id == "book-789"
        assert response.status == SessionStatus.IN_PROGRESS
        assert response.score == 50.0
        assert response.questions_answered == 1
        assert response.total_questions == 2
        assert response.started_at == timestamp
        assert response.completed_at is None

    def test_complete_session_response(self):
        timestamp = datetime.utcnow()
        response_data = {
            "session_id": "session-123",
            "final_score": 80.0,
            "questions_answered": 4,
            "total_questions": 5,
            "completed_at": timestamp,
            "status": SessionStatus.COMPLETED
        }
        
        response = CompleteSessionResponse(**response_data)
        
        assert response.session_id == "session-123"
        assert response.final_score == 80.0
        assert response.questions_answered == 4
        assert response.total_questions == 5
        assert response.completed_at == timestamp
        assert response.status == SessionStatus.COMPLETED

    def test_quiz_session_invalid_status(self):
        with pytest.raises(ValidationError):
            QuizSession(
                user_id="user-123",
                quiz_id="quiz-456",
                book_id="book-789",
                status="invalid_status"  # Invalid enum value
            )

    def test_answer_negative_question_index(self):
        # The model doesn't validate negative indices, but we can test it's allowed
        answer_data = {
            "question_index": -1,
            "user_answer": "Rome",
            "is_correct": True
        }
        
        answer = Answer(**answer_data)
        assert answer.question_index == -1

    def test_quiz_session_empty_strings(self):
        # Empty strings are actually allowed in this model, so let's test that they work
        session = QuizSession(
            user_id="",  # Empty string should be allowed
            quiz_id="quiz-456",
            book_id="book-789"
        )
        assert session.user_id == ""

    def test_submit_answer_request_empty_answer(self):
        # Empty user_answer should be allowed
        request_data = {
            "question_index": 0,
            "user_answer": ""
        }
        
        request = SubmitAnswerRequest(**request_data)
        assert request.user_answer == ""