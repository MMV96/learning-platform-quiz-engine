import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    # Database configuration
    mongodb_url: str = "mongodb://admin:password123@localhost:27017/learning_platform?authSource=admin"
    
    # External Services
    quiz_generator_url: str = "http://quiz-generator:8002"
    
    # Service configuration
    service_port: int = 8003
    service_host: str = "0.0.0.0"
    service_name: str = "quiz-engine"
    
    # Logging
    log_level: str = "INFO"
    
    model_config = ConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()