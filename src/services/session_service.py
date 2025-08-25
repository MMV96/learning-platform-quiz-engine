import logging
from typing import Optional
from datetime import datetime

from ..models.session import (
    QuizSession, Answer, SessionStatus, 
    StartSessionRequest, StartSessionResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    SessionStatusResponse, CompleteSessionResponse
)
from ..models.quiz import Quiz
from .database import db_service
from .quiz_client import quiz_client, QuizClientError

logger = logging.getLogger(__name__)

class SessionServiceError(Exception):
    pass

class SessionService:
    def __init__(self):
        pass

    def calculate_score(self, answers: list[Answer]) -> float:
        if not answers:
            return 0.0
        
        correct_count = sum(1 for answer in answers if answer.is_correct)
        return (correct_count / len(answers)) * 100

    async def start_session(self, request: StartSessionRequest) -> StartSessionResponse:
        try:
            # First, verify the quiz exists and get its details
            quiz = await quiz_client.get_quiz(request.quiz_id)
            if not quiz:
                raise SessionServiceError(f"Quiz {request.quiz_id} not found")

            # Create new quiz session
            session = QuizSession(
                user_id=request.user_id,
                quiz_id=request.quiz_id,
                book_id=quiz.book_id,
                status=SessionStatus.IN_PROGRESS
            )

            # Save to database
            session_id = await db_service.create_session(session)

            logger.info(f"Started new quiz session {session_id} for user {request.user_id}")
            
            return StartSessionResponse(
                session_id=session_id,
                quiz_id=request.quiz_id,
                total_questions=quiz.questions_count,
                status=SessionStatus.IN_PROGRESS,
                started_at=session.started_at
            )

        except QuizClientError as e:
            logger.error(f"Quiz client error starting session: {e}")
            raise SessionServiceError(f"Failed to verify quiz: {e}")
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            raise SessionServiceError(f"Failed to start session: {e}")

    async def submit_answer(self, session_id: str, request: SubmitAnswerRequest) -> SubmitAnswerResponse:
        try:
            # Get the session
            session = await db_service.get_session(session_id)
            if not session:
                raise SessionServiceError(f"Session {session_id} not found")

            if session.status != SessionStatus.IN_PROGRESS:
                raise SessionServiceError(f"Session {session_id} is not in progress")

            # Get the quiz to validate the answer
            quiz = await quiz_client.get_quiz(session.quiz_id)
            if not quiz:
                raise SessionServiceError(f"Quiz {session.quiz_id} not found")

            # Validate question index
            if request.question_index < 0 or request.question_index >= len(quiz.questions):
                raise SessionServiceError(f"Invalid question index: {request.question_index}")

            # Check if this question was already answered
            existing_answer = next(
                (answer for answer in session.answers if answer.question_index == request.question_index),
                None
            )
            if existing_answer:
                raise SessionServiceError(f"Question {request.question_index} already answered")

            # Get the question and validate answer
            question = quiz.questions[request.question_index]
            
            # Normalize answers for comparison (case-insensitive)
            user_answer_normalized = request.user_answer.strip().lower()
            correct_answer_normalized = str(question.correct_answer).strip().lower()
            
            is_correct = user_answer_normalized == correct_answer_normalized

            # Create answer record
            answer = Answer(
                question_index=request.question_index,
                user_answer=request.user_answer,
                is_correct=is_correct,
                answered_at=datetime.utcnow()
            )

            # Add answer to session
            await db_service.add_answer(session_id, answer)

            # Get updated session to calculate current score
            updated_session = await db_service.get_session(session_id)
            current_score = self.calculate_score(updated_session.answers)

            logger.info(f"Answer submitted for session {session_id}, question {request.question_index}, correct: {is_correct}")

            return SubmitAnswerResponse(
                is_correct=is_correct,
                correct_answer=str(question.correct_answer),
                explanation=question.explanation,
                current_score=current_score,
                questions_answered=len(updated_session.answers),
                total_questions=len(quiz.questions)
            )

        except SessionServiceError:
            raise
        except Exception as e:
            logger.error(f"Error submitting answer for session {session_id}: {e}")
            raise SessionServiceError(f"Failed to submit answer: {e}")

    async def get_session_status(self, session_id: str) -> SessionStatusResponse:
        try:
            session = await db_service.get_session(session_id)
            if not session:
                raise SessionServiceError(f"Session {session_id} not found")

            # Get quiz to determine total questions
            quiz = await quiz_client.get_quiz(session.quiz_id)
            total_questions = len(quiz.questions) if quiz else 0

            return SessionStatusResponse(
                session_id=session_id,
                quiz_id=session.quiz_id,
                book_id=session.book_id,
                status=session.status,
                score=session.score if session.score is not None else self.calculate_score(session.answers),
                questions_answered=len(session.answers),
                total_questions=total_questions,
                started_at=session.started_at,
                completed_at=session.completed_at
            )

        except SessionServiceError:
            raise
        except Exception as e:
            logger.error(f"Error getting session status {session_id}: {e}")
            raise SessionServiceError(f"Failed to get session status: {e}")

    async def complete_session(self, session_id: str) -> CompleteSessionResponse:
        try:
            session = await db_service.get_session(session_id)
            if not session:
                raise SessionServiceError(f"Session {session_id} not found")

            if session.status != SessionStatus.IN_PROGRESS:
                raise SessionServiceError(f"Session {session_id} is not in progress")

            # Calculate final score
            final_score = self.calculate_score(session.answers)

            # Mark session as completed
            success = await db_service.complete_session(session_id, final_score)
            if not success:
                raise SessionServiceError(f"Failed to update session {session_id}")

            # Get quiz to determine total questions
            quiz = await quiz_client.get_quiz(session.quiz_id)
            total_questions = len(quiz.questions) if quiz else 0

            completion_time = datetime.utcnow()

            logger.info(f"Completed session {session_id} with score {final_score}%")

            return CompleteSessionResponse(
                session_id=session_id,
                final_score=final_score,
                questions_answered=len(session.answers),
                total_questions=total_questions,
                completed_at=completion_time,
                status=SessionStatus.COMPLETED
            )

        except SessionServiceError:
            raise
        except Exception as e:
            logger.error(f"Error completing session {session_id}: {e}")
            raise SessionServiceError(f"Failed to complete session: {e}")

# Create a global instance
session_service = SessionService()