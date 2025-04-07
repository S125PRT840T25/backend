# Sentiment Analysis API

This project is a RESTful API built with Flask and Celery for processing CSV files containing comments and performing sentiment analysis asynchronously. It uses SQLite to manage file metadata and supports multiple file uploads with progress tracking.

## Features
- Upload CSV files for sentiment analysis.
- Asynchronous processing using Celery with custom task states ("Pending", "Processing", "Success").
- Download processed files with original filenames.
- CORS support for frontend integration.
- SQLite database for persistent file metadata storage.

## Prerequisites
Before setting up the project, ensure you have the following installed on your system:

- **Python 3.11+**: The project requires Python 3.11 or higher.
- **Redis**: Used as the Celery message broker. Install it locally or use a hosted service.
- **Git**: For cloning the repository.

## Setup Instructions

### 1. Clone the Repository
Clone the project to your local machine:
```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Install Python Dependencies
Create a virtual environment and install the required Python packages:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

The `requirements.txt` file should include:
```
flask
flask-cors
celery
redis
pandas
werkzeug
transformers
torch
```

### 3. Install Redis
Install and start Redis as the message broker:
- **On Ubuntu**:
  ```bash
  sudo apt-get update
  sudo apt-get install redis-server
  sudo systemctl enable redis-server
  sudo systemctl start redis-server
  ```
- **On macOS** (using Homebrew):
  ```bash
  brew install redis
  brew services start redis
  ```
- **On Windows**: Use WSL2 or a Redis Docker container, as native Windows support is limited.

Verify Redis is running:
```bash
redis-cli ping
```
Expected output: `PONG`

### 4. Configure the Project
Create a `.env` file in the project root to set environment variables:
```bash
touch .env
```
Add the following content, replacing placeholders with your values:
```
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
MAX_CONTENT_LENGTH=16777216  # 16MB
MODEL_PATH=/path/to/your/trained/model
LABEL_PATH=/path/to/your/label/encoder
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
DEBUG=True
```
- `MODEL_PATH`: Path to your pre-trained BERT model. (DOWNLOAD from teams group file shared by @ddrandy)
- `LABEL_PATH`: Path to your label encoder file (e.g., a pickled file for sentiment labels).
- Ensure the `uploads` and `outputs` directories exist or will be created by the app.

Update `utils/config.py` to load these variables using `python-dotenv`:
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER")
    OUTPUT_FOLDER = os.getenv("OUTPUT_FOLDER")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH"))
    MODEL_PATH = os.getenv("MODEL_PATH")
    LABEL_PATH = os.getenv("LABEL_PATH")
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")
    DEBUG = os.getenv("DEBUG") == "True"
```

### 5. Initialize the SQLite Database
The project uses SQLite to manage file metadata. The database (`file_records.db`) is initialized automatically when the `DBService` class is first instantiated. No manual setup is required beyond ensuring write permissions in the project directory.

## Building and Running the Project Locally

### 1. Start the Flask Application
Run the Flask app:
```bash
python app.py
```
The server will start at `http://localhost:5000`.

### 2. Start the Celery Worker
In a separate terminal, activate the virtual environment and start the Celery worker:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
celery -A services.classification.celery worker --loglevel=info
```
This processes tasks queued by the Flask app.

### 3. Test the API
- **Upload a File**: Use a tool like Postman or cURL:
  ```bash
  curl -X POST -F "file=@example.csv" http://localhost:5000/api/upload
  ```
- **Check Status**: Replace `<task_id>` with the returned ID:
  ```bash
  curl http://localhost:5000/api/task/<task_id>
  ```
- **Download File**: Use the URL from the status response:
  ```bash
  curl http://localhost:5000/api/download/<task_id> -o processed_file.csv
  ```

## Deploying to Production

### 1. Install Production Dependencies
Install Gunicorn for serving Flask in production:
```bash
pip install gunicorn
```

### 2. Run with Gunicorn
Deploy the Flask app with Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
- `-w 4`: Uses 4 worker processes (adjust based on CPU cores).
- `-b 0.0.0.0:8000`: Binds to port 8000 on all interfaces.

### 3. Configure a Reverse Proxy (e.g., Nginx)
Install Nginx:
```bash
sudo apt-get install nginx
```
Create an Nginx config file (e.g., `/etc/nginx/sites-available/your_project`):
```
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.0:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
Enable it and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/your_project /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Manage Processes with Supervisor
Install Supervisor:
```bash
sudo apt-get install supervisor
```
Create a config file (e.g., `/etc/supervisor/conf.d/your_project.conf`):
```
[program:your_project]
directory=/path/to/your_project
command=/path/to/your_project/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/your_project.err.log
stdout_logfile=/var/log/your_project.out.log

[program:your_project_celery]
directory=/path/to/your_project
command=/path/to/your_project/venv/bin/celery -A services.classification.celery worker --loglevel=info
autostart=true
autorestart=true
stderr_logfile=/var/log/your_project_celery.err.log
stdout_logfile=/var/log/your_project_celery.out.log
```
Update and start Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start your_project
sudo supervisorctl start your_project_celery
```

## Troubleshooting
- **Redis Not Running**: Ensure Redis is active (`redis-cli ping` should return `PONG`).
- **File Permissions**: Verify the app has write access to `uploads`, `outputs`, and the SQLite database file.
- **Missing Model**: Provide a valid `MODEL_PATH` and `LABEL_PATH` in `.env`.

## Contributing
Fork the repository, make changes, and submit a pull request. Ensure tests pass and adhere to PEP 8 style guidelines.

## License
This project is licensed under the MIT License.
