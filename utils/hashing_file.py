# hashing_file.py
import hashlib

class HashingFile:
    def __init__(self, file):
        self.file = file
        self.hash = hashlib.sha256()
        
    def write(self, data):
        self.hash.update(data)
        self.file.write(data)
        
    def close(self):
        self.file.close()
        
    def get_hash(self):
        return self.hash.hexdigest()