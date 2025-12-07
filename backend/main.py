import cv2
import pickle
import numpy as np
from insightface.app import FaceAnalysis
import time
import os
import json
from datetime import datetime
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
import threading
import queue
import base64 # Added for base64 encoding frames

print("🔹 Starting Live Attendance Monitoring Backend...")

# --- Configuration ---
CAMERA_URL = "http://10.216.185.30:8080/video" # Your camera URL
REGISTERED_FACES_DIR = "registered_faces" # Must match generate_embeddings.py
EMBEDDINGS_FILE = "embeddings.pkl"
ATTENDANCE_LOG_FILE = "attendance_log.json"
RECOGNITION_THRESHOLD = 0.35 # Cosine distance threshold (lower means more similar)
ATTENDANCE_COOLDOWN_SECONDS = 10 # Mark attendance for a student only once every X seconds
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# --- Global Variables for Attendance and Video Stream ---
attendance_records = {} # {reg_no: {'status': 'Present', 'timestamp': '...'}}
last_marked_time = {} # {reg_no: timestamp_of_last_mark}
frame_queue = queue.Queue(maxsize=1) # Queue to hold the latest PROCESSED frame for LiveAttendance.js
latest_raw_frame = None # Stores the latest RAW frame for RegisterStudent.js
raw_frame_lock = threading.Lock() # Lock for accessing latest_raw_frame

# --- InsightFace Initialization ---
try:
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640))
    print("✅ InsightFace model loaded successfully.")
except Exception as e:
    print(f"❌ Error initializing InsightFace: {e}")
    print("Please ensure InsightFace is installed and models are downloaded.")
    exit()

# --- Embeddings Management ---
registered_embeddings = {}
registered_reg_nos = []
registered_embedding_vectors = np.array([])
embeddings_lock = threading.Lock() # To prevent race conditions when updating embeddings

def load_registered_embeddings():
    global registered_embeddings, registered_reg_nos, registered_embedding_vectors
    with embeddings_lock:
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, "rb") as f:
                    loaded_data = pickle.load(f)
                if isinstance(loaded_data, dict):
                    registered_embeddings = loaded_data
                    registered_reg_nos = list(registered_embeddings.keys())
                    registered_embedding_vectors = np.array(list(registered_embeddings.values()))
                    print(f"✅ Loaded {len(registered_embeddings)} registered student embeddings.")
                else:
                    print(f"❌ Error: '{EMBEDDINGS_FILE}' contains data of type {type(loaded_data)}, expected dict.")
                    registered_embeddings = {}
                    registered_reg_nos = []
                    registered_embedding_vectors = np.array([])
            except Exception as e:
                print(f"❌ Error loading '{EMBEDDINGS_FILE}': {e}")
                registered_embeddings = {}
                registered_reg_nos = []
                registered_embedding_vectors = np.array([])
        else:
            print(f"❌ '{EMBEDDINGS_FILE}' not found. Recognition will not work until embeddings are generated.")
            registered_embeddings = {}
            registered_reg_nos = []
            registered_embedding_vectors = np.array([])

# Load embeddings at startup
load_registered_embeddings()

# --- Attendance Logging Functions ---
def load_attendance_log():
    global attendance_records
    if os.path.exists(ATTENDANCE_LOG_FILE):
        with open(ATTENDANCE_LOG_FILE, 'r') as f:
            attendance_records = json.load(f)
        print(f"✅ Loaded existing attendance log from {ATTENDANCE_LOG_FILE}")
    else:
        print(f"ℹ️ No existing attendance log found at {ATTENDANCE_LOG_FILE}. Starting fresh.")

def save_attendance_log():
    with open(ATTENDANCE_LOG_FILE, 'w') as f:
        json.dump(attendance_records, f, indent=4)

# --- Camera Processing Thread ---
def camera_processing_thread():
    global attendance_records, last_marked_time, latest_raw_frame

    cap = cv2.VideoCapture(CAMERA_URL)
    if not cap.isOpened():
        print(f"❌ [Camera Thread] Could not connect to camera at {CAMERA_URL}!")
        return

    print("🟢 [Camera Thread] Starting live attendance monitoring.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ [Camera Thread] Could not read frame from camera. Attempting to reconnect...")
            cap.release()
            cap = cv2.VideoCapture(CAMERA_URL)
            if not cap.isOpened():
                print("❌ [Camera Thread] Failed to reconnect to camera. Exiting camera thread.")
                break
            time.sleep(1)
            continue

        # Store the raw frame for the registration endpoint
        with raw_frame_lock:
            latest_raw_frame = frame.copy() # Store a copy

        display_frame = frame.copy()
        current_time = time.time()

        faces = app.get(frame)

        if faces:
            for face in faces:
                bbox = face.bbox.astype(int)
                current_embedding = face.embedding

                with embeddings_lock: # Acquire lock before accessing shared embeddings
                    if registered_embedding_vectors.size > 0:
                        similarities = np.dot(registered_embedding_vectors, current_embedding)
                        best_match_idx = np.argmax(similarities)
                        best_similarity = similarities[best_match_idx]
                        best_distance = 1 - best_similarity

                        matched_reg_no = registered_reg_nos[best_match_idx]

                        if best_distance < RECOGNITION_THRESHOLD:
                            if matched_reg_no not in last_marked_time or \
                               (current_time - last_marked_time[matched_reg_no]) > ATTENDANCE_COOLDOWN_SECONDS:

                                attendance_records[matched_reg_no] = {
                                    'status': 'Present',
                                    'timestamp': datetime.now().isoformat()
                                }
                                last_marked_time[matched_reg_no] = current_time
                                save_attendance_log()
                                print(f"✅ Attendance marked for {matched_reg_no} at {datetime.now().strftime('%H:%M:%S')}")

                            cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                            cv2.putText(display_frame, f"{matched_reg_no} ({best_similarity:.2f})", (bbox[0], bbox[1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                        else:
                            cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
                            cv2.putText(display_frame, "Unknown", (bbox[0], bbox[1] - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
                    else:
                        cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
                        cv2.putText(display_frame, "No Registered Faces", (bbox[0], bbox[1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(display_frame, "No Face Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

        try:
            frame_queue.put_nowait(display_frame)
        except queue.Full:
            pass

    cap.release()
    cv2.destroyAllWindows()
    save_attendance_log()
    print("🔴 [Camera Thread] Camera processing thread terminated.")

# --- Flask Application Setup ---
app_flask = Flask(__name__)
CORS(app_flask)

def generate_frames():
    while True:
        try:
            frame = frame_queue.get()
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        except Exception as e:
            print(f"❌ Error in video frame generation: {e}")
            time.sleep(0.1)

@app_flask.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/attendance_data')
def get_attendance_data():
    return jsonify(attendance_records.copy())

# --- NEW: Endpoint for RegisterStudent.js to get a single camera frame (proxied) ---
@app_flask.route('/register_camera_frame')
def get_register_camera_frame():
    with raw_frame_lock:
        if latest_raw_frame is None:
            return jsonify({"error": "Camera not ready or no frame captured yet"}), 503

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', latest_raw_frame)
        if not ret:
            return jsonify({"error": "Could not encode frame to JPEG"}), 500

        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        return jsonify({"content": frame_base64})

# --- Endpoint for RegisterStudent.js to register students ---
@app_flask.route('/register', methods=['POST'])
def register_student():
    if 'image' not in request.files:
        return jsonify({"status": "error", "message": "No image file provided"}), 400

    image_file = request.files['image']
    name = request.form.get('name')
    reg_no = request.form.get('reg_no')
    roll_no = request.form.get('roll_no')
    section = request.form.get('section')

    if not all([name, reg_no, roll_no, section, image_file]):
        return jsonify({"status": "error", "message": "Missing required student details"}), 400

    safe_reg_no = "".join(c for c in reg_no if c.isalnum() or c in ('-', '_')).strip()
    if not safe_reg_no:
        return jsonify({"status": "error", "message": "Invalid Register Number for filename"}), 400

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{safe_reg_no}_{timestamp}.jpg"
    save_path = os.path.join(REGISTERED_FACES_DIR, filename)

    try:
        image_file.save(save_path)
        print(f"✅ Saved new registration image: {save_path}")

        img = cv2.imread(save_path)
        if img is None:
            return jsonify({"status": "error", "message": "Failed to read saved image"}), 500

        faces = app.get(img)
        if faces:
            new_embedding = faces[0].embedding
            with embeddings_lock:
                registered_embeddings[reg_no] = new_embedding
                global registered_reg_nos, registered_embedding_vectors
                registered_reg_nos = list(registered_embeddings.keys())
                registered_embedding_vectors = np.array(list(registered_embeddings.values()))

                with open(EMBEDDINGS_FILE, "wb") as f:
                    pickle.dump(registered_embeddings, f)
                print(f"✅ Updated embeddings.pkl with new student {reg_no}.")
            return jsonify({"status": "success", "message": f"Student {name} ({reg_no}) registered and embeddings updated!"})
        else:
            os.remove(save_path)
            return jsonify({"status": "error", "message": "No face detected in the uploaded image. Registration failed."}), 400

    except Exception as e:
        print(f"❌ Error during registration: {e}")
        return jsonify({"status": "error", "message": f"Server error during registration: {e}"}), 500

@app_flask.route('/')
def index():
    return "Live Attendance Backend is running. Access /video_feed for stream, /attendance_data for JSON, /register_camera_frame for registration camera, and /register for student registration."

# --- Main Execution ---
if __name__ == '__main__':
    load_attendance_log()

    camera_thread = threading.Thread(target=camera_processing_thread, daemon=True)
    camera_thread.start()
    print(f"✅ Camera processing thread started.")

    print(f"🌐 Flask server starting on http://{FLASK_HOST}:{FLASK_PORT}")
    app_flask.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)