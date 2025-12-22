import cv2
import pickle
import numpy as np
import pandas as pd
import os
from datetime import datetime, timedelta
from insightface.app import FaceAnalysis

# Load precomputed embeddings
with open("embeddings.pkl", "rb") as f:
    known_embeddings = pickle.load(f)

# Initialize face analysis
app = FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))

# Class config
# CLASS_DURATION = 3600  # 1 hour in seconds
# LATE_LIMIT = 600       # 10 minutes
# PRESENT_THRESHOLD = 0.7  # 70%

start_time = datetime.now()
attendance_file = "attendance.csv"

# Create CSV if not exists
if not os.path.exists(attendance_file):
    pd.DataFrame(columns=["Register_No", "Join_Time", "Leave_Time", "Duration", "Status"]).to_csv(attendance_file, index=False)

# Camera feed
url = "http://10.4.90.205:8080/video"  # update with your current phone URL

cap = cv2.VideoCapture(url)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

# Store detection times
presence_times = {}

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = app.get(frame)
    current_time = datetime.now()

    for face in faces:
        emb = face.embedding
        best_match = None
        highest_sim = 0.45

        for reg_no, known_emb in known_embeddings.items():
            sim = cosine_similarity(emb, known_emb)
            if sim > highest_sim:
                best_match = reg_no
                highest_sim = sim

        if best_match:
            if best_match not in presence_times:
                presence_times[best_match] = {"join": current_time, "last_seen": current_time, "total": 0}
                print(f"🟢 {best_match} joined at {current_time.strftime('%H:%M:%S')}")
            else:
                last_seen = presence_times[best_match]["last_seen"]
                presence_times[best_match]["total"] += (current_time - last_seen).total_seconds()
                presence_times[best_match]["last_seen"] = current_time

            # Draw box
            box = face.bbox.astype(int)
            cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
            cv2.putText(frame, best_match, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Smart Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# After class end
end_time = datetime.now()
records = []

for reg_no, data in presence_times.items():
    join_time = data["join"]
    duration = data["total"]
    late = (join_time - start_time).total_seconds() > LATE_LIMIT
    present_ratio = duration / CLASS_DURATION

    status = "Absent"
    if not late and present_ratio >= PRESENT_THRESHOLD:
        status = "Present"

    records.append({
        "Register_No": reg_no,
        "Join_Time": join_time.strftime("%H:%M:%S"),
        "Leave_Time": end_time.strftime("%H:%M:%S"),
        "Duration": f"{duration:.1f}s",
        "Status": status
    })

pd.DataFrame(records).to_csv(attendance_file, index=False)
cap.release()
cv2.destroyAllWindows()
print("✅ Attendance evaluation complete. Check attendance.csv.")
