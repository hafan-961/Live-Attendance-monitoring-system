from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import cv2
import numpy as np
import base64
import os
import pickle
import requests
from datetime import datetime
from insightface.app import FaceAnalysis

# ---------------------- INIT APP ----------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- INSIGHTFACE SETUP ----------------------
face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
face_app.prepare(ctx_id=0, det_size=(640, 640))

# Create registered_faces folder if it doesn't exist
REGISTERED_FACES_DIR = "registered_faces"
os.makedirs(REGISTERED_FACES_DIR, exist_ok=True)

EMBEDDINGS_PATH = "embeddings.pkl"

# Initialize known_faces as list
if os.path.exists(EMBEDDINGS_PATH):
    try:
        with open(EMBEDDINGS_PATH, "rb") as f:
            data = pickle.load(f)
            # Ensure it's a list, not a dict
            known_faces = data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading embeddings: {e}")
        known_faces = []
else:
    known_faces = []

print(f"Loaded {len(known_faces)} known faces")

# ---------------------- CAMERA CONFIGURATION ----------------------
CAMERA_IP = "http://10.208.138.152:8080/shot.jpg"  # Your IP camera URL

# ---------------------- CAMERA URL (FIXED) ----------------------
@app.get("/camera_url")
def camera_url():
    return {
        "image_url": "http://127.0.0.1:8000/camera_feed",
        "video_url": CAMERA_IP
    }

# ---------------------- CAMERA FEED ENDPOINT ----------------------
@app.get("/camera_feed")
def get_camera_feed():
    """
    Proxies the IP camera feed and returns base64 encoded image
    """
    import requests
    
    try:
        # Fetch image from IP camera
        response = requests.get(CAMERA_IP, timeout=5)
        
        if response.status_code != 200:
            return {"error": f"Camera returned status {response.status_code}"}
        
        # Read image from response
        nparr = np.frombuffer(response.content, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Failed to decode frame"}
        
        # Resize frame for faster streaming
        frame = cv2.resize(frame, (640, 480))
        
        # Encode frame to JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        img_bytes = buffer.tobytes()
        
        return {
            "content": base64.b64encode(img_bytes).decode('utf-8'),
            "type": "image/jpeg"
        }
    
    except requests.exceptions.Timeout:
        return {"error": "Camera connection timeout"}
    except requests.exceptions.ConnectionError:
        return {"error": f"Cannot connect to camera at {CAMERA_IP}"}
    except Exception as e:
        return {"error": f"Camera error: {str(e)}"}

# ---------------------- REGISTER FACE ----------------------
@app.post("/register")
async def register_student(
    name: str = Form(...),
    reg_no: str = Form(...),
    roll_no: str = Form(...),
    section: str = Form(...),
    image: UploadFile = File(...)
):
    try:
        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid image format"}
        
        # Detect faces
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"error": "No face detected"}
        
        # Extract embedding
        face_embedding = faces[0].embedding.tolist()
        
        # Save the image with register number as filename
        image_filename = f"{reg_no}_{name}.jpg"
        image_path = os.path.join(REGISTERED_FACES_DIR, image_filename)
        cv2.imwrite(image_path, frame)
        
        # Create student record
        student_record = {
            "name": name,
            "register_no": reg_no,
            "roll_no": roll_no,
            "section": section,
            "embedding": face_embedding,
            "image_path": image_path
        }
        
        # Ensure known_faces is a list
        if not isinstance(known_faces, list):
            known_faces.clear()
        
        # Add to known faces
        known_faces.append(student_record)
        
        # Save to pickle file
        with open(EMBEDDINGS_PATH, "wb") as f:
            pickle.dump(known_faces, f)
        
        print(f"✅ Student registered: {name}")
        print(f"   📁 Image saved to: {image_path}")
        print(f"   Total registered: {len(known_faces)}")
        
        return {
            "status": "success",
            "message": f"Student {name} registered successfully!",
            "image_path": image_path
        }
    
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        return {"error": f"Registration failed: {str(e)}"}

# ---------------------- MARK ATTENDANCE ----------------------
@app.post("/mark_attendance")
async def mark_attendance(image: UploadFile = File(...)):
    try:
        img_bytes = await image.read()
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        faces = face_app.get(frame)
        
        if len(faces) == 0:
            return {"status": "no_face"}
        
        detected = faces[0].embedding
        best_match = None
        best_score = 999
        
        for person in known_faces:
            db_emb = np.array(person["embedding"])
            distance = np.linalg.norm(detected - db_emb)
            if distance < best_score:
                best_score = distance
                best_match = person
        
        if best_score < 0.8 and best_match:
            timestamp = datetime.now().strftime("%H:%M:%S")
            record = {
                "Register_No": best_match["register_no"],
                "Name": best_match["name"],
                "Roll_No": best_match["roll_no"],
                "Section": best_match["section"],
                "Time": timestamp,
                "Status": "Present"
            }
            attendance_records.append(record)
            return record
        else:
            return {"status": "unknown"}
    
    except Exception as e:
        return {"error": f"Attendance marking failed: {str(e)}"}

# ---------------------- GET ATTENDANCE RECORDS ----------------------
# Store attendance records in memory (you can use a database later)
attendance_records = []

@app.get("/attendance")
def get_attendance():
    # Return list of attendance records
    return attendance_records

# ---------------------- START SERVER ----------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)