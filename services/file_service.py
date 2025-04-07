import os
import pandas as pd
from werkzeug.utils import secure_filename
from services.db_service import DBService
import uuid


class FileService:
    def __init__(self, upload_folder, output_folder):
        self.db_service = DBService()
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

    def save_uploaded_file(self, file):
        filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        stored_filename = f"{unique_id}"
        
        old_file = self.db_service.get_filename(unique_id)
        if old_file:
            self.db_service.delete_file_record()
        
        file_path = os.path.join(self.upload_folder, stored_filename)
        file.save(file_path, buffer_size = 128 * 1024)
        file.close()
        self.db_service.save_file_record(unique_id, filename)
        return file_path, unique_id

    def read_comments(self, file_path, column='comment'):
        df = pd.read_csv(file_path)
        if column not in df.columns:
            raise ValueError(f"CSV must have a '{column}' column")
        return df[column].tolist()

    def save_classified_data(self, data, unique_id, original_filename):
        output_filename = f"{unique_id}"
        output_path = os.path.join(self.output_folder, output_filename)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return output_path, output_filename

    def get_original_filename(self, unique_id):
        return self.db_service.get_filename(unique_id)

    def delete_file(self, unique_id):
        upload_file = os.path.join(self.upload_folder, unique_id)
        output_file = os.path.join(self.output_folder, unique_id)
        if os.path.exists(upload_file):
            os.remove(upload_file)
        if os.path.exists(output_file):
            os.remove(output_file)
            