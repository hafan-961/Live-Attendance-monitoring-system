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
from collections import deque
from deepface import DeepFace 
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

#stop TensorFlow logs
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' 

app_flask = Flask(__name__)
CORS(app_flask, resources={r"/*": {"origins": "*"}}, methods=["GET", "POST", "DELETE", "OPTIONS"])

# CONFIGURATION
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "dsr.lovely.professional@gmail.com"
SENDER_PASSWORD = "ysfmjnuejldjkdyv" 

#IMPORTANT: Update this IP if your phone IP changes
CAMERA_URL = "http://10.172.11.157:8080/video" 

REGISTERED_FACES_DIR = "registered_faces"
EMBEDDINGS_FILE = "embeddings.pkl"
STUDENT_DB_FILE = "students.json"
HISTORY_FILE = "attendance_history.json"
SIMILARITY_THRESHOLD = 0.60  
FLASK_PORT = 5050 

# GLOBAL STATE 
is_session_active = False 
attendance_records = {} 
last_marked_time = {} 
global_frame = None
global_frame_lock = threading.Lock()
current_faces_data = [] 
faces_data_lock = threading.Lock()
sentiment_history = deque(maxlen=40) 
class_sentiment = {"rating": "Initializing...", "score": 0, "count": 0}

student_db = {}
registered_embeddings = {}
registered_reg_nos = []
registered_embedding_vectors = np.array([])
embeddings_lock = threading.Lock()

def load_data_from_disk():
    global registered_embeddings, registered_reg_nos, registered_embedding_vectors, student_db
    if os.path.exists(STUDENT_DB_FILE):
        try:
            with open(STUDENT_DB_FILE, 'r') as f: student_db = json.load(f)
        except: pass
    if os.path.exists(EMBEDDINGS_FILE):
        try:
            with open(EMBEDDINGS_FILE, "rb") as f:
                registered_embeddings = pickle.load(f)
                registered_reg_nos = list(registered_embeddings.keys())
                vectors = np.array(list(registered_embeddings.values()))
                if vectors.size > 0:
                    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
                    registered_embedding_vectors = vectors / norms
                else:
                    registered_embedding_vectors = np.array([])
        except: pass

load_data_from_disk()

def send_email_thread(absent_students):
    print(f"📧 Sending {len(absent_students)} emails...")
    context = ssl._create_unverified_context()
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls(context=context)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        for student in absent_students:
            dest = student.get('email')
            if not dest or "@" not in dest: continue
            msg = MIMEMultipart()
            msg['From'] = SENDER_EMAIL; msg['To'] = dest; msg['Subject'] = f"Absence Alert: {student.get('name')}"
            body = f"Dear Parent, your ward {student.get('name')} was absent for today's session."
            msg.attach(MIMEText(body, 'plain'))
            server.send_message(msg)
        server.quit()
    except Exception as e: print(f"Email Error: {e}")

try:
    app = FaceAnalysis(name='buffalo_l', providers=['CoreMLExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=-1, det_size=(640, 640)) 
    print("AI Engine Ready.")
except Exception as e:
    sys.exit(1)

def processing_thread_func():
    global current_faces_data, attendance_records, last_marked_time, class_sentiment, is_session_active
    while True:
        frame_to_process = None
        with global_frame_lock:
            if global_frame is not None: frame_to_process = global_frame.copy()
        if frame_to_process is None: time.sleep(0.1); continue

        try:
            faces = app.get(frame_to_process)
            processed_results = []
            frame_vibe_scores = []
            if faces:
                for face in faces:
                    bbox = face.bbox.astype(int)
                    x1, y1, x2, y2 = [max(0, c) for c in bbox]
                    emotion_label, score = "Focused", 70
                    try:
                        face_img = frame_to_process[y1:y2, x1:x2]
                        if face_img.size > 0:
                            res = DeepFace.analyze(face_img, actions=['emotion'], enforce_detection=False, detector_backend='skip', silent=True)
                            emo = res[0]['dominant_emotion']
                            mapping = {'happy': (100, "Satisfied 😊"), 'surprise': (85, "Interested 🤩"), 'neutral': (70, "Focused 😐"), 'sad': (40, "Bored 🥱"), 'angry': (20, "Confused 😖")}
                            score, emotion_label = mapping.get(emo, (70, "Focused"))
                            frame_vibe_scores.append(score)
                    except: pass 

                    embedding = face.embedding / np.linalg.norm(face.embedding)
                    name, color = "Unknown", (0, 0, 255)
                    with embeddings_lock:
                        if registered_embedding_vectors.size > 0:
                            sims = np.dot(registered_embedding_vectors, embedding)
                            idx = np.argmax(sims)
                            if sims[idx] > SIMILARITY_THRESHOLD:
                                name = registered_reg_nos[idx]; color = (0, 255, 0)
                                if is_session_active:
                                    if name in attendance_records:
                                        attendance_records[name]['emotion'] = emotion_label
                                    elif name not in last_marked_time or (time.time() - last_marked_time[name]) > 30:
                                        attendance_records[name] = {'status': 'Present', 'timestamp': datetime.now().isoformat(), 'emotion': emotion_label}
                                        last_marked_time[name] = time.time()
                    processed_results.append({"bbox": [x1,y1,x2,y2], "name": name, "color": color, "emotion": emotion_label})
            
            if frame_vibe_scores:
                avg = sum(frame_vibe_scores) / len(frame_vibe_scores)
                sentiment_history.append(avg); smoothed = sum(sentiment_history) / len(sentiment_history)
                class_sentiment = {"rating": "Excellent" if smoothed > 80 else "Focused" if smoothed > 60 else "Bored", "score": int(smoothed), "count": len(faces)}
            
            with faces_data_lock: current_faces_data = processed_results
        except: pass
        time.sleep(0.02)

@app_flask.route('/start_session', methods=['POST'])
def start_session():
    global is_session_active; is_session_active = True
    attendance_records.clear(); last_marked_time.clear()
    return jsonify({"status": "success"})

@app_flask.route('/end_session_notify', methods=['POST'])
def end_session_notify():
    global is_session_active
    try:
        present_ids = [str(k) for k in attendance_records.keys()]
        absent_list = []; present_list = []
        for reg_no, info in student_db.items():
            data = {**info, "reg_no": reg_no}
            if str(reg_no) in present_ids:
                data['final_emotion'] = attendance_records[str(reg_no)].get('emotion', 'Focused')
                present_list.append(data)
            else: absent_list.append(data)
        
        session_record = {"session_id": datetime.now().strftime("%Y%m%d_%H%M%S"), "date": datetime.now().strftime("%Y-%m-%d"), "time": datetime.now().strftime("%I:%M %p"), "present_count": len(present_list), "absent_count": len(absent_list), "present_list": present_list, "absent_list": absent_list}
        history = []
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f: history = json.load(f)
        history.insert(0, session_record)
        with open(HISTORY_FILE, 'w') as f: json.dump(history, f, indent=4)
        
        if absent_list: threading.Thread(target=send_email_thread, args=(absent_list,), daemon=True).start()
        is_session_active = False; attendance_records.clear(); last_marked_time.clear()
        return jsonify({"status": "success", "message": "Session Saved and Emails Triggered."})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/get_history', methods=['GET'])
def get_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f: return jsonify(json.load(f))
    return jsonify([])

@app_flask.route('/delete_student/<reg_no>', methods=['DELETE'])
def delete_student(reg_no):
    global student_db
    try:
        reg_no = str(reg_no)
        if reg_no in student_db:
            del student_db[reg_no]
            with open(STUDENT_DB_FILE, 'w') as f: json.dump(student_db, f, indent=4)
        if os.path.exists(EMBEDDINGS_FILE):
            with open(EMBEDDINGS_FILE, "rb") as f: embeddings = pickle.load(f)
            if reg_no in embeddings:
                del embeddings[reg_no]
                with open(EMBEDDINGS_FILE, "wb") as f: pickle.dump(embeddings, f)
        load_data_from_disk()
        img_path = os.path.join(REGISTERED_FACES_DIR, f"{reg_no}.jpg")
        if os.path.exists(img_path): os.remove(img_path)
        return jsonify({"status": "success"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = None
            with global_frame_lock:
                if global_frame is not None: frame = global_frame.copy()
            if frame is None: time.sleep(0.1); continue
            with faces_data_lock:
                for d in current_faces_data:
                    x1, y1, x2, y2 = d["bbox"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), d["color"], 2)
                    cv2.putText(frame, f"{d['name']} | {d['emotion']}", (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, d["color"], 2)
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/video_feed_clean')
def video_feed_clean():
    def generate():
        while True:
            frame = None
            with global_frame_lock:
                if global_frame is not None: frame = global_frame.copy()
            if frame is None: time.sleep(0.1); continue
            ret, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
            time.sleep(0.03)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/attendance_data')
def get_att(): return jsonify(attendance_records)

@app_flask.route('/class_sentiment')
def get_sent(): return jsonify(class_sentiment)

@app_flask.route('/students')
def get_stu(): return jsonify([{"register_no": k, **v} for k, v in student_db.items()])

@app_flask.route('/register', methods=['POST'])
def register():
    try:
        reg_no, name = request.form.get('reg_no'), request.form.get('name')
        file = request.files['image']
        path = os.path.join(REGISTERED_FACES_DIR, f"{reg_no}.jpg")
        file.save(path)
        img = cv2.imread(path); faces = app.get(img)
        if not faces: return jsonify({"status": "error", "message": "No face found"}), 400
        student_db[reg_no] = {"name": name, "email": request.form.get('email'), "roll_no": request.form.get('roll_no'), "section": request.form.get('section')}
        with open(STUDENT_DB_FILE, 'w') as f: json.dump(student_db, f, indent=4)
        with embeddings_lock:
            temp = {}
            if os.path.exists(EMBEDDINGS_FILE):
                with open(EMBEDDINGS_FILE, "rb") as f: temp = pickle.load(f)
            temp[reg_no] = faces[0].embedding
            with open(EMBEDDINGS_FILE, "wb") as f: pickle.dump(temp, f)
            load_data_from_disk()
        return jsonify({"status": "success", "message": f"Registered {name}!"})
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app_flask.route('/register_camera_frame')
def get_register_camera_frame():
    frame = None
    with global_frame_lock:
        if global_frame is not None: frame = global_frame.copy()
    if frame is None: return jsonify({"error": "Loading..."}), 503
    ret, buffer = cv2.imencode('.jpg', frame)
    return jsonify({"content": base64.b64encode(buffer).decode('utf-8')})

@app_flask.route('/reset_attendance', methods=['POST'])
def reset():
    global is_session_active
    is_session_active = False
    attendance_records.clear(); last_marked_time.clear()
    return jsonify({"status": "success"})

if __name__ == '__main__':
    def cap_loop():
        global global_frame
        cap = cv2.VideoCapture(CAMERA_URL)
        while True:
            ret, frame = cap.read()
            if ret:
                with global_frame_lock: global_frame = frame.copy()
            else: time.sleep(2); cap = cv2.VideoCapture(CAMERA_URL)
    threading.Thread(target=cap_loop, daemon=True).start()
    threading.Thread(target=processing_thread_func, daemon=True).start()
    app_flask.run(host='127.0.0.1', port=5050, threaded=True, debug=False)
