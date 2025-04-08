from celery import Celery
from .file_service import FileService
from models.sentiment_model import SentimentModel
from utils.config import Config
import os

# Celery configuration
celery = Celery(
    __name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND
)


class ClassificationService:
    def __init__(self):
        self.file_service = FileService(Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER)
        self.sentiment_model = SentimentModel(Config.MODEL_PATH, Config.LABEL_PATH)


@celery.task(bind=True)
def classification_task(self, unique_id, classification_types=["sentiment"]):
    self.update_state(state="PENDING")
    service = ClassificationService()
    file_service = service.file_service
    sentiment_model = service.sentiment_model

    stored_filename = file_service.get_hash(unique_id)
    if not stored_filename:
        raise NameError("Cannot fetch hash file of task", unique_id)
    file_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)
    comments = file_service.read_comments(file_path)
    total = len(comments)
    file_service.set_state(unique_id, "processing")
    self.update_state(
        state="PROCESSING",
        meta={"current": 0, "total": total},
    )
    classified_data = []
    for idx, comment in enumerate(comments):
        result = {"comment": comment}
        self.update_state(
            state="PROCESSING",
            meta={"current": idx, "total": total},
        )
        if "sentiment" in classification_types:
            sentiment = sentiment_model.predict(comment)
            result["sentiment"] = sentiment

        classified_data.append(result)

    file_service.save_classified_data(classified_data, stored_filename)
    file_service.set_state(unique_id, "success")
    return stored_filename
