from flask import Flask, request, jsonify, send_from_directory, render_template
from services.classification import ClassificationService, celery, classify_comments
from utils.config import Config
import os, uuid
from pathlib import Path


app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH

# init service
classification_service = ClassificationService()
file_service = classification_service.file_service


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        file_path, unique_id = file_service.save_uploaded_file(file)
        task = classify_comments.delay(unique_id, file.filename)
        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        app.logger.error(f"error: {str(e)}")
        if app.debug:
            raise e
        else:
            return jsonify({"error": "Internal server error."}), 400


@app.route("/api/task/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task = classify_comments.AsyncResult(task_id)
    if task.state == "PENDING":
        return jsonify({"status": "Pending"}), 202
    elif task.state == "SUCCESS":
        return (
            jsonify(
                {"status": "Success", "download_url": f"/api/download/{task.result}"}
            ),
            200,
        )
    else:
        return jsonify({"status": task.state}), 500


@app.route("/api/download/<filename>", methods=["GET"])
def download_file(filename):
    original_filename = file_service.get_original_filename(filename)
    if not original_filename:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(
        Config.OUTPUT_FOLDER,
        filename,
        as_attachment=True,
        download_name=f"processed_{original_filename}",
    )


if __name__ == "__main__":
    app.run(debug=True)
