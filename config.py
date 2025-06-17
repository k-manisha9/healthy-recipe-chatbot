import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    SECRET_KEY = os.getenv("SECRET_KEY")
    SESSION_TYPE = "filesystem"  # Store sessions in the filesystem
    SESSION_FILE_DIR = "./flask_session"  # Directory to store session files
    SESSION_PERMANENT = False  # Sessions expire when the browser is closed
    SESSION_USE_SIGNER = True  # Sign session cookies for security