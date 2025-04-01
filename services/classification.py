from .file_service import FileService
#from models.bert_classifier import BertClassifier
from models.sentiment_model import SentimentModel
#from utils.theme_mapping import ThemeMapping
from utils.config import Config
import os

class ClassificationService:
    def __init__(self, upload_folder, output_folder):
        self.file_service = FileService(upload_folder, output_folder)
        self.sentiment_model = SentimentModel(Config.MODEL_PATH, Config.LABEL_PATH)

    def classify_comments(self, file, classification_types=['sentiment']):
        file_path = self.file_service.save_uploaded_file(file)
        comments = self.file_service.read_comments(file_path)

        classified_data = []
        for comment in comments:
            result = {'comment': comment}

            if 'sentiment' in classification_types:
                sentiment = self.sentiment_model.predict(comment)
                result['sentiment'] = sentiment

            classified_data.append(result)

        output_filename = 'classified_' + os.path.basename(file_path)
        output_path = self.file_service.save_classified_data(classified_data, output_filename)
        return output_path
