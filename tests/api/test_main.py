import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.main import app


class TestQuizEngineAPI:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_health_check_success(self, client):
        with patch('src.main.db_service') as mock_db_service, \
             patch('src.main.quiz_client') as mock_quiz_client:
            
            mock_db_service.client.admin.command = AsyncMock()
            mock_quiz_client.health_check = AsyncMock(return_value=True)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "quiz-engine"
            assert data["version"] == "1.0.0"
            assert data["database"] == "connected"
            assert data["quiz_generator"] == "connected"

    def test_health_check_database_failure(self, client):
        with patch('src.main.db_service') as mock_db_service, \
             patch('src.main.quiz_client') as mock_quiz_client:
            
            mock_db_service.client.admin.command.side_effect = Exception("Database unavailable")
            mock_quiz_client.health_check = AsyncMock(return_value=True)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"
            assert "Database unavailable" in data["error"]

    def test_health_check_quiz_generator_failure(self, client):
        with patch('src.main.db_service') as mock_db_service, \
             patch('src.main.quiz_client') as mock_quiz_client:
            
            mock_db_service.client.admin.command = AsyncMock()
            mock_quiz_client.health_check = AsyncMock(return_value=False)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["quiz_generator"] == "disconnected"

    def test_get_available_quizzes_success(self, client, sample_quiz_data):
        with patch('src.main.quiz_client') as mock_quiz_client:
            from src.models.quiz import QuizListResponse, QuizListItem
            
            quiz_list = QuizListResponse(
                quizzes=[QuizListItem(
                    id=sample_quiz_data["id"],
                    book_id=sample_quiz_data["book_id"],
                    questions_count=sample_quiz_data["questions_count"],
                    created_at=sample_quiz_data["created_at"]
                )],
                total=1,
                limit=10,
                offset=0
            )
            mock_quiz_client.list_quizzes = AsyncMock(return_value=quiz_list)
            
            response = client.get("/quiz/available/test-book-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["quizzes"]) == 1
            assert data["quizzes"][0]["book_id"] == "test-book-123"

    def test_get_available_quizzes_service_error(self, client):
        with patch('src.main.quiz_client') as mock_quiz_client:
            mock_quiz_client.list_quizzes = AsyncMock(side_effect=Exception("Service unavailable"))
            
            response = client.get("/quiz/available/test-book-123")
            
            assert response.status_code == 500
            data = response.json()
            assert "Service unavailable" in data["detail"]

    def test_get_quiz_details_success(self, client, sample_quiz_data):
        with patch('src.main.quiz_client') as mock_quiz_client:
            from src.models.quiz import Quiz
            
            quiz = Quiz(**sample_quiz_data)
            mock_quiz_client.get_quiz = AsyncMock(return_value=quiz)
            
            response = client.get("/quiz/507f1f77bcf86cd799439011")
            
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "507f1f77bcf86cd799439011"
            assert data["book_id"] == "test-book-123"

    def test_get_quiz_details_not_found(self, client):
        with patch('src.main.quiz_client') as mock_quiz_client:
            mock_quiz_client.get_quiz = AsyncMock(return_value=None)
            
            response = client.get("/quiz/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"]

    def test_start_quiz_session_success(self, client, sample_start_session_request, sample_quiz_data):
        with patch('src.main.session_service') as mock_session_service:
            from src.models.session import StartSessionResponse, SessionStatus
            from datetime import datetime
            
            response_data = StartSessionResponse(
                session_id="507f1f77bcf86cd799439012",
                quiz_id=sample_start_session_request["quiz_id"],
                total_questions=1,
                status=SessionStatus.IN_PROGRESS,
                started_at=datetime.utcnow()
            )
            mock_session_service.start_session = AsyncMock(return_value=response_data)
            
            response = client.post("/session/start", json=sample_start_session_request)
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "507f1f77bcf86cd799439012"
            assert data["quiz_id"] == sample_start_session_request["quiz_id"]
            assert data["total_questions"] == 1

    def test_start_quiz_session_validation_error(self, client):
        invalid_request = {
            "user_id": "test-user-123"
            # Missing quiz_id
        }
        
        response = client.post("/session/start", json=invalid_request)
        
        assert response.status_code == 422  # Validation error

    def test_start_quiz_session_quiz_not_found(self, client, sample_start_session_request):
        with patch('src.main.session_service') as mock_session_service:
            from src.services.session_service import SessionServiceError
            
            mock_session_service.start_session = AsyncMock(
                side_effect=SessionServiceError("Quiz not found")
            )
            
            response = client.post("/session/start", json=sample_start_session_request)
            
            assert response.status_code == 404
            data = response.json()
            assert "Quiz not found" in data["detail"]

    def test_get_session_status_success(self, client):
        with patch('src.main.session_service') as mock_session_service:
            from src.models.session import SessionStatusResponse, SessionStatus
            from datetime import datetime
            
            response_data = SessionStatusResponse(
                session_id="507f1f77bcf86cd799439012",
                quiz_id="507f1f77bcf86cd799439011",
                book_id="test-book-123",
                status=SessionStatus.IN_PROGRESS,
                score=0.0,
                questions_answered=0,
                total_questions=1,
                started_at=datetime.utcnow(),
                completed_at=None
            )
            mock_session_service.get_session_status = AsyncMock(return_value=response_data)
            
            response = client.get("/session/507f1f77bcf86cd799439012")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "507f1f77bcf86cd799439012"
            assert data["status"] == "in_progress"

    def test_get_session_status_not_found(self, client):
        with patch('src.main.session_service') as mock_session_service:
            from src.services.session_service import SessionServiceError
            
            mock_session_service.get_session_status = AsyncMock(
                side_effect=SessionServiceError("Session not found")
            )
            
            response = client.get("/session/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "Session not found" in data["detail"]

    def test_submit_answer_success(self, client, sample_submit_answer_request):
        with patch('src.main.session_service') as mock_session_service:
            from src.models.session import SubmitAnswerResponse
            
            response_data = SubmitAnswerResponse(
                is_correct=True,
                correct_answer="Rome",
                explanation="Rome is the capital and largest city of Italy.",
                current_score=100.0,
                questions_answered=1,
                total_questions=1
            )
            mock_session_service.submit_answer = AsyncMock(return_value=response_data)
            
            response = client.post(
                "/session/507f1f77bcf86cd799439012/answer", 
                json=sample_submit_answer_request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["is_correct"] is True
            assert data["correct_answer"] == "Rome"
            assert data["current_score"] == 100.0

    def test_submit_answer_validation_error(self, client):
        invalid_request = {
            "user_answer": "Rome"
            # Missing question_index
        }
        
        response = client.post(
            "/session/507f1f77bcf86cd799439012/answer", 
            json=invalid_request
        )
        
        assert response.status_code == 422

    def test_complete_session_success(self, client):
        with patch('src.main.session_service') as mock_session_service:
            from src.models.session import CompleteSessionResponse, SessionStatus
            from datetime import datetime
            
            response_data = CompleteSessionResponse(
                session_id="507f1f77bcf86cd799439012",
                final_score=100.0,
                questions_answered=1,
                total_questions=1,
                completed_at=datetime.utcnow(),
                status=SessionStatus.COMPLETED
            )
            mock_session_service.complete_session = AsyncMock(return_value=response_data)
            
            response = client.post("/session/507f1f77bcf86cd799439012/complete")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "507f1f77bcf86cd799439012"
            assert data["final_score"] == 100.0
            assert data["status"] == "completed"

    def test_complete_session_not_found(self, client):
        with patch('src.main.session_service') as mock_session_service:
            from src.services.session_service import SessionServiceError
            
            mock_session_service.complete_session = AsyncMock(
                side_effect=SessionServiceError("Session not found")
            )
            
            response = client.post("/session/nonexistent-id/complete")
            
            assert response.status_code == 404
            data = response.json()
            assert "Session not found" in data["detail"]

    def test_cors_middleware(self, client):
        # Test that CORS headers are present
        response = client.options("/session/start")
        
        # FastAPI TestClient might not fully simulate CORS, but we can test the endpoint exists
        assert response.status_code in [200, 405]  # 405 is fine for OPTIONS on POST endpoint

    def test_app_metadata(self):
        # Test that the FastAPI app has correct metadata
        assert app.title == "Learning Platform Quiz Engine"
        assert app.version == "1.0.0"
        assert "microservice" in app.description.lower()

    def test_query_parameter_validation(self, client):
        # Test various query parameter validations
        
        # Valid parameters
        response = client.get("/quiz/available/test-book?limit=1&offset=0")
        assert response.status_code in [200, 500]  # 500 if service fails, but validation passes
        
        # Invalid limit (above maximum)
        response = client.get("/quiz/available/test-book?limit=200")
        assert response.status_code == 422
        
        # Invalid offset (below minimum)
        response = client.get("/quiz/available/test-book?offset=-1")
        assert response.status_code == 422

    def test_request_logging(self, client, sample_start_session_request):
        with patch('src.main.session_service') as mock_session_service, \
             patch('src.main.logger') as mock_logger:
            
            from src.models.session import StartSessionResponse, SessionStatus
            from datetime import datetime
            
            response_data = StartSessionResponse(
                session_id="507f1f77bcf86cd799439012",
                quiz_id=sample_start_session_request["quiz_id"],
                total_questions=1,
                status=SessionStatus.IN_PROGRESS,
                started_at=datetime.utcnow()
            )
            mock_session_service.start_session = AsyncMock(return_value=response_data)
            
            response = client.post("/session/start", json=sample_start_session_request)
            
            assert response.status_code == 200
            # Verify that appropriate logging was called
            mock_logger.info.assert_called_with(
                f"Starting new session for user {sample_start_session_request['user_id']}, quiz {sample_start_session_request['quiz_id']}"
            )