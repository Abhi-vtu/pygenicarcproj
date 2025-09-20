from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# --- MongoDB Atlas Connection ---
MONGO_URI = "mongodb+srv://abhisheksmd1_db_user:1FmphEPRE29GR8a6@cluster0.7fsrms0.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client["taskflow_db"]
    tasks_collection = db["tasks"]
    client.admin.command("ping")
    print("✅ Connected to MongoDB Atlas!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)


# --- Helper: Convert Mongo doc to JSON-safe dict ---
def task_to_json(task):
    created_at = task.get("created_at")
    if isinstance(created_at, datetime.datetime):
        created_at_str = created_at.strftime("%a, %d %b %Y %H:%M:%S GMT")
    else:
        created_at_str = task["_id"].generation_time.strftime("%a, %d %b %Y %H:%M:%S GMT")

    return {
        "id": str(task["_id"]),
        "title": task.get("title", ""),
        "description": task.get("description", ""),
        "status": task.get("status", "To Do"),
        "created_at": created_at_str,
    }


# --- Routes ---
@app.route("/", methods=["GET"])
def root():
    return jsonify({"message": "Welcome to TaskFlow API. Use /api/tasks"})


@app.route("/api", methods=["GET"])
def home():
    return jsonify({"message": "TaskFlow API running"})


@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    tasks = list(tasks_collection.find().sort("created_at", -1))
    return jsonify([task_to_json(t) for t in tasks])


@app.route("/api/tasks", methods=["POST"])
def add_task():
    data = request.json
    if not data.get("title"):
        return jsonify({"error": "Title required"}), 400
    new_task = {
        "title": data["title"],
        "description": data.get("description", ""),
        "status": data.get("status", "To Do"),
        "created_at": datetime.datetime.utcnow(),
    }
    result = tasks_collection.insert_one(new_task)
    new_task["_id"] = result.inserted_id
    return jsonify(task_to_json(new_task)), 201


@app.route("/api/tasks/<task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.json
    updates = {k: v for k, v in data.items() if k in ["title", "description", "status"]}
    if not updates:
        return jsonify({"error": "No data provided"}), 400

    result = tasks_collection.find_one_and_update(
        {"_id": ObjectId(task_id)},
        {"$set": updates},
        return_document=True
    )
    if not result:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task_to_json(result))


@app.route("/api/tasks/<task_id>", methods=["DELETE"])
def delete_task(task_id):
    result = tasks_collection.delete_one({"_id": ObjectId(task_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Task not found"}), 404
    return jsonify({"message": "Task deleted"}), 200


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
