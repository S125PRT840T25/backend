from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from services.classification import ClassificationService, celery, classification_task
from utils.config import Config

app = Flask(__name__)
# enable cors
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_CONTENT_LENGTH
app.debug = Config.DEBUG

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
