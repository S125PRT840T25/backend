import os
import pandas as pd
from werkzeug.utils import secure_filename
import uuid


class FileService:
    def __init__(self, upload_folder, output_folder):
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)
        self.filename_mapping = {}

    def save_uploaded_file(self, file):
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())
        stored_filename = f"{unique_id}"
        file_path = os.path.join(self.upload_folder, stored_filename)
        file.save(file_path)
        self.filename_mapping[unique_id] = original_filename
        return file_path, unique_id

    def read_comments(self, file_path):
        df = pd.read_csv(file_path)
        if "comment" not in df.columns:
            raise ValueError("CSV must have a 'comment' column")
        return df["comment"].tolist()

    def save_classified_data(self, data, unique_id, original_filename):
        output_filename = f"{unique_id}"
        output_path = os.path.join(self.output_folder, output_filename)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return output_path, output_filename

    def get_original_filename(self, unique_id):
        return self.filename_mapping.get(unique_id, None)
