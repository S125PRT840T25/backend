class Config:
    MODEL_PATH = "data/fine_tuned_model"
    LABEL_PATH = "data/label_encoder.pkl"
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    CELERY_BROKER_URL = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/0"