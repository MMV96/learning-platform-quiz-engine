import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app
from src.services.database import db_service
from src.services.quiz_client import quiz_client
from src.services.session_service import session_service


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_db_service():
    mock_service = AsyncMock()
    mock_service.client = MagicMock()
    mock_service.database = MagicMock()
    mock_service.sessions_collection = MagicMock()
    return mock_service


@pytest.fixture
def mock_quiz_client():
    mock_client = AsyncMock()
    return mock_client


@pytest.fixture
def sample_quiz_data():
    return {
        "id": "507f1f77bcf86cd799439011",
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
        "questions_count": 1,
        "created_at": datetime.utcnow(),
        "ai_model": "claude-3-sonnet-20240229",
        "metadata": {"chapter": "1"}
    }


@pytest.fixture
def sample_session_data():
    from src.models.session import QuizSession, SessionStatus
    return {
        "id": "507f1f77bcf86cd799439012",
        "user_id": "test-user-123",
        "quiz_id": "507f1f77bcf86cd799439011",
        "book_id": "test-book-123",
        "answers": [],
        "score": None,
        "started_at": datetime.utcnow(),
        "completed_at": None,
        "status": SessionStatus.IN_PROGRESS
    }


@pytest.fixture
def sample_start_session_request():
    return {
        "user_id": "test-user-123",
        "quiz_id": "507f1f77bcf86cd799439011"
    }


@pytest.fixture
def sample_submit_answer_request():
    return {
        "question_index": 0,
        "user_answer": "Rome"
    }