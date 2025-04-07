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
    self.update_state(state="PREPROCESSING")
    service = ClassificationService()
    file_service = service.file_service
    sentiment_model = service.sentiment_model

    filename = file_service.get_original_filename(unique_id)
    stored_filename = f"{unique_id}"
    file_path = os.path.join(Config.UPLOAD_FOLDER, stored_filename)
    comments = file_service.read_comments(file_path)
    total = len(comments)
    self.update_state(
        state="PROCESSING",
        meta={"current": 0, "total": total},
    )
    classified_data = []
    for idx, comment in enumerate(comments):
        result = {"comment": comment}
        self.update_state(meta={"current": idx})
        if "sentiment" in classification_types:
            sentiment = sentiment_model.predict(comment)
            result["sentiment"] = sentiment

        classified_data.append(result)

    self.update_state(state="POSTPROCESS")
    _, output_filename = file_service.save_classified_data(
        classified_data, unique_id, filename
    )
    return output_filename
