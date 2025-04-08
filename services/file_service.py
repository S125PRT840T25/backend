import os
import pandas as pd
from werkzeug.utils import secure_filename
from services.db_service import DBService
import uuid
from utils.hashing_file import HashingFile


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
        file_path = os.path.join(self.upload_folder, stored_filename)

        old_file = self.db_service.get_filename(unique_id)
        if old_file:
            self.db_service.delete_record(unique_id)

        destination = open(file_path, "wb")
        hashing_file = HashingFile(destination)
        file.save(hashing_file, buffer_size=64 * 1024)
        file.close()
        hash_value = hashing_file.get_hash()
        hash_file_path = os.path.join(self.upload_folder, hash_value)
        old_id = None
        if not os.path.isfile(hash_file_path):
            os.rename(file_path, hash_file_path)
        else:
            os.remove(file_path)
            old_id = self.db_service.get_file_id(hash_value)
        size = os.path.getsize(hash_file_path)
        hash_id = self.db_service.check_hash(hash_value, size)
        self.db_service.save_file_record(unique_id, filename, hash_id, hash_value, size)
        return unique_id, old_id

    def read_comments(self, file_path, column="comment"):
        df = pd.read_csv(file_path)
        if column not in df.columns:
            raise ValueError(f"CSV must have a '{column}' column")
        return df[column].tolist()

    def save_classified_data(self, data, filename):
        output_path = os.path.join(self.output_folder, filename)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        return filename

    def get_original_filename(self, unique_id):
        return self.db_service.get_filename(unique_id)

    def delete_file(self, filename):
        upload_file = os.path.join(self.upload_folder, filename)
        output_file = os.path.join(self.output_folder, filename)
        if os.path.exists(upload_file):
            os.remove(upload_file)
        if os.path.exists(output_file):
            os.remove(output_file)

    def get_hash(self, u_id):
        return self.db_service.get_file_hash(u_id)

    def get_state(self, unique_id):
        return self.db_service.get_file_state(unique_id)

    def set_state(self, u_id, state):
        self.db_service.update_file_state(u_id, state)

    def get_original_id(self, uid):
        hash_value = self.db_service.get_file_hash(uid)
        return self.db_service.get_file_id(hash_value)
