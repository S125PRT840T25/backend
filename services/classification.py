from celery import Celery
from .file_service import FileService
#from models.bert_classifier import BertClassifier
from models.sentiment_model import SentimentModel
#from utils.theme_mapping import ThemeMapping
from utils.config import Config
import os

# Celery configuration
celery = Celery(__name__, broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)

class ClassificationService:
    def __init__(self):
        self.file_service = FileService(Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER)
        self.sentiment_model = SentimentModel(Config.MODEL_PATH, Config.LABEL_PATH)

    @celery.task(bind=True)
    def classify_comments(self, file_path, classification_types=['sentiment']):
        filename = os.path.basename(file_path)
        self.file_service = FileService(Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER)
        comments = self.file_service.read_comments(file_path)
    
        classified_data = []
        for comment in comments:
            result = {'comment': comment}

            if 'sentiment' in classification_types:
                sentiment = self.sentiment_model.predict(comment)
                result['sentiment'] = sentiment

            classified_data.append(result)
            
        output_filename = f"processed_{filename}"
        output_path = self.file_service.save_classified_data(classified_data, output_filename)
        return output_filename
