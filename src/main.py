from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import Optional

from .config import settings
from .models.quiz import QuizListResponse, Quiz
from .models.session import (
    StartSessionRequest, StartSessionResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    SessionStatusResponse, CompleteSessionResponse
)
from .services.database import db_service
from .services.quiz_client import quiz_client
from .services.session_service import session_service, SessionServiceError

# Setup logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.service_name} service")
    await db_service.connect()
    yield
    # Shutdown
    logger.info(f"Shutting down {settings.service_name} service")
    await db_service.disconnect()

app = FastAPI(
    title="Learning Platform Quiz Engine",
    description="Microservice for managing quiz sessions and user interactions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Quiz Discovery Endpoints (proxy to quiz-generator)
@app.get("/api/quiz/available/{book_id}", response_model=QuizListResponse)
async def get_available_quizzes(
    book_id: str = Path(..., description="Book ID to filter quizzes"),
    limit: int = Query(10, ge=1, le=100, description="Number of quizzes to return"),
    offset: int = Query(0, ge=0, description="Number of quizzes to skip")
):
    try:
        logger.info(f"Fetching available quizzes for book_id: {book_id}")
        quiz_list = await quiz_client.list_quizzes(book_id, limit, offset)
        return quiz_list
    except Exception as e:
        logger.error(f"Error fetching quizzes for book {book_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/{quiz_id}", response_model=Quiz)
async def get_quiz_details(quiz_id: str = Path(..., description="Quiz ID")):
    try:
        logger.info(f"Fetching quiz details for quiz_id: {quiz_id}")
        quiz = await quiz_client.get_quiz(quiz_id)
        if not quiz:
            raise HTTPException(status_code=404, detail=f"Quiz {quiz_id} not found")
        return quiz
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quiz {quiz_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Session Management Endpoints
@app.post("/api/session/start", response_model=StartSessionResponse)
async def start_quiz_session(request: StartSessionRequest):
    try:
        logger.info(f"Starting new session for user {request.user_id}, quiz {request.quiz_id}")
        response = await session_service.start_session(request)
        return response
    except SessionServiceError as e:
        logger.warning(f"Session service error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/session/{session_id}", response_model=SessionStatusResponse)
async def get_session_status(session_id: str = Path(..., description="Session ID")):
    try:
        logger.info(f"Getting status for session {session_id}")
        response = await session_service.get_session_status(session_id)
        return response
    except SessionServiceError as e:
        logger.warning(f"Session service error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    request: SubmitAnswerRequest,
    session_id: str = Path(..., description="Session ID")
):
    try:
        logger.info(f"Submitting answer for session {session_id}, question {request.question_index}")
        response = await session_service.submit_answer(session_id, request)
        return response
    except SessionServiceError as e:
        logger.warning(f"Session service error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/session/{session_id}/complete", response_model=CompleteSessionResponse)
async def complete_session(session_id: str = Path(..., description="Session ID")):
    try:
        logger.info(f"Completing session {session_id}")
        response = await session_service.complete_session(session_id)
        return response
    except SessionServiceError as e:
        logger.warning(f"Session service error: {e}")
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing session: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health Check
@app.get("/health")
async def health_check():
    try:
        # Test database connection
        await db_service.client.admin.command('ping')
        
        # Test quiz-generator service connection
        quiz_generator_healthy = await quiz_client.health_check()
        
        health_status = {
            "status": "healthy" if quiz_generator_healthy else "degraded",
            "service": settings.service_name,
            "version": "1.0.0",
            "database": "connected",
            "quiz_generator": "connected" if quiz_generator_healthy else "disconnected"
        }
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": settings.service_name,
            "version": "1.0.0",
            "database": "disconnected",
            "quiz_generator": "unknown",
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.service_host, port=settings.service_port)