import os
from dotenv import load_dotenv

# Load environment variables from a .env file if present (works locally, ignored in Render)
load_dotenv()

class Config:
    # General
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///farmer360.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB upload limit

    # Google API
    GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
    GOOGLE_API_KEY1 = os.environ.get("GOOGLE_API_KEY1")
