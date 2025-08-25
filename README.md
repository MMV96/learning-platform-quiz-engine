# Quiz Engine Service

A Python/FastAPI microservice for managing quiz sessions in the Learning Platform. This service handles quiz discovery, session management, answer validation, and scoring.

## 🏗️ Architecture

The Quiz Engine serves as an intermediary between users and the quiz-generator service, managing quiz sessions and user interactions locally while fetching quiz content from the quiz-generator API.

### External Dependencies
- **MongoDB**: Local storage for quiz sessions
- **Quiz Generator Service**: HTTP API for quiz content

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB running locally
- Quiz Generator Service

### 1. Environment Setup
```bash
# Clone and navigate to project
cd quiz-engine

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# MONGODB_URL=mongodb://admin:password123@localhost:27017/learning_platform?authSource=admin
# QUIZ_GENERATOR_URL=http://quiz-generator
```

### 2. Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python -m src.main
# or
uvicorn src.main:app --host 0.0.0.0 --port 80 --reload
```

### 3. Docker Deployment
```bash
# Build image
docker build -t quiz-engine .

# Run container
docker run -p 80:80 --env-file .env quiz-engine
```

## 📊 API Endpoints

### Quiz Discovery (Proxy to quiz-generator)
```http
GET /api/quiz/available/{book_id}?limit=10&offset=0
GET /api/quiz/{quiz_id}
```

### Session Management
```http
POST /api/session/start
GET /api/session/{session_id}
POST /api/session/{session_id}/answer
POST /api/session/{session_id}/complete
```

### Health Check
```http
GET /health
```

## 🔌 Usage Examples

### 1. Start a Quiz Session
```bash
curl -X POST "http://localhost/api/session/start" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "quiz_id": "60f7b1b3c9a6b1234567890a"
  }'
```

Response:
```json
{
  "session_id": "60f7b1b3c9a6b1234567890b",
  "quiz_id": "60f7b1b3c9a6b1234567890a",
  "total_questions": 10,
  "status": "in_progress",
  "started_at": "2024-01-15T10:30:00Z"
}
```

### 2. Submit an Answer
```bash
curl -X POST "http://localhost/api/session/{session_id}/answer" \
  -H "Content-Type: application/json" \
  -d '{
    "question_index": 0,
    "user_answer": "Machine learning is a branch of AI"
  }'
```

Response:
```json
{
  "is_correct": true,
  "correct_answer": "Machine learning is a branch of AI",
  "explanation": "Machine learning is indeed a branch of artificial intelligence...",
  "current_score": 100.0,
  "questions_answered": 1,
  "total_questions": 10
}
```

### 3. Get Session Status
```bash
curl "http://localhost/api/session/{session_id}"
```

### 4. Complete Session
```bash
curl -X POST "http://localhost/api/session/{session_id}/complete"
```

## 📋 Data Models

### Quiz Session
```python
{
  "id": "session_id",
  "user_id": "user123",
  "quiz_id": "quiz_id_from_generator",
  "book_id": "ml_basics_001",
  "answers": [
    {
      "question_index": 0,
      "user_answer": "user response",
      "is_correct": true,
      "answered_at": "2024-01-15T10:35:00Z"
    }
  ],
  "score": 85.5,
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:45:00Z",
  "status": "completed"
}
```

## 🔧 Configuration

### Environment Variables
| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URL` | MongoDB connection string | `mongodb://admin:password123@localhost:27017/learning_platform?authSource=admin` |
| `QUIZ_GENERATOR_URL` | Quiz Generator service URL | `http://quiz-generator` |
| `SERVICE_PORT` | Service port | `80` |
| `SERVICE_HOST` | Service host | `0.0.0.0` |
| `SERVICE_NAME` | Service name for logging | `quiz-engine` |
| `LOG_LEVEL` | Logging level | `INFO` |

## 🧪 Testing

The service provides a health endpoint to verify all dependencies:

```bash
curl http://localhost/health
```

Expected response when healthy:
```json
{
  "status": "healthy",
  "service": "quiz-engine",
  "version": "1.0.0",
  "database": "connected",
  "quiz_generator": "connected"
}
```

## 🏛️ Project Structure
```
quiz-engine/
├── src/
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Environment configuration
│   ├── models/
│   │   ├── quiz.py            # Quiz data models
│   │   └── session.py         # Session models
│   └── services/
│       ├── database.py        # MongoDB connection
│       ├── quiz_client.py     # Quiz-generator HTTP client
│       └── session_service.py # Session business logic
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## 🔍 Scoring Algorithm

Simple percentage-based scoring:
```python
score = (correct_answers / total_questions) * 100
```

## 🚨 Error Handling

The service returns appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (invalid session state, duplicate answers)
- `404` - Resource not found (session, quiz)
- `500` - Internal server error

## 🔗 Integration

This service integrates with:
- **Quiz Generator Service**: Fetches quiz content via HTTP API
- **MongoDB**: Stores quiz sessions locally
- **Future Services**: Ready for user authentication integration

## 📝 Development Notes

- Sessions are identified by MongoDB ObjectId
- Answer validation is case-insensitive
- Duplicate answers for the same question are prevented
- Sessions can only be completed once
- All timestamps are stored in UTC

---

**Service Port**: 80  
**Health Check**: `GET /health`  
**API Documentation**: Visit `http://localhost/docs` when running
