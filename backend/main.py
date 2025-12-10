# import cv2
# import pickle
# import numpy as np
# from insightface.app import FaceAnalysis
# import time
# import os
# import json
# from datetime import datetime
# from flask import Flask, Response, jsonify, request
# from flask_cors import CORS
# import threading
# import queue
# import base64 # Added for base64 encoding frames

# print("🔹 Starting Live Attendance Monitoring Backend...")

# # --- Configuration ---
# CAMERA_URL = "http://10.172.140.210:8080/video" # Your camera URL
# REGISTERED_FACES_DIR = "registered_faces" # Must match generate_embeddings.py
# EMBEDDINGS_FILE = "embeddings.pkl"
# ATTENDANCE_LOG_FILE = "attendance_log.json"
# RECOGNITION_THRESHOLD = 0.35 # Cosine distance threshold (lower means more similar)
# ATTENDANCE_COOLDOWN_SECONDS = 10 # Mark attendance for a student only once every X seconds
# FLASK_HOST = '0.0.0.0'
# FLASK_PORT = 5000

# # --- Global Variables for Attendance and Video Stream ---
# attendance_records = {} # {reg_no: {'status': 'Present', 'timestamp': '...'}}
# last_marked_time = {} # {reg_no: timestamp_of_last_mark}
# frame_queue = queue.Queue(maxsize=1) # Queue to hold the latest PROCESSED frame for LiveAttendance.js
# latest_raw_frame = None # Stores the latest RAW frame for RegisterStudent.js
# raw_frame_lock = threading.Lock() # Lock for accessing latest_raw_frame

# # --- InsightFace Initialization ---
# try:
#     app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
#     app.prepare(ctx_id=0, det_size=(640, 640))
#     print("✅ InsightFace model loaded successfully.")
# except Exception as e:
#     print(f"❌ Error initializing InsightFace: {e}")
#     print("Please ensure InsightFace is installed and models are downloaded.")
#     exit()

# # --- Embeddings Management ---
# registered_embeddings = {}
# registered_reg_nos = []
# registered_embedding_vectors = np.array([])
# embeddings_lock = threading.Lock() # To prevent race conditions when updating embeddings

# def load_registered_embeddings():
#     global registered_embeddings, registered_reg_nos, registered_embedding_vectors
#     with embeddings_lock:
#         if os.path.exists(EMBEDDINGS_FILE):
#             try:
#                 with open(EMBEDDINGS_FILE, "rb") as f:
#                     loaded_data = pickle.load(f)
#                 if isinstance(loaded_data, dict):
#                     registered_embeddings = loaded_data
#                     registered_reg_nos = list(registered_embeddings.keys())
#                     registered_embedding_vectors = np.array(list(registered_embeddings.values()))
#                     print(f"✅ Loaded {len(registered_embeddings)} registered student embeddings.")
#                 else:
#                     print(f"❌ Error: '{EMBEDDINGS_FILE}' contains data of type {type(loaded_data)}, expected dict.")
#                     registered_embeddings = {}
#                     registered_reg_nos = []
#                     registered_embedding_vectors = np.array([])
#             except Exception as e:
#                 print(f"❌ Error loading '{EMBEDDINGS_FILE}': {e}")
#                 registered_embeddings = {}
#                 registered_reg_nos = []
#                 registered_embedding_vectors = np.array([])
#         else:
#             print(f"❌ '{EMBEDDINGS_FILE}' not found. Recognition will not work until embeddings are generated.")
#             registered_embeddings = {}
#             registered_reg_nos = []
#             registered_embedding_vectors = np.array([])

# # Load embeddings at startup
# load_registered_embeddings()

# # --- Attendance Logging Functions ---
# def load_attendance_log():
#     global attendance_records
#     if os.path.exists(ATTENDANCE_LOG_FILE):
#         with open(ATTENDANCE_LOG_FILE, 'r') as f:
#             attendance_records = json.load(f)
#         print(f"✅ Loaded existing attendance log from {ATTENDANCE_LOG_FILE}")
#     else:
#         print(f"ℹ️ No existing attendance log found at {ATTENDANCE_LOG_FILE}. Starting fresh.")

# def save_attendance_log():
#     with open(ATTENDANCE_LOG_FILE, 'w') as f:
#         json.dump(attendance_records, f, indent=4)

# # --- Camera Processing Thread ---
# def camera_processing_thread():
#     global attendance_records, last_marked_time, latest_raw_frame

#     cap = cv2.VideoCapture(CAMERA_URL)
#     if not cap.isOpened():
#         print(f"❌ [Camera Thread] Could not connect to camera at {CAMERA_URL}!")
#         return

#     print("🟢 [Camera Thread] Starting live attendance monitoring.")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("❌ [Camera Thread] Could not read frame from camera. Attempting to reconnect...")
#             cap.release()
#             cap = cv2.VideoCapture(CAMERA_URL)
#             if not cap.isOpened():
#                 print("❌ [Camera Thread] Failed to reconnect to camera. Exiting camera thread.")
#                 break
#             time.sleep(1)
#             continue

#         # Store the raw frame for the registration endpoint
#         with raw_frame_lock:
#             latest_raw_frame = frame.copy() # Store a copy

#         display_frame = frame.copy()
#         current_time = time.time()

#         faces = app.get(frame)

#         if faces:
#             for face in faces:
#                 bbox = face.bbox.astype(int)
#                 current_embedding = face.embedding

#                 with embeddings_lock: # Acquire lock before accessing shared embeddings
#                     if registered_embedding_vectors.size > 0:
#                         similarities = np.dot(registered_embedding_vectors, current_embedding)
#                         best_match_idx = np.argmax(similarities)
#                         best_similarity = similarities[best_match_idx]
#                         best_distance = 1 - best_similarity

#                         matched_reg_no = registered_reg_nos[best_match_idx]

#                         if best_distance < RECOGNITION_THRESHOLD:
#                             if matched_reg_no not in last_marked_time or \
#                                (current_time - last_marked_time[matched_reg_no]) > ATTENDANCE_COOLDOWN_SECONDS:

#                                 attendance_records[matched_reg_no] = {
#                                     'status': 'Present',
#                                     'timestamp': datetime.now().isoformat()
#                                 }
#                                 last_marked_time[matched_reg_no] = current_time
#                                 save_attendance_log()
#                                 print(f"✅ Attendance marked for {matched_reg_no} at {datetime.now().strftime('%H:%M:%S')}")

#                             cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
#                             cv2.putText(display_frame, f"{matched_reg_no} ({best_similarity:.2f})", (bbox[0], bbox[1] - 10),
#                                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
#                         else:
#                             cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
#                             cv2.putText(display_frame, "Unknown", (bbox[0], bbox[1] - 10),
#                                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
#                     else:
#                         cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
#                         cv2.putText(display_frame, "No Registered Faces", (bbox[0], bbox[1] - 10),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2, cv2.LINE_AA)
#         else:
#             cv2.putText(display_frame, "No Face Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)

#         try:
#             frame_queue.put_nowait(display_frame)
#         except queue.Full:
#             pass

#     cap.release()
#     cv2.destroyAllWindows()
#     save_attendance_log()
#     print("🔴 [Camera Thread] Camera processing thread terminated.")

# # --- Flask Application Setup ---
# app_flask = Flask(__name__)
# CORS(app_flask)

# def generate_frames():
#     while True:
#         try:
#             frame = frame_queue.get()
#             ret, buffer = cv2.imencode('.jpg', frame)
#             if not ret:
#                 continue
#             frame_bytes = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
#         except Exception as e:
#             print(f"❌ Error in video frame generation: {e}")
#             time.sleep(0.1)

# @app_flask.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app_flask.route('/attendance_data')
# def get_attendance_data():
#     return jsonify(attendance_records.copy())

# # --- NEW: Endpoint for RegisterStudent.js to get a single camera frame (proxied) ---
# @app_flask.route('/register_camera_frame')
# def get_register_camera_frame():
#     with raw_frame_lock:
#         if latest_raw_frame is None:
#             return jsonify({"error": "Camera not ready or no frame captured yet"}), 503

#         # Encode frame as JPEG
#         ret, buffer = cv2.imencode('.jpg', latest_raw_frame)
#         if not ret:
#             return jsonify({"error": "Could not encode frame to JPEG"}), 500

#         frame_base64 = base64.b64encode(buffer).decode('utf-8')
#         return jsonify({"content": frame_base64})

# # --- Endpoint for RegisterStudent.js to register students ---
# @app_flask.route('/register', methods=['POST'])
# def register_student():
#     if 'image' not in request.files:
#         return jsonify({"status": "error", "message": "No image file provided"}), 400

#     image_file = request.files['image']
#     name = request.form.get('name')
#     reg_no = request.form.get('reg_no')
#     roll_no = request.form.get('roll_no')
#     section = request.form.get('section')

#     if not all([name, reg_no, roll_no, section, image_file]):
#         return jsonify({"status": "error", "message": "Missing required student details"}), 400

#     safe_reg_no = "".join(c for c in reg_no if c.isalnum() or c in ('-', '_')).strip()
#     if not safe_reg_no:
#         return jsonify({"status": "error", "message": "Invalid Register Number for filename"}), 400

#     timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
#     filename = f"{safe_reg_no}_{timestamp}.jpg"
#     save_path = os.path.join(REGISTERED_FACES_DIR, filename)

#     try:
#         image_file.save(save_path)
#         print(f"✅ Saved new registration image: {save_path}")

#         img = cv2.imread(save_path)
#         if img is None:
#             return jsonify({"status": "error", "message": "Failed to read saved image"}), 500

#         faces = app.get(img)
#         if faces:
#             new_embedding = faces[0].embedding
#             with embeddings_lock:
#                 registered_embeddings[reg_no] = new_embedding
#                 global registered_reg_nos, registered_embedding_vectors
#                 registered_reg_nos = list(registered_embeddings.keys())
#                 registered_embedding_vectors = np.array(list(registered_embeddings.values()))

#                 with open(EMBEDDINGS_FILE, "wb") as f:
#                     pickle.dump(registered_embeddings, f)
#                 print(f"✅ Updated embeddings.pkl with new student {reg_no}.")
#             return jsonify({"status": "success", "message": f"Student {name} ({reg_no}) registered and embeddings updated!"})
#         else:
#             os.remove(save_path)
#             return jsonify({"status": "error", "message": "No face detected in the uploaded image. Registration failed."}), 400

#     except Exception as e:
#         print(f"❌ Error during registration: {e}")
#         return jsonify({"status": "error", "message": f"Server error during registration: {e}"}), 500

# @app_flask.route('/')
# def index():
#     return "Live Attendance Backend is running. Access /video_feed for stream, /attendance_data for JSON, /register_camera_frame for registration camera, and /register for student registration."

# # --- Main Execution ---
# if __name__ == '__main__':
#     load_attendance_log()

#     camera_thread = threading.Thread(target=camera_processing_thread, daemon=True)
#     camera_thread.start()
#     print(f"✅ Camera processing thread started.")

#     print(f"🌐 Flask server starting on http://{FLASK_HOST}:{FLASK_PORT}")
#     app_flask.run(host=FLASK_HOST, port=FLASK_PORT, debug=False, threaded=True)















# import cv2
# import pickle
# import numpy as np
# from insightface.app import FaceAnalysis
# import time
# import os
# import json
# from datetime import datetime
# from flask import Flask, Response, jsonify, request
# from flask_cors import CORS
# import threading
# import base64

# print("🔹 Starting Live Attendance Monitoring Backend...")

# # --- Configuration ---
# CAMERA_URL = "http://10.172.140.210:8080/video"
# REGISTERED_FACES_DIR = "registered_faces"
# EMBEDDINGS_FILE = "embeddings.pkl"
# ATTENDANCE_LOG_FILE = "attendance_log.json"
# RECOGNITION_THRESHOLD = 0.35
# ATTENDANCE_COOLDOWN_SECONDS = 30 # Increased slightly to prevent spam log
# FLASK_HOST = '0.0.0.0'
# FLASK_PORT = 5000

# # --- Global Variables ---
# attendance_records = {} 
# last_marked_time = {} 

# # -- Shared State for Threading --
# # We store the latest frame and the latest detection results separately
# global_frame = None
# global_frame_lock = threading.Lock()

# current_faces_data = [] # Stores coordinate and name data, not the image
# faces_data_lock = threading.Lock()

# # --- InsightFace Initialization ---
# try:
#     # detached detection size ensures model runs fast
#     app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
#     app.prepare(ctx_id=0, det_size=(640, 640)) 
#     print("✅ InsightFace model loaded successfully.")
# except Exception as e:
#     print(f"❌ Error initializing InsightFace: {e}")
#     exit()

# # --- Embeddings Management ---
# registered_embeddings = {}
# registered_reg_nos = []
# registered_embedding_vectors = np.array([])
# embeddings_lock = threading.Lock()

# def load_registered_embeddings():
#     global registered_embeddings, registered_reg_nos, registered_embedding_vectors
#     with embeddings_lock:
#         if os.path.exists(EMBEDDINGS_FILE):
#             try:
#                 with open(EMBEDDINGS_FILE, "rb") as f:
#                     data = pickle.load(f)
#                     if isinstance(data, dict):
#                         registered_embeddings = data
#                         registered_reg_nos = list(data.keys())
#                         registered_embedding_vectors = np.array(list(data.values()))
#                         print(f"✅ Loaded {len(data)} students.")
#                     else:
#                         print("❌ Embeddings file corrupted.")
#             except Exception as e:
#                 print(f"❌ Error loading embeddings: {e}")

# load_registered_embeddings()

# # --- Attendance Logic ---
# def load_attendance_log():
#     global attendance_records
#     if os.path.exists(ATTENDANCE_LOG_FILE):
#         try:
#             with open(ATTENDANCE_LOG_FILE, 'r') as f:
#                 attendance_records = json.load(f)
#         except:
#             print("Could not read attendance log, starting fresh.")

# def save_attendance_log():
#     with open(ATTENDANCE_LOG_FILE, 'w') as f:
#         json.dump(attendance_records, f, indent=4)

# load_attendance_log()

# # --- THREAD 1: Camera Capture (High Speed) ---
# def capture_thread_func():
#     global global_frame
#     cap = cv2.VideoCapture(CAMERA_URL)
    
#     print("🟢 [Capture Thread] Stream started.")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("❌ Camera disconnected, retrying in 2s...")
#             cap.release()
#             time.sleep(2)
#             cap = cv2.VideoCapture(CAMERA_URL)
#             continue
        
#         # Resize optional: If camera is 4k, resize to 720p for speed
#         # frame = cv2.resize(frame, (1280, 720))

#         with global_frame_lock:
#             global_frame = frame.copy()
        
#         # Slight sleep to allow context switching
#         time.sleep(0.01)

# # --- THREAD 2: AI Processing (Running at its own pace) ---
# def processing_thread_func():
#     global current_faces_data, attendance_records, last_marked_time
    
#     print("🧠 [AI Thread] Detection logic started.")
#     while True:
#         frame_to_process = None
        
#         # 1. Get the latest frame
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame_to_process = global_frame.copy()
        
#         if frame_to_process is None:
#             time.sleep(0.1)
#             continue

#         # 2. Run InsightFace (Heavy Operation)
#         faces = app.get(frame_to_process)
        
#         # 3. Process Results
#         processed_results = []
#         current_time = time.time()
        
#         if faces:
#             for face in faces:
#                 bbox = face.bbox.astype(int)
#                 embedding = face.embedding
                
#                 name = "Unknown"
#                 color = (0, 0, 255) # Red
#                 sim_score = 0.0

#                 with embeddings_lock:
#                     if registered_embedding_vectors.size > 0:
#                         similarities = np.dot(registered_embedding_vectors, embedding)
#                         best_idx = np.argmax(similarities)
#                         best_sim = similarities[best_idx]
#                         best_dist = 1 - best_sim
                        
#                         if best_dist < RECOGNITION_THRESHOLD:
#                             matched_reg = registered_reg_nos[best_idx]
#                             name = matched_reg
#                             sim_score = best_sim
#                             color = (0, 255, 0) # Green
                            
#                             # Mark Attendance
#                             if matched_reg not in last_marked_time or \
#                                (current_time - last_marked_time[matched_reg]) > ATTENDANCE_COOLDOWN_SECONDS:
                                
#                                 attendance_records[matched_reg] = {
#                                     'status': 'Present',
#                                     'timestamp': datetime.now().isoformat()
#                                 }
#                                 last_marked_time[matched_reg] = current_time
#                                 save_attendance_log()
#                                 print(f"✅ Marked: {matched_reg}")

#                 processed_results.append({
#                     "bbox": bbox,
#                     "name": name,
#                     "score": sim_score,
#                     "color": color
#                 })

#         # 4. Update the shared results list
#         with faces_data_lock:
#             current_faces_data = processed_results
        
#         # 5. Throttle AI Loop (Optional: prevent CPU 100%)
#         # Adjust this sleep to balance CPU usage vs Detection Speed
#         time.sleep(0.05) 

# # --- Flask App ---
# app_flask = Flask(__name__)
# CORS(app_flask)

# def generate_video_stream():
#     """Generates the MJPEG stream by overlaying LAST KNOWN data on LATEST frame"""
#     while True:
#         frame = None
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame = global_frame.copy()
        
#         if frame is None:
#             time.sleep(0.1)
#             continue

#         # Draw the LAST KNOWN faces (Even if AI is calculating next frame)
#         # This keeps the video smooth (30fps) even if AI is 5fps
#         local_faces_data = []
#         with faces_data_lock:
#             local_faces_data = current_faces_data # Copy reference

#         for data in local_faces_data:
#             x1, y1, x2, y2 = data["bbox"]
#             cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
#             label = f"{data['name']}"
#             if data["score"] > 0:
#                 label += f" ({data['score']:.2f})"
#             cv2.putText(frame, label, (x1, y1 - 10), 
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, data["color"], 2)

#         # Encode
#         ret, buffer = cv2.imencode('.jpg', frame)
#         frame_bytes = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
#         # Limit stream to ~30 FPS to save bandwidth
#         time.sleep(0.03)

# @app_flask.route('/video_feed')
# def video_feed():
#     return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app_flask.route('/attendance_data')
# def get_attendance_data():
#     return jsonify(attendance_records)

# @app_flask.route('/register_camera_frame')
# def get_register_camera_frame():
#     # Helper for RegisterStudent.js to get a snapshot
#     frame = None
#     with global_frame_lock:
#         if global_frame is not None:
#             frame = global_frame.copy()
            
#     if frame is None:
#         return jsonify({"error": "Camera loading..."}), 503
        
#     ret, buffer = cv2.imencode('.jpg', frame)
#     b64_img = base64.b64encode(buffer).decode('utf-8')
#     return jsonify({"content": b64_img})

# @app_flask.route('/register', methods=['POST'])
# def register_student():
#     if 'image' not in request.files:
#         return jsonify({"status": "error", "message": "No image"}), 400
    
#     file = request.files['image']
#     reg_no = request.form.get('reg_no')
#     name = request.form.get('name')

#     if not reg_no or not file:
#         return jsonify({"status": "error", "message": "Missing info"}), 400

#     filename = f"{reg_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
#     path = os.path.join(REGISTERED_FACES_DIR, filename)
#     file.save(path)
    
#     # Generate embedding immediately
#     img = cv2.imread(path)
#     faces = app.get(img)
#     if not faces:
#         os.remove(path)
#         return jsonify({"status": "error", "message": "No face detected in upload"}), 400
    
#     with embeddings_lock:
#         registered_embeddings[reg_no] = faces[0].embedding
#         # Update lookup arrays
#         global registered_reg_nos, registered_embedding_vectors
#         registered_reg_nos = list(registered_embeddings.keys())
#         registered_embedding_vectors = np.array(list(registered_embeddings.values()))
#         # Save to disk
#         with open(EMBEDDINGS_FILE, "wb") as f:
#             pickle.dump(registered_embeddings, f)
            
#     return jsonify({"status": "success", "message": f"Registered {name}"})

# if __name__ == '__main__':
#     # 1. Start Capture Thread
#     t_cap = threading.Thread(target=capture_thread_func, daemon=True)
#     t_cap.start()

#     # 2. Start AI Processing Thread
#     t_ai = threading.Thread(target=processing_thread_func, daemon=True)
#     t_ai.start()

#     # 3. Start Flask
#     print(f"🌐 Server running at http://{FLASK_HOST}:{FLASK_PORT}")
#     app_flask.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)



# import cv2
# import pickle
# import numpy as np
# from insightface.app import FaceAnalysis
# import time
# import os
# import json
# from datetime import datetime
# from flask import Flask, Response, jsonify, request
# from flask_cors import CORS
# import threading
# import base64

# print("🔹 Starting Live Attendance Monitoring Backend...")

# # --- Configuration ---
# CAMERA_URL = "http://10.172.140.210:8080/video"
# REGISTERED_FACES_DIR = "registered_faces"
# EMBEDDINGS_FILE = "embeddings.pkl"
# ATTENDANCE_LOG_FILE = "attendance_log.json"
# RECOGNITION_THRESHOLD = 0.35
# ATTENDANCE_COOLDOWN_SECONDS = 30 
# FLASK_HOST = '0.0.0.0'
# FLASK_PORT = 5000

# # --- Global Variables ---
# attendance_records = {} 
# last_marked_time = {} 

# # -- Shared State for Threading --
# global_frame = None
# global_frame_lock = threading.Lock()

# current_faces_data = [] 
# faces_data_lock = threading.Lock()

# # --- InsightFace Initialization ---
# try:
#     app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
#     app.prepare(ctx_id=0, det_size=(640, 640)) 
#     print("✅ InsightFace model loaded successfully.")
# except Exception as e:
#     print(f"❌ Error initializing InsightFace: {e}")
#     exit()

# # --- Embeddings Management ---
# registered_embeddings = {}
# registered_reg_nos = []
# registered_embedding_vectors = np.array([])
# embeddings_lock = threading.Lock()

# def load_registered_embeddings():
#     global registered_embeddings, registered_reg_nos, registered_embedding_vectors
#     with embeddings_lock:
#         if os.path.exists(EMBEDDINGS_FILE):
#             try:
#                 with open(EMBEDDINGS_FILE, "rb") as f:
#                     data = pickle.load(f)
#                     if isinstance(data, dict):
#                         registered_embeddings = data
#                         registered_reg_nos = list(data.keys())
#                         registered_embedding_vectors = np.array(list(data.values()))
#                         print(f"✅ Loaded {len(data)} students.")
#                     else:
#                         print("❌ Embeddings file corrupted.")
#             except Exception as e:
#                 print(f"❌ Error loading embeddings: {e}")

# load_registered_embeddings()

# # --- Attendance Logic ---
# def load_attendance_log():
#     global attendance_records
#     if os.path.exists(ATTENDANCE_LOG_FILE):
#         try:
#             with open(ATTENDANCE_LOG_FILE, 'r') as f:
#                 attendance_records = json.load(f)
#         except:
#             print("Could not read attendance log, starting fresh.")

# def save_attendance_log():
#     with open(ATTENDANCE_LOG_FILE, 'w') as f:
#         json.dump(attendance_records, f, indent=4)

# load_attendance_log()

# # --- THREAD 1: Camera Capture ---
# def capture_thread_func():
#     global global_frame
#     cap = cv2.VideoCapture(CAMERA_URL)
    
#     print("🟢 [Capture Thread] Stream started.")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("❌ Camera disconnected, retrying in 2s...")
#             cap.release()
#             time.sleep(2)
#             cap = cv2.VideoCapture(CAMERA_URL)
#             continue
        
#         with global_frame_lock:
#             global_frame = frame.copy()
        
#         time.sleep(0.01)

# # --- THREAD 2: AI Processing ---
# def processing_thread_func():
#     global current_faces_data, attendance_records, last_marked_time
    
#     print("🧠 [AI Thread] Detection logic started.")
#     while True:
#         frame_to_process = None
        
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame_to_process = global_frame.copy()
        
#         if frame_to_process is None:
#             time.sleep(0.1)
#             continue

#         faces = app.get(frame_to_process)
        
#         processed_results = []
#         current_time = time.time()
        
#         if faces:
#             for face in faces:
#                 bbox = face.bbox.astype(int)
#                 embedding = face.embedding
                
#                 name = "Unknown"
#                 color = (0, 0, 255) # Red
#                 sim_score = 0.0

#                 with embeddings_lock:
#                     if registered_embedding_vectors.size > 0:
#                         similarities = np.dot(registered_embedding_vectors, embedding)
#                         best_idx = np.argmax(similarities)
#                         best_sim = similarities[best_idx]
#                         best_dist = 1 - best_sim
                        
#                         if best_dist < RECOGNITION_THRESHOLD:
#                             matched_reg = registered_reg_nos[best_idx]
#                             name = matched_reg
#                             sim_score = best_sim
#                             color = (0, 255, 0) # Green
                            
#                             if matched_reg not in last_marked_time or \
#                                (current_time - last_marked_time[matched_reg]) > ATTENDANCE_COOLDOWN_SECONDS:
                                
#                                 attendance_records[matched_reg] = {
#                                     'status': 'Present',
#                                     'timestamp': datetime.now().isoformat()
#                                 }
#                                 last_marked_time[matched_reg] = current_time
#                                 save_attendance_log()
#                                 print(f"✅ Marked: {matched_reg}")

#                 processed_results.append({
#                     "bbox": bbox,
#                     "name": name,
#                     "score": sim_score,
#                     "color": color
#                 })

#         with faces_data_lock:
#             current_faces_data = processed_results
        
#         time.sleep(0.05) 

# # --- Flask App ---
# app_flask = Flask(__name__)
# CORS(app_flask)

# def generate_video_stream():
#     while True:
#         frame = None
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame = global_frame.copy()
        
#         if frame is None:
#             time.sleep(0.1)
#             continue

#         local_faces_data = []
#         with faces_data_lock:
#             local_faces_data = current_faces_data 

#         for data in local_faces_data:
#             x1, y1, x2, y2 = data["bbox"]
#             cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
#             label = f"{data['name']}"
#             if data["score"] > 0:
#                 label += f" ({data['score']:.2f})"
#             cv2.putText(frame, label, (x1, y1 - 10), 
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.7, data["color"], 2)

#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret: continue
#         frame_bytes = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
#         time.sleep(0.03)

# @app_flask.route('/video_feed')
# def video_feed():
#     return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app_flask.route('/attendance_data')
# def get_attendance_data():
#     return jsonify(attendance_records)

# # --- FIX: Added Reset Endpoint ---
# @app_flask.route('/reset_attendance', methods=['POST'])
# def reset_attendance():
#     global attendance_records, last_marked_time
#     # Clear Memory
#     attendance_records = {}
#     last_marked_time = {}
#     # Clear File
#     save_attendance_log()
#     print("⚠️ Attendance log has been reset by user.")
#     return jsonify({"status": "success", "message": "Attendance log cleared."})

# @app_flask.route('/register_camera_frame')
# def get_register_camera_frame():
#     frame = None
#     with global_frame_lock:
#         if global_frame is not None:
#             frame = global_frame.copy()
            
#     if frame is None:
#         return jsonify({"error": "Camera loading..."}), 503
        
#     ret, buffer = cv2.imencode('.jpg', frame)
#     b64_img = base64.b64encode(buffer).decode('utf-8')
#     return jsonify({"content": b64_img})

# @app_flask.route('/register', methods=['POST'])
# def register_student():
#     if 'image' not in request.files:
#         return jsonify({"status": "error", "message": "No image"}), 400
    
#     file = request.files['image']
#     reg_no = request.form.get('reg_no')
#     name = request.form.get('name')

#     if not reg_no or not file:
#         return jsonify({"status": "error", "message": "Missing info"}), 400

#     if not os.path.exists(REGISTERED_FACES_DIR):
#         os.makedirs(REGISTERED_FACES_DIR)

#     filename = f"{reg_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
#     path = os.path.join(REGISTERED_FACES_DIR, filename)
#     file.save(path)
    
#     img = cv2.imread(path)
#     faces = app.get(img)
#     if not faces:
#         os.remove(path)
#         return jsonify({"status": "error", "message": "No face detected in upload"}), 400
    
#     with embeddings_lock:
#         registered_embeddings[reg_no] = faces[0].embedding
#         global registered_reg_nos, registered_embedding_vectors
#         registered_reg_nos = list(registered_embeddings.keys())
#         registered_embedding_vectors = np.array(list(registered_embeddings.values()))
#         with open(EMBEDDINGS_FILE, "wb") as f:
#             pickle.dump(registered_embeddings, f)
            
#     return jsonify({"status": "success", "message": f"Registered {name}"})

# if __name__ == '__main__':
#     t_cap = threading.Thread(target=capture_thread_func, daemon=True)
#     t_cap.start()

#     t_ai = threading.Thread(target=processing_thread_func, daemon=True)
#     t_ai.start()

#     print(f"🌐 Server running at http://{FLASK_HOST}:{FLASK_PORT}")
#     app_flask.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)


# import cv2
# import pickle
# import numpy as np
# from insightface.app import FaceAnalysis
# import time
# import os
# import json
# from datetime import datetime
# from flask import Flask, Response, jsonify, request
# from flask_cors import CORS
# import threading
# import base64

# print("🔹 Starting Live Attendance Monitoring Backend...")

# # --- Configuration ---
# CAMERA_URL = "http://10.172.140.210:8080/video"
# REGISTERED_FACES_DIR = "registered_faces"
# EMBEDDINGS_FILE = "embeddings.pkl"
# ATTENDANCE_LOG_FILE = "attendance_log.json"

# # --- TUNING PARAMETERS (CRITICAL) ---
# # SIMILARITY_THRESHOLD: 
# # 0.50 = Loose (Easy match, potential false positives)
# # 0.60 = Strict (Good for attendance)
# # 0.70 = Very Strict (Might not recognize you if lighting changes)
# SIMILARITY_THRESHOLD = 0.60  

# MIN_FACE_SIZE = 80 
# ATTENDANCE_COOLDOWN_SECONDS = 30 
# FLASK_HOST = '0.0.0.0'
# FLASK_PORT = 5000

# # --- Global Variables ---
# attendance_records = {} 
# last_marked_time = {} 

# # -- Shared State for Threading --
# global_frame = None
# global_frame_lock = threading.Lock()

# current_faces_data = [] 
# faces_data_lock = threading.Lock()

# # --- InsightFace Initialization ---
# try:
#     app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
#     app.prepare(ctx_id=0, det_size=(640, 640)) 
#     print("✅ InsightFace model loaded successfully.")
# except Exception as e:
#     print(f"❌ Error initializing InsightFace: {e}")
#     exit()

# # --- Embeddings Management ---
# registered_embeddings = {}
# registered_reg_nos = []
# registered_embedding_vectors = np.array([])
# embeddings_lock = threading.Lock()

# def load_registered_embeddings():
#     global registered_embeddings, registered_reg_nos, registered_embedding_vectors
#     with embeddings_lock:
#         if os.path.exists(EMBEDDINGS_FILE):
#             try:
#                 with open(EMBEDDINGS_FILE, "rb") as f:
#                     data = pickle.load(f)
#                     if isinstance(data, dict):
#                         registered_embeddings = data
#                         registered_reg_nos = list(data.keys())
#                         registered_embedding_vectors = np.array(list(data.values()))
                        
#                         # CRITICAL: Ensure loaded embeddings are normalized
#                         # This handles cases where old embeddings might not be normalized
#                         if registered_embedding_vectors.size > 0:
#                             norms = np.linalg.norm(registered_embedding_vectors, axis=1, keepdims=True)
#                             registered_embedding_vectors = registered_embedding_vectors / norms

#                         print(f"✅ Loaded {len(data)} students.")
#                     else:
#                         print("❌ Embeddings file corrupted.")
#             except Exception as e:
#                 print(f"❌ Error loading embeddings: {e}")

# load_registered_embeddings()

# # --- Attendance Logic ---
# def load_attendance_log():
#     global attendance_records
#     if os.path.exists(ATTENDANCE_LOG_FILE):
#         try:
#             with open(ATTENDANCE_LOG_FILE, 'r') as f:
#                 attendance_records = json.load(f)
#         except:
#             pass

# def save_attendance_log():
#     with open(ATTENDANCE_LOG_FILE, 'w') as f:
#         json.dump(attendance_records, f, indent=4)

# load_attendance_log()

# # --- THREAD 1: Camera Capture ---
# def capture_thread_func():
#     global global_frame
#     cap = cv2.VideoCapture(CAMERA_URL)
#     print("🟢 [Capture Thread] Stream started.")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("❌ Camera disconnected, retrying...")
#             cap.release()
#             time.sleep(2)
#             cap = cv2.VideoCapture(CAMERA_URL)
#             continue
        
#         with global_frame_lock:
#             global_frame = frame.copy()
#         time.sleep(0.01)

# # --- THREAD 2: AI Processing ---
# def processing_thread_func():
#     global current_faces_data, attendance_records, last_marked_time
#     print("🧠 [AI Thread] Detection logic started.")
    
#     while True:
#         frame_to_process = None
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame_to_process = global_frame.copy()
        
#         if frame_to_process is None:
#             time.sleep(0.1)
#             continue

#         faces = app.get(frame_to_process)
#         processed_results = []
#         current_time = time.time()
        
#         if faces:
#             for face in faces:
#                 bbox = face.bbox.astype(int)
                
#                 # Filter Small Faces
#                 face_w = bbox[2] - bbox[0]
#                 face_h = bbox[3] - bbox[1]
#                 if face_w < MIN_FACE_SIZE: continue

#                 # CRITICAL: Normalize Live Embedding
#                 embedding = face.embedding
#                 norm = np.linalg.norm(embedding)
#                 if norm > 0:
#                     embedding = embedding / norm

#                 name = "Unknown"
#                 color = (0, 0, 255) # Red
#                 sim_score = 0.0

#                 with embeddings_lock:
#                     if registered_embedding_vectors.size > 0:
#                         # Dot product of normalized vectors = Cosine Similarity
#                         similarities = np.dot(registered_embedding_vectors, embedding)
#                         best_idx = np.argmax(similarities)
#                         best_sim = similarities[best_idx]
                        
#                         # Check Similarity Threshold (Higher is better)
#                         if best_sim > SIMILARITY_THRESHOLD:
#                             matched_reg = registered_reg_nos[best_idx]
#                             name = matched_reg
#                             sim_score = best_sim
#                             color = (0, 255, 0) # Green
                            
#                             if matched_reg not in last_marked_time or \
#                                (current_time - last_marked_time[matched_reg]) > ATTENDANCE_COOLDOWN_SECONDS:
                                
#                                 attendance_records[matched_reg] = {
#                                     'status': 'Present',
#                                     'timestamp': datetime.now().isoformat()
#                                 }
#                                 last_marked_time[matched_reg] = current_time
#                                 save_attendance_log()
#                                 print(f"✅ Marked: {matched_reg} (Score: {best_sim:.2f})")

#                 processed_results.append({
#                     "bbox": bbox,
#                     "name": name,
#                     "score": sim_score,
#                     "color": color
#                 })

#         with faces_data_lock:
#             current_faces_data = processed_results
        
#         time.sleep(0.05) 

# # --- Flask App ---
# app_flask = Flask(__name__)
# CORS(app_flask)

# def generate_video_stream():
#     while True:
#         frame = None
#         with global_frame_lock:
#             if global_frame is not None:
#                 frame = global_frame.copy()
        
#         if frame is None:
#             time.sleep(0.1)
#             continue

#         local_faces_data = []
#         with faces_data_lock:
#             local_faces_data = current_faces_data 

#         for data in local_faces_data:
#             x1, y1, x2, y2 = data["bbox"]
#             cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
            
#             # Show Name and Score on Video
#             label = f"{data['name']}"
#             if data['name'] != "Unknown":
#                 label += f" ({int(data['score']*100)}%)"
            
#             cv2.putText(frame, label, (x1, y1 - 10), 
#                         cv2.FONT_HERSHEY_SIMPLEX, 0.6, data["color"], 2)

#         ret, buffer = cv2.imencode('.jpg', frame)
#         if not ret: continue
#         yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
#         time.sleep(0.03)

# @app_flask.route('/video_feed')
# def video_feed():
#     return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# @app_flask.route('/attendance_data')
# def get_attendance_data():
#     return jsonify(attendance_records)

# @app_flask.route('/reset_attendance', methods=['POST'])
# def reset_attendance():
#     global attendance_records, last_marked_time
#     attendance_records = {}
#     last_marked_time = {}
#     save_attendance_log()
#     return jsonify({"status": "success", "message": "Cleared."})

# @app_flask.route('/register_camera_frame')
# def get_register_camera_frame():
#     frame = None
#     with global_frame_lock:
#         if global_frame is not None: frame = global_frame.copy()
#     if frame is None: return jsonify({"error": "Loading..."}), 503
#     ret, buffer = cv2.imencode('.jpg', frame)
#     return jsonify({"content": base64.b64encode(buffer).decode('utf-8')})

# @app_flask.route('/register', methods=['POST'])
# def register_student():
#     if 'image' not in request.files: return jsonify({"status": "error"}), 400
#     file = request.files['image']
#     reg_no = request.form.get('reg_no')
#     name = request.form.get('name')

#     if not os.path.exists(REGISTERED_FACES_DIR): os.makedirs(REGISTERED_FACES_DIR)
#     filename = f"{reg_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
#     path = os.path.join(REGISTERED_FACES_DIR, filename)
#     file.save(path)
    
#     img = cv2.imread(path)
#     faces = app.get(img)
#     if not faces:
#         os.remove(path)
#         return jsonify({"status": "error", "message": "No face detected"}), 400
    
#     # Register with Normalization
#     faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
#     embedding = faces[0].embedding
#     norm = np.linalg.norm(embedding)
#     if norm > 0: embedding = embedding / norm

#     with embeddings_lock:
#         registered_embeddings[reg_no] = embedding
#         global registered_reg_nos, registered_embedding_vectors
#         registered_reg_nos = list(registered_embeddings.keys())
#         registered_embedding_vectors = np.array(list(registered_embeddings.values()))
#         with open(EMBEDDINGS_FILE, "wb") as f:
#             pickle.dump(registered_embeddings, f)
            
#     return jsonify({"status": "success", "message": f"Registered {name}"})

# if __name__ == '__main__':
#     t_cap = threading.Thread(target=capture_thread_func, daemon=True)
#     t_cap.start()
#     t_ai = threading.Thread(target=processing_thread_func, daemon=True)
#     t_ai.start()
#     print(f"🌐 Server running at http://{FLASK_HOST}:{FLASK_PORT}")
#     app_flask.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)


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

print("🔹 Starting Live Attendance Monitoring Backend...")

# --- Configuration ---
CAMERA_URL = "http://10.172.140.210:8080/video"
REGISTERED_FACES_DIR = "registered_faces"
EMBEDDINGS_FILE = "embeddings.pkl"
ATTENDANCE_LOG_FILE = "attendance_log.json"

# --- TUNING PARAMETERS (CRITICAL) ---
# SIMILARITY_THRESHOLD: 
# 0.50 = Loose (Easy match, potential false positives)
# 0.60 = Strict (Good for attendance)
# 0.70 = Very Strict (Might not recognize you if lighting changes)
SIMILARITY_THRESHOLD = 0.60  

MIN_FACE_SIZE = 80 
ATTENDANCE_COOLDOWN_SECONDS = 30 
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000

# --- Global Variables ---
attendance_records = {} 
last_marked_time = {} 

# -- Shared State for Threading --
global_frame = None
global_frame_lock = threading.Lock()

current_faces_data = [] 
faces_data_lock = threading.Lock()

# --- InsightFace Initialization ---
try:
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640)) 
    print("✅ InsightFace model loaded successfully.")
except Exception as e:
    print(f"❌ Error initializing InsightFace: {e}")
    exit()

# --- Embeddings Management ---
registered_embeddings = {}
registered_reg_nos = []
registered_embedding_vectors = np.array([])
embeddings_lock = threading.Lock()

def load_registered_embeddings():
    global registered_embeddings, registered_reg_nos, registered_embedding_vectors
    with embeddings_lock:
        if os.path.exists(EMBEDDINGS_FILE):
            try:
                with open(EMBEDDINGS_FILE, "rb") as f:
                    data = pickle.load(f)
                    if isinstance(data, dict):
                        registered_embeddings = data
                        registered_reg_nos = list(data.keys())
                        registered_embedding_vectors = np.array(list(data.values()))
                        
                        # CRITICAL: Ensure loaded embeddings are normalized
                        # This handles cases where old embeddings might not be normalized
                        if registered_embedding_vectors.size > 0:
                            norms = np.linalg.norm(registered_embedding_vectors, axis=1, keepdims=True)
                            registered_embedding_vectors = registered_embedding_vectors / norms

                        print(f"✅ Loaded {len(data)} students.")
                    else:
                        print("❌ Embeddings file corrupted.")
            except Exception as e:
                print(f"❌ Error loading embeddings: {e}")

load_registered_embeddings()

# --- Attendance Logic ---
def load_attendance_log():
    global attendance_records
    if os.path.exists(ATTENDANCE_LOG_FILE):
        try:
            with open(ATTENDANCE_LOG_FILE, 'r') as f:
                attendance_records = json.load(f)
        except:
            pass

def save_attendance_log():
    with open(ATTENDANCE_LOG_FILE, 'w') as f:
        json.dump(attendance_records, f, indent=4)

load_attendance_log()

# --- THREAD 1: Camera Capture ---
def capture_thread_func():
    global global_frame
    cap = cv2.VideoCapture(CAMERA_URL)
    print("🟢 [Capture Thread] Stream started.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Camera disconnected, retrying...")
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_URL)
            continue
        
        with global_frame_lock:
            global_frame = frame.copy()
        time.sleep(0.01)

# --- THREAD 2: AI Processing ---
def processing_thread_func():
    global current_faces_data, attendance_records, last_marked_time
    print("🧠 [AI Thread] Detection logic started.")
    
    while True:
        frame_to_process = None
        with global_frame_lock:
            if global_frame is not None:
                frame_to_process = global_frame.copy()
        
        if frame_to_process is None:
            time.sleep(0.1)
            continue

        faces = app.get(frame_to_process)
        processed_results = []
        current_time = time.time()
        
        if faces:
            for face in faces:
                bbox = face.bbox.astype(int)
                
                # Filter Small Faces
                face_w = bbox[2] - bbox[0]
                face_h = bbox[3] - bbox[1]
                if face_w < MIN_FACE_SIZE: continue

                # CRITICAL: Normalize Live Embedding
                embedding = face.embedding
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm

                name = "Unknown"
                color = (0, 0, 255) # Red
                sim_score = 0.0

                with embeddings_lock:
                    if registered_embedding_vectors.size > 0:
                        # Dot product of normalized vectors = Cosine Similarity
                        similarities = np.dot(registered_embedding_vectors, embedding)
                        best_idx = np.argmax(similarities)
                        best_sim = similarities[best_idx]
                        
                        # Check Similarity Threshold (Higher is better)
                        if best_sim > SIMILARITY_THRESHOLD:
                            matched_reg = registered_reg_nos[best_idx]
                            name = matched_reg
                            sim_score = best_sim
                            color = (0, 255, 0) # Green
                            
                            if matched_reg not in last_marked_time or \
                               (current_time - last_marked_time[matched_reg]) > ATTENDANCE_COOLDOWN_SECONDS:
                                
                                attendance_records[matched_reg] = {
                                    'status': 'Present',
                                    'timestamp': datetime.now().isoformat()
                                }
                                last_marked_time[matched_reg] = current_time
                                save_attendance_log()
                                print(f"✅ Marked: {matched_reg} (Score: {best_sim:.2f})")

                processed_results.append({
                    "bbox": bbox,
                    "name": name,
                    "score": sim_score,
                    "color": color
                })

        with faces_data_lock:
            current_faces_data = processed_results
        
        time.sleep(0.05) 

# --- Flask App ---
app_flask = Flask(__name__)
CORS(app_flask)

def generate_video_stream():
    while True:
        frame = None
        with global_frame_lock:
            if global_frame is not None:
                frame = global_frame.copy()
        
        if frame is None:
            time.sleep(0.1)
            continue

        local_faces_data = []
        with faces_data_lock:
            local_faces_data = current_faces_data 

        for data in local_faces_data:
            x1, y1, x2, y2 = data["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), data["color"], 2)
            
            # Show Name and Score on Video
            label = f"{data['name']}"
            if data['name'] != "Unknown":
                label += f" ({int(data['score']*100)}%)"
            
            cv2.putText(frame, label, (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, data["color"], 2)

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret: continue
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        time.sleep(0.03)

@app_flask.route('/video_feed')
def video_feed():
    return Response(generate_video_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app_flask.route('/attendance_data')
def get_attendance_data():
    return jsonify(attendance_records)

@app_flask.route('/reset_attendance', methods=['POST'])
def reset_attendance():
    global attendance_records, last_marked_time
    attendance_records = {}
    last_marked_time = {}
    save_attendance_log()
    return jsonify({"status": "success", "message": "Cleared."})

@app_flask.route('/register_camera_frame')
def get_register_camera_frame():
    frame = None
    with global_frame_lock:
        if global_frame is not None: frame = global_frame.copy()
    if frame is None: return jsonify({"error": "Loading..."}), 503
    ret, buffer = cv2.imencode('.jpg', frame)
    return jsonify({"content": base64.b64encode(buffer).decode('utf-8')})

@app_flask.route('/register', methods=['POST'])
def register_student():
    if 'image' not in request.files: return jsonify({"status": "error"}), 400
    file = request.files['image']
    reg_no = request.form.get('reg_no')
    name = request.form.get('name')

    if not os.path.exists(REGISTERED_FACES_DIR): os.makedirs(REGISTERED_FACES_DIR)
    filename = f"{reg_no}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
    path = os.path.join(REGISTERED_FACES_DIR, filename)
    file.save(path)
    
    img = cv2.imread(path)
    faces = app.get(img)
    if not faces:
        os.remove(path)
        return jsonify({"status": "error", "message": "No face detected"}), 400
    
    # Register with Normalization
    faces.sort(key=lambda x: (x.bbox[2]-x.bbox[0])*(x.bbox[3]-x.bbox[1]), reverse=True)
    embedding = faces[0].embedding
    norm = np.linalg.norm(embedding)
    if norm > 0: embedding = embedding / norm

    with embeddings_lock:
        registered_embeddings[reg_no] = embedding
        global registered_reg_nos, registered_embedding_vectors
        registered_reg_nos = list(registered_embeddings.keys())
        registered_embedding_vectors = np.array(list(registered_embeddings.values()))
        with open(EMBEDDINGS_FILE, "wb") as f:
            pickle.dump(registered_embeddings, f)
            
    return jsonify({"status": "success", "message": f"Registered {name}"})

if __name__ == '__main__':
    t_cap = threading.Thread(target=capture_thread_func, daemon=True)
    t_cap.start()
    t_ai = threading.Thread(target=processing_thread_func, daemon=True)
    t_ai.start()
    print(f"🌐 Server running at http://{FLASK_HOST}:{FLASK_PORT}")
    app_flask.run(host=FLASK_HOST, port=FLASK_PORT, threaded=True, debug=False)