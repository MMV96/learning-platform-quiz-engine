import pytest
from datetime import datetime
from pydantic import ValidationError

from src.models.quiz import (
    QuestionType, DifficultyLevel, Question, Quiz, QuizListItem, QuizListResponse
)


class TestQuizModels:
    def test_question_type_enum(self):
        assert QuestionType.MULTIPLE_CHOICE == "multiple_choice"
        assert QuestionType.BOOLEAN == "boolean"
        assert QuestionType.OPEN == "open"

    def test_difficulty_level_enum(self):
        assert DifficultyLevel.EASY == "easy"
        assert DifficultyLevel.MEDIUM == "medium"
        assert DifficultyLevel.HARD == "hard"

    def test_question_creation_multiple_choice(self):
        question_data = {
            "question": "What is the capital of Italy?",
            "type": QuestionType.MULTIPLE_CHOICE,
            "correct_answer": "Rome",
            "options": ["Rome", "Milan", "Naples", "Venice"],
            "explanation": "Rome is the capital and largest city of Italy.",
            "difficulty": DifficultyLevel.EASY,
            "topic": "Geography",
            "concepts_tested": ["Italian cities", "European capitals"]
        }
        
        question = Question(**question_data)
        
        assert question.question == "What is the capital of Italy?"
        assert question.type == QuestionType.MULTIPLE_CHOICE
        assert question.correct_answer == "Rome"
        assert question.options == ["Rome", "Milan", "Naples", "Venice"]
        assert question.explanation == "Rome is the capital and largest city of Italy."
        assert question.difficulty == DifficultyLevel.EASY
        assert question.topic == "Geography"
        assert question.concepts_tested == ["Italian cities", "European capitals"]

    def test_question_creation_boolean(self):
        question_data = {
            "question": "Rome is the capital of Italy.",
            "type": QuestionType.BOOLEAN,
            "correct_answer": True,
            "explanation": "Yes, Rome is indeed the capital of Italy.",
            "difficulty": DifficultyLevel.EASY,
            "topic": "Geography",
            "concepts_tested": ["Italian capitals"]
        }
        
        question = Question(**question_data)
        
        assert question.question == "Rome is the capital of Italy."
        assert question.type == QuestionType.BOOLEAN
        assert question.correct_answer is True
        assert question.options is None
        assert question.explanation == "Yes, Rome is indeed the capital of Italy."

    def test_question_creation_open(self):
        question_data = {
            "question": "What is the capital of Italy?",
            "type": QuestionType.OPEN,
            "correct_answer": "Rome",
            "explanation": "Rome is the capital and largest city of Italy.",
            "difficulty": DifficultyLevel.MEDIUM,
            "topic": "Geography",
            "concepts_tested": ["Italian geography"]
        }
        
        question = Question(**question_data)
        
        assert question.question == "What is the capital of Italy?"
        assert question.type == QuestionType.OPEN
        assert question.correct_answer == "Rome"
        assert question.options is None

    def test_question_missing_required_fields(self):
        with pytest.raises(ValidationError) as exc_info:
            Question(
                question="Incomplete question",
                type=QuestionType.MULTIPLE_CHOICE
                # Missing required fields
            )
        
        errors = exc_info.value.errors()
        required_fields = {"correct_answer", "explanation", "difficulty", "topic", "concepts_tested"}
        error_fields = {error["loc"][0] for error in errors}
        
        assert required_fields.issubset(error_fields)

    def test_quiz_creation(self):
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
        
        quiz_data = {
            "id": "quiz-123",
            "book_id": "book-456",
            "questions": [question],
            "questions_count": 1,
            "created_at": datetime.utcnow(),
            "ai_model": "claude-3-sonnet-20240229",
            "metadata": {"chapter": "1", "difficulty": "easy"}
        }
        
        quiz = Quiz(**quiz_data)
        
        assert quiz.id == "quiz-123"
        assert quiz.book_id == "book-456"
        assert len(quiz.questions) == 1
        assert quiz.questions_count == 1
        assert quiz.ai_model == "claude-3-sonnet-20240229"
        assert quiz.metadata == {"chapter": "1", "difficulty": "easy"}

    def test_quiz_questions_count_mismatch(self):
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
        
        quiz_data = {
            "id": "quiz-123",
            "book_id": "book-456",
            "questions": [question],
            "questions_count": 5,  # Mismatch with actual questions length
            "created_at": datetime.utcnow()
        }
        
        # The model should still be created as it doesn't validate this constraint
        quiz = Quiz(**quiz_data)
        assert len(quiz.questions) == 1
        assert quiz.questions_count == 5

    def test_quiz_list_item_creation(self):
        quiz_item_data = {
            "id": "quiz-123",
            "book_id": "book-456",
            "questions_count": 10,
            "created_at": datetime.utcnow()
        }
        
        quiz_item = QuizListItem(**quiz_item_data)
        
        assert quiz_item.id == "quiz-123"
        assert quiz_item.book_id == "book-456"
        assert quiz_item.questions_count == 10

    def test_quiz_list_response_creation(self):
        quiz_item = QuizListItem(
            id="quiz-123",
            book_id="book-456",
            questions_count=10,
            created_at=datetime.utcnow()
        )
        
        quiz_list_data = {
            "quizzes": [quiz_item],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        
        quiz_list = QuizListResponse(**quiz_list_data)
        
        assert len(quiz_list.quizzes) == 1
        assert quiz_list.total == 1
        assert quiz_list.limit == 10
        assert quiz_list.offset == 0

    def test_quiz_list_response_empty(self):
        quiz_list_data = {
            "quizzes": [],
            "total": 0,
            "limit": 10,
            "offset": 0
        }
        
        quiz_list = QuizListResponse(**quiz_list_data)
        
        assert len(quiz_list.quizzes) == 0
        assert quiz_list.total == 0

    def test_question_with_invalid_type(self):
        with pytest.raises(ValidationError):
            Question(
                question="What is the capital of Italy?",
                type="invalid_type",  # Invalid enum value
                correct_answer="Rome",
                explanation="Rome is the capital and largest city of Italy.",
                difficulty=DifficultyLevel.EASY,
                topic="Geography",
                concepts_tested=["Italian cities"]
            )

    def test_question_with_invalid_difficulty(self):
        with pytest.raises(ValidationError):
            Question(
                question="What is the capital of Italy?",
                type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Rome",
                explanation="Rome is the capital and largest city of Italy.",
                difficulty="super_hard",  # Invalid enum value
                topic="Geography",
                concepts_tested=["Italian cities"]
            )

    def test_quiz_metadata_default(self):
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
        
        quiz_data = {
            "id": "quiz-123",
            "book_id": "book-456",
            "questions": [question],
            "questions_count": 1,
            "created_at": datetime.utcnow()
            # metadata not provided - should default to empty dict
        }
        
        quiz = Quiz(**quiz_data)
        assert quiz.metadata == {}