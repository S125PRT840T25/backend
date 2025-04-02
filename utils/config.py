from dotenv import load_dotenv
import os
load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG").lower() == "true"
    MODEL_PATH = os.getenv("MODEL_PATH", "data/fine_tuned_model")
    LABEL_PATH = os.getenv("LABEL_PATH", "data/label_encoder.pkl")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER", "outputs")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")