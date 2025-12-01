from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import uvicorn
import cv2
import numpy as np
import base64
import os
import pickle
import requests
from datetime import datetime

# ---- ALWAYS LOAD APP FIRST (prevents app-not-found error) ----
app = FastAPI()

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Load InsightFace safely ----
try:
    from insightface.app import FaceAnalysis
    face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=0, det_size=(640, 640))
    insight_loaded = True
    print("✅ InsightFace loaded successfully")
except Exception as e:
    print("❌ InsightFace failed to load:", e)
    insight_loaded = False

# ---- Storage ----
REGISTERED_FACES_DIR = "registered_faces"
os.makedirs(REGISTERED_FACES_DIR, exist_ok=True)

EMBEDDINGS_PATH = "embeddings.pkl"

try:
    known_faces = pickle.load(open(EMBEDDINGS_PATH, "rb"))
    if not isinstance(known_faces, list):
        known_faces = []
except:
    known_faces = []

print(f"✅ Loaded {len(known_faces)} known faces")

attendance_records = []

# ---- Camera ----
CAMERA_IP = "http://10.168.33.206:8080/shot.jpg"


# -----------------------------------------------------------
# ENDPOINT: Check camera URL
# -----------------------------------------------------------
@app.get("/camera_url")
def camera_url():
    return {
        "video_url": CAMERA_IP,
        "image_url": "http://127.0.0.1:8000/camera_feed"
    }


# -----------------------------------------------------------
# ENDPOINT: Camera Feed
# -----------------------------------------------------------
@app.get("/camera_feed")
def camera_feed():
    try:
        print("📷 Fetching camera feed...")
        res = requests.get(CAMERA_IP, timeout=5)
        
        if res.status_code != 200:
            print(f"❌ Camera returned status {res.status_code}")
            return {"error": f"Camera returned status {res.status_code}"}
        
        nparr = np.frombuffer(res.content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            print("❌ Failed to decode frame")
            return {"error": "Failed to decode frame"}
        
        frame = cv2.resize(frame, (640, 480))
        _, buffer = cv2.imencode(".jpg", frame)
        
        print("✅ Camera feed sent successfully")

        return {
            "content": base64.b64encode(buffer).decode(),
            "type": "image/jpeg"
        }

    except requests.exceptions.Timeout:
        print("❌ Camera connection timeout")
        return {"error": "Camera connection timeout"}
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to camera at {CAMERA_IP}")
        return {"error": f"Cannot connect to camera at {CAMERA_IP}"}
    except Exception as e:
        print(f"❌ Camera error: {str(e)}")
        return {"error": str(e)}


# -----------------------------------------------------------
# ENDPOINT: Register Student
# -----------------------------------------------------------
@app.post("/register")
async def register_student(
    name: str = Form(...),
    reg_no: str = Form(...),
    roll_no: str = Form(...),
    section: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        if not insight_loaded:
            return {"error": "InsightFace failed to load"}

        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Invalid image format"}

        faces = face_app.get(frame)
        if len(faces) == 0:
            return {"error": "No face detected"}

        emb = faces[0].embedding.tolist()

        filename = f"{reg_no}_{name}.jpg"
        path = os.path.join(REGISTERED_FACES_DIR, filename)
        cv2.imwrite(path, frame)

        student = {
            "name": name,
            "register_no": reg_no,
            "roll_no": roll_no,
            "section": section,
            "embedding": emb,
            "image_path": path
        }

        known_faces.append(student)
        pickle.dump(known_faces, open(EMBEDDINGS_PATH, "wb"))

        print(f"✅ Student registered: {name}")
        return {"status": "success", "message": f"Student {name} registered successfully!"}

    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return {"error": str(e)}


# -----------------------------------------------------------
# ENDPOINT: Start Attendance
# -----------------------------------------------------------
@app.post("/start_attendance")
def start_attendance():

    if not insight_loaded:
        return {"error": "InsightFace failed to load"}

    try:
        print("📷 Starting attendance capture...")
        res = requests.get(CAMERA_IP, timeout=5)
        
        if res.status_code != 200:
            return {"error": "Failed to capture frame from camera"}
        
        nparr = np.frombuffer(res.content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            return {"error": "Failed to decode frame"}

        faces = face_app.get(frame)
        if len(faces) == 0:
            # DEBUG: Save image to check why face is not detected
            cv2.imwrite("debug_no_face.jpg", frame)
            print("❌ No face detected. Saved frame to 'debug_no_face.jpg'")
            return {"status": "no_face", "detected": [], "error": "No face detected"}

        detected = []
        for face in faces:
            emb = face.embedding
            best_match = None
            best_score = 999

            for person in known_faces:
                db = np.array(person["embedding"])
                score = np.linalg.norm(emb - db)

                if score < best_score:
                    best_score = score
                    best_match = person

            if best_score < 1.0 and best_match:
                record = {
                    "Register_No": best_match["register_no"],
                    "Name": best_match["name"],
                    "Roll_No": best_match["roll_no"],
                    "Section": best_match["section"],
                    "Time": datetime.now().strftime("%H:%M:%S"),
                    "Status": "Present"
                }
    
                # Avoid duplicate records
                duplicate = False
                for existing in attendance_records:
                    if existing["Register_No"] == record["Register_No"] and existing["Time"] == record["Time"]:
                        duplicate = True
                        break

                if not duplicate:
                    attendance_records.append(record)
                    detected.append(record)
                print(f"✅ Match found: {best_match['name']} (Score: {best_score:.2f})")
            else:
                print(f"❌ Unknown face. Best score: {best_score:.2f} (Threshold: 1.0)")

        print(f"✅ Detected {len(detected)} student(s)")
        return {"status": "success", "detected": detected}

    except Exception as e:
        print(f"❌ Attendance error: {str(e)}")
        return {"error": str(e)}


# -----------------------------------------------------------
# GET ATTENDANCE
# -----------------------------------------------------------
@app.get("/attendance")
def get_attendance():
    return attendance_records


# -----------------------------------------------------------
# GET REGISTERED STUDENTS
# -----------------------------------------------------------
@app.get("/students")
def get_students():
    # Return list of students without embeddings (too large)
    students_list = []
    for person in known_faces:
        students_list.append({
            "name": person["name"],
            "register_no": person["register_no"],
            "roll_no": person["roll_no"],
            "section": person["section"],
            # "image_path": person["image_path"] # Optional: if you want to serve images later
        })
    return students_list


# -----------------------------------------------------------
# RUN SERVER
# -----------------------------------------------------------
if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)