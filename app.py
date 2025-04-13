from flask import Flask, request, jsonify, send_from_directory
from flasgger import Swagger
from flask_cors import CORS
from services.classification import ClassificationService, celery, classification_task
from utils.config import Config

app = Flask(__name__)
swagger = Swagger(app)
# enable cors
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
app.debug = Config.DEBUG

# init service
classification_service = ClassificationService()
file_service = classification_service.file_service


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """
    Upload a CSV file for sentiment analysis
    ---
    tags:
      - Upload
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: The CSV file to upload. Must contain a 'comment' column.
    responses:
      202:
        description: File uploaded successfully and processing task queued
        schema:
          type: object
          properties:
            task_id:
              type: string
              description: The ID of the processing task
      400:
        description: Error in upload request
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message (e.g., "No file part", "No selected file", "File must be a CSV")
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    if not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "File must be a CSV"}), 400

    try:
        unique_id, old_id = file_service.save_uploaded_file(file)
        if not old_id:
            task = classification_task.apply_async(args=[unique_id], task_id=unique_id)
        return jsonify({"task_id": unique_id}), 202
    except Exception as e:
        app.logger.error(f"error: {str(e)}")
        if app.debug:
            raise e
        else:
            return jsonify({"error": "Internal server error."}), 400


@app.route("/api/task/<id>", methods=["GET"])
def get_task_status(id):
    """
    Get the status of a processing task
    ---
    tags:
      - Task
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The ID of the task (returned from the upload endpoint)
    responses:
      200:
        description: Task status
        schema:
          type: object
          properties:
            status:
              type: string
              description: The status of the task (e.g., "Pending", "Processing", "Success")
            download_url:
              type: string
              description: The URL to download the processed file (if status is "Success")
      202:
        description: Task is still processing
        schema:
          type: object
          properties:
            status:
              type: string
              description: "Processing"
            current:
              type: integer
              description: Current progress of the task
            total:
              type: integer
              description: Total number of steps in the task
      404:
        description: Task not found
        schema:
          type: object
          properties:
            status:
              type: string
              description: "Invalid"
    """
    original_id = file_service.get_original_id(id)
    if not original_id:
        original_id = id
    state = file_service.get_state(original_id)
    if not state:
        return jsonify({"status": "Invalid"}), 404
    if state == "success":
        return (
            jsonify(
                {
                    "status": "Success",
                    "download_url": f"/api/download/{id}",
                }
            ),
            200,
        )
    elif state == "pending":
        return jsonify({"status": "Pending"}), 202
    task = classification_task.AsyncResult(original_id)
    if task.state == "PENDING":
        return jsonify({"status": "Pending"}), 202
    elif task.state == "PROCESSING":
        return (
            jsonify(
                {
                    "status": "Processing",
                    "current": task.info.get("current", 0),
                    "total": task.info.get("total", 0),
                }
            ),
            202,
        )
    else:
        result = {"status": str(task.state)}
        if app.debug:
            result["info"] = str(task.info)
        return jsonify(result), 202


@app.route("/api/download/<id>", methods=["GET"])
def download_file(id):
    """
    Download the processed CSV file
    ---
    tags:
      - Download
    parameters:
      - name: id
        in: path
        type: string
        required: true
        description: The ID of the processed file (from the task status endpoint)
    responses:
      200:
        description: The processed CSV file
        headers:
          Content-Disposition:
            type: string
            description: The filename of the downloaded file (e.g., "processed_original_filename.csv")
      404:
        description: File not found
        schema:
          type: object
          properties:
            error:
              type: string
              description: "File not found"
    """
    original_filename = file_service.get_original_filename(id)
    if not original_filename:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(
        Config.OUTPUT_FOLDER,
        file_service.get_hash(id),
        as_attachment=True,
        download_name=f"processed_{original_filename}",
    )


if __name__ == "__main__":
    app.run()
