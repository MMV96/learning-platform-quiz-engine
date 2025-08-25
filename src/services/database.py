import logging
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from bson import ObjectId
from datetime import datetime

from ..config import settings
from ..models.session import QuizSession, Answer, SessionStatus

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
        self.sessions_collection: Optional[AsyncIOMotorCollection] = None

    async def connect(self) -> None:
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            # Test connection
            await self.client.admin.command('ping')
            logger.info("Successfully connected to MongoDB")
            
            # Get database (extract from connection string or use default)
            db_name = settings.mongodb_url.split('/')[-1].split('?')[0] if '/' in settings.mongodb_url else 'learning_platform'
            self.database = self.client[db_name]
            
            # Get collections
            self.sessions_collection = self.database['quiz_sessions']
            
            # Create indexes for better performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def disconnect(self) -> None:
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def _create_indexes(self) -> None:
        try:
            # Index on user_id for faster queries
            await self.sessions_collection.create_index("user_id")
            # Index on quiz_id for faster queries
            await self.sessions_collection.create_index("quiz_id")
            # Index on status for filtering
            await self.sessions_collection.create_index("status")
            # Compound index for user sessions
            await self.sessions_collection.create_index([("user_id", 1), ("started_at", -1)])
            
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    # Quiz Session Operations
    async def create_session(self, session: QuizSession) -> str:
        try:
            session_dict = session.model_dump(exclude={'id'})
            result = await self.sessions_collection.insert_one(session_dict)
            logger.info(f"Created new quiz session: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[QuizSession]:
        try:
            if not ObjectId.is_valid(session_id):
                return None
                
            session_doc = await self.sessions_collection.find_one({"_id": ObjectId(session_id)})
            if session_doc:
                session_doc['_id'] = str(session_doc['_id'])
                return QuizSession(**session_doc)
            return None
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            raise

    async def update_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        try:
            if not ObjectId.is_valid(session_id):
                return False
                
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            raise

    async def add_answer(self, session_id: str, answer: Answer) -> bool:
        try:
            if not ObjectId.is_valid(session_id):
                return False
                
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {"$push": {"answers": answer.model_dump()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to add answer to session {session_id}: {e}")
            raise

    async def complete_session(self, session_id: str, score: float) -> bool:
        try:
            if not ObjectId.is_valid(session_id):
                return False
                
            result = await self.sessions_collection.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$set": {
                        "score": score,
                        "completed_at": datetime.utcnow(),
                        "status": SessionStatus.COMPLETED
                    }
                }
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            raise

    async def get_user_sessions(self, user_id: str, limit: int = 10, offset: int = 0) -> List[QuizSession]:
        try:
            cursor = self.sessions_collection.find({"user_id": user_id})
            cursor = cursor.sort("started_at", -1).skip(offset).limit(limit)
            
            sessions = []
            async for session_doc in cursor:
                session_doc['_id'] = str(session_doc['_id'])
                sessions.append(QuizSession(**session_doc))
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get sessions for user {user_id}: {e}")
            raise

# Create a global instance
db_service = DatabaseService()