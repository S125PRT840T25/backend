from flask import Flask, request, send_file, render_template
from services.classification import ClassificationService
from utils.config import Config
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

# init service
classification_service = ClassificationService(
    Config.UPLOAD_FOLDER,
    Config.OUTPUT_FOLDER
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if not file.filename.lower().endswith('.csv'):
        return 'File must be a CSV', 400

    try:
        output_path = classification_service.classify_comments(file)
        return f"File classified successfully. Download from <a href=\"/download/{os.path.basename(output_path)}\">here</a>.", 200
    except Exception as e:
        print(e)
        raise e
        return f"Error: {str(e)}", 400

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(Config.OUTPUT_FOLDER, filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
