import logging
from typing import Optional
import httpx
from httpx import HTTPStatusError, RequestError

from ..config import settings
from ..models.quiz import Quiz, QuizListResponse

logger = logging.getLogger(__name__)

class QuizClientError(Exception):
    pass

class QuizClient:
    def __init__(self):
        self.base_url = settings.quiz_generator_url
        self.timeout = httpx.Timeout(30.0)

    async def get_quiz(self, quiz_id: str) -> Optional[Quiz]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(f"{self.base_url}/quizzes/{quiz_id}")
                response.raise_for_status()
                
                quiz_data = response.json()
                
                # Transform the response to match our Quiz model
                # The quiz-generator returns QuizDocument with questions inside
                quiz = Quiz(
                    id=quiz_data.get('id') or quiz_data.get('_id'),
                    book_id=quiz_data['book_id'],
                    questions=quiz_data['questions'],
                    questions_count=len(quiz_data['questions']),
                    created_at=quiz_data['created_at'],
                    ai_model=quiz_data.get('ai_model'),
                    metadata=quiz_data.get('metadata', {})
                )
                
                logger.info(f"Successfully retrieved quiz {quiz_id}")
                return quiz
                
            except HTTPStatusError as e:
                if e.response.status_code == 404:
                    logger.warning(f"Quiz {quiz_id} not found")
                    return None
                else:
                    logger.error(f"HTTP error getting quiz {quiz_id}: {e}")
                    raise QuizClientError(f"Failed to get quiz: {e}")
            except RequestError as e:
                logger.error(f"Request error getting quiz {quiz_id}: {e}")
                raise QuizClientError(f"Failed to connect to quiz-generator service: {e}")
            except Exception as e:
                logger.error(f"Unexpected error getting quiz {quiz_id}: {e}")
                raise QuizClientError(f"Unexpected error: {e}")

    async def list_quizzes(self, book_id: Optional[str] = None, limit: int = 10, offset: int = 0) -> QuizListResponse:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                params = {
                    'limit': limit,
                    'offset': offset
                }
                if book_id:
                    params['book_id'] = book_id
                
                response = await client.get(f"{self.base_url}/quizzes", params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Transform the response to match our QuizListResponse model
                quiz_list = QuizListResponse(
                    quizzes=[
                        {
                            'id': quiz.get('id') or quiz.get('_id'),
                            'book_id': quiz['book_id'],
                            'questions_count': quiz['questions_count'],
                            'created_at': quiz['created_at']
                        }
                        for quiz in data['quizzes']
                    ],
                    total=data['total'],
                    limit=data['limit'],
                    offset=data['offset']
                )
                
                logger.info(f"Successfully retrieved {len(quiz_list.quizzes)} quizzes for book_id: {book_id}")
                return quiz_list
                
            except HTTPStatusError as e:
                logger.error(f"HTTP error listing quizzes: {e}")
                raise QuizClientError(f"Failed to list quizzes: {e}")
            except RequestError as e:
                logger.error(f"Request error listing quizzes: {e}")
                raise QuizClientError(f"Failed to connect to quiz-generator service: {e}")
            except Exception as e:
                logger.error(f"Unexpected error listing quizzes: {e}")
                raise QuizClientError(f"Unexpected error: {e}")

    async def health_check(self) -> bool:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
            try:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
            except Exception as e:
                logger.warning(f"Quiz-generator health check failed: {e}")
                return False

# Create a global instance
quiz_client = QuizClient()