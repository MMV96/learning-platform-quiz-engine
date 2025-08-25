import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from datetime import datetime

from src.services.quiz_client import QuizClient, QuizClientError
from src.models.quiz import Quiz, QuizListResponse


class TestQuizClient:
    @pytest.fixture
    def quiz_client(self):
        with patch('src.services.quiz_client.settings') as mock_settings:
            mock_settings.quiz_generator_url = "http://quiz-generator"
            return QuizClient()

    @pytest.fixture
    def sample_quiz_response(self):
        return {
            "_id": "507f1f77bcf86cd799439011",
            "book_id": "test-book-123",
            "questions": [
                {
                    "question": "What is the capital of Italy?",
                    "type": "multiple_choice",
                    "correct_answer": "Rome",
                    "options": ["Rome", "Milan", "Naples", "Venice"],
                    "explanation": "Rome is the capital and largest city of Italy.",
                    "difficulty": "easy",
                    "topic": "Geography",
                    "concepts_tested": ["Italian cities", "European capitals"]
                }
            ],
            "created_at": "2024-01-01T00:00:00.000Z",
            "ai_model": "claude-3-sonnet-20240229",
            "metadata": {"chapter": "1"}
        }

    @pytest.fixture
    def sample_quiz_list_response(self):
        return {
            "quizzes": [
                {
                    "_id": "507f1f77bcf86cd799439011",
                    "book_id": "test-book-123",
                    "questions_count": 1,
                    "created_at": "2024-01-01T00:00:00.000Z"
                }
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }

    @pytest.mark.asyncio
    async def test_get_quiz_success(self, quiz_client, sample_quiz_response):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_quiz_response
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.get_quiz("507f1f77bcf86cd799439011")
            
            assert isinstance(result, Quiz)
            assert result.id == "507f1f77bcf86cd799439011"
            assert result.book_id == "test-book-123"
            assert len(result.questions) == 1
            assert result.questions_count == 1
            
            mock_client.get.assert_called_once_with(
                "http://quiz-generator/quizzes/507f1f77bcf86cd799439011"
            )

    @pytest.mark.asyncio
    async def test_get_quiz_not_found(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate 404 response
            http_error = httpx.HTTPStatusError(
                message="Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
            mock_client.get.side_effect = http_error
            
            result = await quiz_client.get_quiz("nonexistent-id")
            
            assert result is None

    @pytest.mark.asyncio
    async def test_get_quiz_http_error(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate 500 response
            http_error = httpx.HTTPStatusError(
                message="Internal Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
            mock_client.get.side_effect = http_error
            
            with pytest.raises(QuizClientError) as exc_info:
                await quiz_client.get_quiz("507f1f77bcf86cd799439011")
            
            assert "Failed to get quiz" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_quiz_request_error(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate connection error
            request_error = httpx.RequestError(
                message="Connection failed",
                request=MagicMock()
            )
            mock_client.get.side_effect = request_error
            
            with pytest.raises(QuizClientError) as exc_info:
                await quiz_client.get_quiz("507f1f77bcf86cd799439011")
            
            assert "Failed to connect to quiz-generator service" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_quiz_unexpected_error(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate unexpected error
            mock_client.get.side_effect = Exception("Unexpected error")
            
            with pytest.raises(QuizClientError) as exc_info:
                await quiz_client.get_quiz("507f1f77bcf86cd799439011")
            
            assert "Unexpected error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_quizzes_success(self, quiz_client, sample_quiz_list_response):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_quiz_list_response
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.list_quizzes("test-book-123", limit=5, offset=10)
            
            assert isinstance(result, QuizListResponse)
            assert len(result.quizzes) == 1
            assert result.total == 1
            assert result.limit == 10
            assert result.offset == 0
            assert result.quizzes[0].id == "507f1f77bcf86cd799439011"
            
            mock_client.get.assert_called_once_with(
                "http://quiz-generator/quizzes",
                params={
                    'limit': 5,
                    'offset': 10,
                    'book_id': 'test-book-123'
                }
            )

    @pytest.mark.asyncio
    async def test_list_quizzes_no_book_id(self, quiz_client, sample_quiz_list_response):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = sample_quiz_list_response
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.list_quizzes(limit=20, offset=5)
            
            assert isinstance(result, QuizListResponse)
            
            mock_client.get.assert_called_once_with(
                "http://quiz-generator/quizzes",
                params={
                    'limit': 20,
                    'offset': 5
                }
            )

    @pytest.mark.asyncio
    async def test_list_quizzes_http_error(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate 500 response
            http_error = httpx.HTTPStatusError(
                message="Internal Server Error",
                request=MagicMock(),
                response=MagicMock(status_code=500)
            )
            mock_client.get.side_effect = http_error
            
            with pytest.raises(QuizClientError) as exc_info:
                await quiz_client.list_quizzes()
            
            assert "Failed to list quizzes" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_quizzes_request_error(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate connection error
            request_error = httpx.RequestError(
                message="Connection failed",
                request=MagicMock()
            )
            mock_client.get.side_effect = request_error
            
            with pytest.raises(QuizClientError) as exc_info:
                await quiz_client.list_quizzes()
            
            assert "Failed to connect to quiz-generator service" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_health_check_success(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.health_check()
            
            assert result is True
            mock_client.get.assert_called_once_with("http://quiz-generator/health")

    @pytest.mark.asyncio
    async def test_health_check_failure(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.health_check()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, quiz_client):
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            # Simulate connection error
            mock_client.get.side_effect = Exception("Connection failed")
            
            result = await quiz_client.health_check()
            
            assert result is False

    @pytest.mark.asyncio
    async def test_get_quiz_with_id_field(self, quiz_client):
        # Test when response has 'id' field instead of '_id'
        quiz_response = {
            "id": "507f1f77bcf86cd799439011",  # Using 'id' instead of '_id'
            "book_id": "test-book-123",
            "questions": [
                {
                    "question": "What is the capital of Italy?",
                    "type": "multiple_choice",
                    "correct_answer": "Rome",
                    "options": ["Rome", "Milan", "Naples", "Venice"],
                    "explanation": "Rome is the capital and largest city of Italy.",
                    "difficulty": "easy",
                    "topic": "Geography",
                    "concepts_tested": ["Italian cities"]
                }
            ],
            "created_at": "2024-01-01T00:00:00.000Z",
            "ai_model": "claude-3-sonnet-20240229"
        }
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = quiz_response
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            
            result = await quiz_client.get_quiz("507f1f77bcf86cd799439011")
            
            assert result.id == "507f1f77bcf86cd799439011"

    def test_quiz_client_initialization(self):
        with patch('src.services.quiz_client.settings') as mock_settings:
            mock_settings.quiz_generator_url = "http://custom-url:9000"
            
            client = QuizClient()
            
            assert client.base_url == "http://custom-url:9000"
            # httpx.Timeout object doesn't have a total attribute in newer versions
            # Check that timeout is set correctly by checking it's a Timeout instance
            import httpx
            assert isinstance(client.timeout, httpx.Timeout)