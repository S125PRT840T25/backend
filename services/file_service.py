import os
import pandas as pd
from werkzeug.utils import secure_filename

class FileService:
    def __init__(self, upload_folder, output_folder):
        self.upload_folder = upload_folder
        self.output_folder = output_folder
        os.makedirs(upload_folder, exist_ok=True)
        os.makedirs(output_folder, exist_ok=True)

    def save_uploaded_file(self, file):
        filename = secure_filename(file.filename)
        file_path = os.path.join(self.upload_folder, filename)
        file.save(file_path)
        return file_path

    def read_comments(self, file_path):
        df = pd.read_csv(file_path)
        if 'comment' not in df.columns:
            raise ValueError("CSV must have a 'comment' column")
        return df['comment'].tolist()

    def save_classified_data(self, data, output_filename='classified.csv'):
        df = pd.DataFrame(data)
        output_path = os.path.join(self.output_folder, output_filename)
        df.to_csv(output_path, index=False)
        return output_path
