import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.services.session_service import SessionService, SessionServiceError
from src.services.quiz_client import QuizClientError
from src.models.session import (
    QuizSession, Answer, SessionStatus,
    StartSessionRequest, SubmitAnswerRequest
)
from src.models.quiz import Quiz, Question, QuestionType, DifficultyLevel


class TestSessionService:
    @pytest.fixture
    def session_service(self):
        return SessionService()

    @pytest.fixture
    def sample_quiz(self):
        question = Question(
            question="What is the capital of Italy?",
            type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Rome",
            options=["Rome", "Milan", "Naples", "Venice"],
            explanation="Rome is the capital and largest city of Italy.",
            difficulty=DifficultyLevel.EASY,
            topic="Geography",
            concepts_tested=["Italian cities"]
        )
        
        return Quiz(
            id="quiz-123",
            book_id="book-456",
            questions=[question],
            questions_count=1,
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def sample_session(self):
        return QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.IN_PROGRESS
        )

    def test_calculate_score_empty_answers(self, session_service):
        result = session_service.calculate_score([])
        assert result == 0.0

    def test_calculate_score_all_correct(self, session_service):
        answers = [
            Answer(question_index=0, user_answer="Rome", is_correct=True),
            Answer(question_index=1, user_answer="Paris", is_correct=True)
        ]
        
        result = session_service.calculate_score(answers)
        assert result == 100.0

    def test_calculate_score_half_correct(self, session_service):
        answers = [
            Answer(question_index=0, user_answer="Rome", is_correct=True),
            Answer(question_index=1, user_answer="London", is_correct=False)
        ]
        
        result = session_service.calculate_score(answers)
        assert result == 50.0

    def test_calculate_score_all_incorrect(self, session_service):
        answers = [
            Answer(question_index=0, user_answer="Milan", is_correct=False),
            Answer(question_index=1, user_answer="London", is_correct=False)
        ]
        
        result = session_service.calculate_score(answers)
        assert result == 0.0

    @pytest.mark.asyncio
    async def test_start_session_success(self, session_service, sample_quiz):
        request = StartSessionRequest(user_id="user-456", quiz_id="quiz-123")
        
        with patch('src.services.session_service.quiz_client') as mock_quiz_client, \
             patch('src.services.session_service.db_service') as mock_db_service:
            
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            mock_db_service.create_session = AsyncMock(return_value="session-123")
            
            result = await session_service.start_session(request)
            
            assert result.session_id == "session-123"
            assert result.quiz_id == "quiz-123"
            assert result.total_questions == 1
            assert result.status == SessionStatus.IN_PROGRESS
            
            mock_quiz_client.get_quiz.assert_called_once_with("quiz-123")
            mock_db_service.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_session_quiz_not_found(self, session_service):
        request = StartSessionRequest(user_id="user-456", quiz_id="nonexistent-quiz")
        
        with patch('src.services.session_service.quiz_client') as mock_quiz_client:
            mock_quiz_client.get_quiz = AsyncMock(return_value=None)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.start_session(request)
            
            assert "Quiz nonexistent-quiz not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_quiz_client_error(self, session_service):
        request = StartSessionRequest(user_id="user-456", quiz_id="quiz-123")
        
        with patch('src.services.session_service.quiz_client') as mock_quiz_client:
            mock_quiz_client.get_quiz = AsyncMock(side_effect=QuizClientError("Service unavailable"))
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.start_session(request)
            
            assert "Failed to verify quiz" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_start_session_database_error(self, session_service, sample_quiz):
        request = StartSessionRequest(user_id="user-456", quiz_id="quiz-123")
        
        with patch('src.services.session_service.quiz_client') as mock_quiz_client, \
             patch('src.services.session_service.db_service') as mock_db_service:
            
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            mock_db_service.create_session = AsyncMock(side_effect=Exception("Database error"))
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.start_session(request)
            
            assert "Failed to start session" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_answer_success(self, session_service, sample_session, sample_quiz):
        request = SubmitAnswerRequest(question_index=0, user_answer="Rome")
        
        # Create a session with updated answers
        updated_session = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.IN_PROGRESS,
            answers=[Answer(question_index=0, user_answer="Rome", is_correct=True)]
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(side_effect=[sample_session, updated_session])
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            mock_db_service.add_answer = AsyncMock(return_value=True)
            
            result = await session_service.submit_answer("session-123", request)
            
            assert result.is_correct is True
            assert result.correct_answer == "Rome"
            assert result.explanation == "Rome is the capital and largest city of Italy."
            assert result.current_score == 100.0
            assert result.questions_answered == 1
            assert result.total_questions == 1
            
            mock_db_service.add_answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_submit_answer_incorrect(self, session_service, sample_session, sample_quiz):
        request = SubmitAnswerRequest(question_index=0, user_answer="Milan")
        
        # Create a session with updated answers
        updated_session = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.IN_PROGRESS,
            answers=[Answer(question_index=0, user_answer="Milan", is_correct=False)]
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(side_effect=[sample_session, updated_session])
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            mock_db_service.add_answer = AsyncMock(return_value=True)
            
            result = await session_service.submit_answer("session-123", request)
            
            assert result.is_correct is False
            assert result.correct_answer == "Rome"
            assert result.current_score == 0.0

    @pytest.mark.asyncio
    async def test_submit_answer_case_insensitive(self, session_service, sample_session, sample_quiz):
        request = SubmitAnswerRequest(question_index=0, user_answer="rome")  # lowercase
        
        # Create a session with updated answers
        updated_session = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.IN_PROGRESS,
            answers=[Answer(question_index=0, user_answer="rome", is_correct=True)]
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(side_effect=[sample_session, updated_session])
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            mock_db_service.add_answer = AsyncMock(return_value=True)
            
            result = await session_service.submit_answer("session-123", request)
            
            assert result.is_correct is True

    @pytest.mark.asyncio
    async def test_submit_answer_session_not_found(self, session_service):
        request = SubmitAnswerRequest(question_index=0, user_answer="Rome")
        
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=None)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.submit_answer("nonexistent-session", request)
            
            assert "Session nonexistent-session not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_answer_session_not_in_progress(self, session_service):
        request = SubmitAnswerRequest(question_index=0, user_answer="Rome")
        
        completed_session = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.COMPLETED
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=completed_session)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.submit_answer("session-123", request)
            
            assert "Session session-123 is not in progress" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_answer_invalid_question_index(self, session_service, sample_session, sample_quiz):
        request = SubmitAnswerRequest(question_index=5, user_answer="Rome")  # Invalid index
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(return_value=sample_session)
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.submit_answer("session-123", request)
            
            assert "Invalid question index: 5" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_submit_answer_already_answered(self, session_service, sample_quiz):
        request = SubmitAnswerRequest(question_index=0, user_answer="Rome")
        
        # Session with existing answer for question 0
        session_with_answer = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            answers=[Answer(question_index=0, user_answer="Milan", is_correct=False)],
            status=SessionStatus.IN_PROGRESS
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(return_value=session_with_answer)
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.submit_answer("session-123", request)
            
            assert "Question 0 already answered" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_session_status_success(self, session_service, sample_session, sample_quiz):
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(return_value=sample_session)
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            
            result = await session_service.get_session_status("session-123")
            
            assert result.session_id == "session-123"
            assert result.quiz_id == "quiz-123"
            assert result.book_id == "book-456"
            assert result.status == SessionStatus.IN_PROGRESS
            assert result.score == 0.0  # Calculated from empty answers
            assert result.questions_answered == 0
            assert result.total_questions == 1

    @pytest.mark.asyncio
    async def test_get_session_status_not_found(self, session_service):
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=None)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.get_session_status("nonexistent-session")
            
            assert "Session nonexistent-session not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_session_success(self, session_service, sample_quiz):
        session_with_answers = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            answers=[Answer(question_index=0, user_answer="Rome", is_correct=True)],
            status=SessionStatus.IN_PROGRESS
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service, \
             patch('src.services.session_service.quiz_client') as mock_quiz_client:
            
            mock_db_service.get_session = AsyncMock(return_value=session_with_answers)
            mock_db_service.complete_session = AsyncMock(return_value=True)
            mock_quiz_client.get_quiz = AsyncMock(return_value=sample_quiz)
            
            result = await session_service.complete_session("session-123")
            
            assert result.session_id == "session-123"
            assert result.final_score == 100.0
            assert result.questions_answered == 1
            assert result.total_questions == 1
            assert result.status == SessionStatus.COMPLETED
            
            mock_db_service.complete_session.assert_called_once_with("session-123", 100.0)

    @pytest.mark.asyncio
    async def test_complete_session_not_found(self, session_service):
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=None)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.complete_session("nonexistent-session")
            
            assert "Session nonexistent-session not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_session_not_in_progress(self, session_service):
        completed_session = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.COMPLETED
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=completed_session)
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.complete_session("session-123")
            
            assert "Session session-123 is not in progress" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_session_database_update_failed(self, session_service):
        session_in_progress = QuizSession(
            id="session-123",
            user_id="user-456",
            quiz_id="quiz-123",
            book_id="book-456",
            status=SessionStatus.IN_PROGRESS
        )
        
        with patch('src.services.session_service.db_service') as mock_db_service:
            mock_db_service.get_session = AsyncMock(return_value=session_in_progress)
            mock_db_service.complete_session = AsyncMock(return_value=False)  # Failed to update
            
            with pytest.raises(SessionServiceError) as exc_info:
                await session_service.complete_session("session-123")
            
            assert "Failed to update session session-123" in str(exc_info.value)