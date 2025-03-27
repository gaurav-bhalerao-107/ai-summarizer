import os
from dotenv import load_dotenv

# Load environment variables from a .env file (optional for local development)
load_dotenv()

class Config:
    PROJECT_NAME = os.getenv("PROJECT_NAME", "AI Summarizer")
    
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5000))

    MONGO_DBNAME = os.getenv("MONGO_DBNAME", "summarizer_db")
    MONGO_DBURI = os.getenv("MONGO_DBURI", "mongodb://localhost:27017")

    BASE_URL = os.getenv("BASE_URL", "http://localhost:9000")

    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")  # Comma-separated list

config = Config()