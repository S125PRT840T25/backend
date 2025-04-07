from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
from services.classification import ClassificationService, celery, classification_task
from utils.config import Config

app = Flask(__name__)
# enable cors
CORS(app)
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
        task = classification_task.apply_async(args=[unique_id], task_id=unique_id)
        return jsonify({"task_id": task.id}), 202
    except Exception as e:
        app.logger.error(f"error: {str(e)}")
        if app.debug:
            raise e
        else:
            return jsonify({"error": "Internal server error."}), 400


@app.route("/api/task/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task = classification_task.AsyncResult(task_id)
    if task.state == "PENDING":
        return jsonify({"status": "Pending"}), 202
    elif task.state == "SUCCESS":
        return (
            jsonify(
                {
                    "task_id": task_id,
                    "status": "Success",
                    "download_url": f"/api/download/{task.result}",
                }
            ),
            200,
        )
    else:
        return jsonify({"status": task.state}), 500


@app.route("/api/download/<id>", methods=["GET"])
def download_file(id):
    original_filename = file_service.get_original_filename(id)
    if not original_filename:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory(
        Config.OUTPUT_FOLDER,
        id,
        as_attachment=True,
        download_name=f"processed_{original_filename}",
    )


if __name__ == "__main__":
    app.run(debug=Config.DEBUG)
