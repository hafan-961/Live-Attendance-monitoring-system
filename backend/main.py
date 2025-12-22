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
import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- INITIALIZE FLASK & CORS ---
app_flask = Flask(__name__)
# Crucial for React to communicate with Python
CORS(app_flask, resources={r"/*": {"origins": "*"}})

print("🔹 Starting Live Attendance Monitoring Backend...")

# --- EMAIL CONFIGURATION ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "dsr.lovely.professional@gmail.com"
SENDER_PASSWORD = "ysfm jnue jldj kdyv"  # Must be a 16-char Google App Password

# --- CONFIGURATION & PATHS ---
CAMERA_URL = "http://10.215.90.242:8080/video"
REGISTERED_FACES_DIR = "registered_faces"
EMBEDDINGS_FILE = "embeddings.pkl"
ATTENDANCE_LOG_FILE = "attendance_log.json"
STUDENT_DB_FILE = "students.json"

# --- TUNING ---
SIMILARITY_THRESHOLD = 0.60  
MIN_FACE_SIZE = 80 
ATTENDANCE_COOLDOWN_SECONDS = 30 
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# --- GLOBAL STATE ---
attendance_records = {} 
last_marked_time = {} 
global_frame = None
global_frame_lock = threading.Lock()
current_faces_data = [] 
faces_data_lock = threading.Lock()
student_db = {}
registered_embeddings = {}
registered_reg_nos = []
registered_embedding_vectors = np.array([])
embeddings_lock = threading.Lock()

# --- INSIGHTFACE INITIALIZATION ---
try:
    # Use ctx_id=0 for GPU (CUDA), -1 for CPU
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640)) 
    print("✅ InsightFace model loaded successfully.")
except Exception as e:
    print(f"❌ Error initializing InsightFace: {e}")
    exit()

# --- DATA MANAGEMENT ---
def load_data():
    global registered_embeddings, registered_reg_nos, registered_embedding_vectors, student_db
    
    # Load Student MetaData (Name, Email, etc.)
    if os.path.exists(STUDENT_DB_FILE):
        try:
            with open(STUDENT_DB_FILE, 'r') as f:
                student_db = json.load(f)
            print(f"✅ Loaded {len(student_db)} student records from JSON.")
        except: pass

    # Load Face Embeddings (Binary data)
    with embeddings_lock:
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        registered_embeddings = data
                        registered_reg_nos = list(data.keys())
                        registered_embedding_vectors = np.array(list(data.values()))
                        if registered_embedding_vectors.size > 0:
                            # Normalize vectors for faster cosine similarity via dot product
                            norms = np.linalg.norm(registered_embedding_vectors, axis=1, keepdims=True)
                            registered_embedding_vectors = registered_embedding_vectors / norms
                        print(f"✅ Loaded {len(data)} student embeddings.")
            except: pass

def save_student_db():
    with open(STUDENT_DB_FILE, 'w') as f:
        json.dump(student_db, f, indent=4)

load_data()

# --- EMAIL LOGIC ---
def send_email_thread(absent_students):
    """Background thread to send emails without freezing the app"""
    print(f"📧 Starting email broadcast to {len(absent_students)} absentees...")
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        
        for student in absent_students:
            email = student.get('email')
            name = student.get('name')
            reg_no = student.get('reg_no')

            if not email or "@" not in email:
                continue

            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL
            msg['To'] = email
            msg['Subject'] = f"Absence Alert: {name} ({reg_no})"

            body = f"Dear Parent,\n\nThis is to notify you that your ward, {name} (Reg No: {reg_no}), was marked ABSENT for the class session on {datetime.now().strftime('%Y-%m-%d')}.\n\nRegards,\nAttendance System"
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
            print(f"📤 Sent: {email}")

        server.quit()
        print("✅ Email notification session complete.")
    except Exception as e:
        print(f"❌ SMTP Error: {e}")

# --- BACKGROUND THREADS ---
def capture_thread_func():
    global global_frame
    cap = cv2.VideoCapture(CAMERA_URL)
    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_URL)
            continue
        with global_frame_lock:
            global_frame = frame.copy()
        time.sleep(0.01)

def processing_thread_func():
    global current_faces_data, attendance_records, last_marked_time
    while True:
        frame_to_process = None
        with global_frame_lock:
            if global_frame is not None: frame_to_process = global_frame.copy()
        
        if frame_to_process is None:
            time.sleep(0.1)
            continue

        faces = app.get(frame_to_process)
        processed_results = []
        current_time = time.time()
        
        if faces:
            for face in faces:
                bbox = face.bbox.astype(int)
                if (bbox[2]-bbox[0]) < MIN_FACE_SIZE: continue
                
                embedding = face.embedding
                norm = np.linalg.norm(embedding)
                if norm > 0: embedding = embedding / norm

                name, color, sim_score = "Unknown", (0, 0, 255), 0.0
                with embeddings_lock:
                    if registered_embedding_vectors.size > 0:
                        similarities = np.dot(registered_embedding_vectors, embedding)
                        best_idx = np.argmax(similarities)
                        if similarities[best_idx] > SIMILARITY_THRESHOLD:
                            name = registered_reg_nos[best_idx]
                            sim_score = similarities[best_idx]
                            color = (0, 255, 0)
                            
                            # Update Attendance Records
                            if name not in last_marked_time or (current_time - last_marked_time[name]) > ATTENDANCE_COOLDOWN_SECONDS:
                                attendance_records[name] = {'status': 'Present', 'timestamp': datetime.now().isoformat()}
                                last_marked_time[name] = current_time

                processed_results.append({"bbox": bbox, "name": name, "score": sim_score, "color": color})
        
        with faces_data_lock:
            current_faces_data = processed_results
        time.sleep(0.05)

# --- FLASK ROUTES ---

@app_flask.route('/video_feed')
def video_feed():
    """Live stream with Boxes (For Live Attendance Page)"""
    def generate():
        while True:
            frame = None
            with global_frame_lock:
                if global_frame is not None: frame = global_frame.copy()
            if frame is None: continue
            with faces_data_lock:
                for data in current_faces_data:
                    x1, y1, x2, y2 = data["bbox"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
                    label = f"{data['name']} ({int(data['score']*100)}%)" if data['name'] != "Unknown" else "Unknown"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, data["color"], 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/video_feed_clean')
def video_feed_clean():
    """Live stream WITHOUT Boxes (For Registration Page)"""
    def generate():
        while True:
            frame = None
            with global_frame_lock:
                if global_frame is not None: frame = global_frame.copy()
            if frame is None: continue
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/students', methods=['GET'])
def get_all_students():
    student_list = [{"register_no": k, **v} for k, v in student_db.items()]
    return jsonify(student_list)

@app_flask.route('/attendance_data')
def get_attendance_data(): 
    return jsonify(attendance_records)

@app_flask.route('/reset_attendance', methods=['POST'])
def reset_attendance():
    """Clears current attendance session from memory and log"""
    global attendance_records, last_marked_time
    try:
        attendance_records.clear()
        last_marked_time.clear()
        print("🗑️ Attendance list reset.")
        return jsonify({"status": "success", "message": "Attendance list reset."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/end_session_notify', methods=['POST'])
def end_session_notify():
    """Identifies absentees and triggers email thread"""
    global attendance_records, student_db
    try:
        present_ids = attendance_records.keys()
        absent_students = []

        for reg_no, info in student_db.items():
            if reg_no not in present_ids:
                data = info.copy()
                data['reg_no'] = reg_no
                absent_students.append(data)

        if not absent_students:
            return jsonify({"status": "success", "message": "Everyone is present."})

        # Start thread
        threading.Thread(target=send_email_thread, args=(absent_students,), daemon=True).start()
        
        return jsonify({"status": "success", "message": f"Session ended. {len(absent_students)} emails triggered."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/register', methods=['POST'])
def register_student():
    """Saves student image, info, and embedding"""
    global registered_reg_nos, registered_embedding_vectors
    if 'image' not in request.files: return jsonify({"status": "error", "message": "No image"}), 400
    file = request.files['image']
    reg_no, name = request.form.get('reg_no'), request.form.get('name')
    
    if not os.path.exists(REGISTERED_FACES_DIR): os.makedirs(REGISTERED_FACES_DIR)
    path = os.path.join(REGISTERED_FACES_DIR, f"{reg_no}.jpg")
    file.save(path)
    
    img = cv2.imread(path)
    faces = app.get(img)
    if not faces:
        os.remove(path)
        return jsonify({"status": "error", "message": "No face detected"}), 400
    
    faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
    embedding = faces[0].embedding
    norm = np.linalg.norm(embedding)
    if norm > 0: embedding = embedding / norm
    
    student_db[reg_no] = {
        "name": name, 
        "email": request.form.get('email'), 
        "roll_no": request.form.get('roll_no'), 
        "section": request.form.get('section')
    }
    save_student_db()
    
    with embeddings_lock:
        registered_embeddings[reg_no] = embedding
        registered_reg_nos = list(registered_embeddings.keys())
        registered_embedding_vectors = np.array(list(registered_embeddings.values()))
        with open(EMBEDDINGS_FILE, "wb") as f: pickle.dump(registered_embeddings, f)
        
    return jsonify({"status": "success", "message": f"Registered {name}!"})

@app_flask.route('/register_camera_frame')
def get_register_camera_frame():
    """Captures a single frame for registration snapshot"""
    frame = None
    with global_frame_lock:
        if global_frame is not None: frame = global_frame.copy()
    if frame is None: return jsonify({"error": "Loading..."}), 503
    ret, buffer = cv2.imencode('.jpg', frame)
    return jsonify({"content": base64.b64encode(buffer).decode('utf-8')})

if __name__ == '__main__':
    # Start Background Threads
    threading.Thread(target=capture_thread_func, daemon=True).start()
    threading.Thread(target=processing_thread_func, daemon=True).start()
    
    # Run Flask
    print(f"🌐 Server running at http://{FLASK_HOST}:{FLASK_PORT}")
    app_flask.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)