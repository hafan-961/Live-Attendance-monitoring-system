import cv2
import pickle
import numpy as np
import pandas as pd
import os
from datetime import datetime
from insightface.app import FaceAnalysis

# Load precomputed embeddings
with open("embeddings.pkl", "rb") as f:
    known_embeddings = pickle.load(f)

# Initialize face analysis
app = FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))

# Attendance CSV
attendance_file = "attendance.csv"
if not os.path.exists(attendance_file):
    pd.DataFrame(columns=["Register_No", "Time", "Status"]).to_csv(attendance_file, index=False)

# Camera feed
url = "http://10.212.93.162:8080/video"
cap = cv2.VideoCapture(url)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

marked = set()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    faces = app.get(frame)
    for face in faces:
        emb = face.embedding
        best_match = None
        highest_sim = 0.45  # threshold for match

        for reg_no, known_emb in known_embeddings.items():
            sim = cosine_similarity(emb, known_emb)
            if sim > highest_sim:
                best_match = reg_no
                highest_sim = sim

        if best_match and best_match not in marked:
            print(f"✅ {best_match} marked Present")
            time_now = datetime.now().strftime("%H:%M:%S")
            df = pd.read_csv(attendance_file)
            df.loc[len(df.index)] = [best_match, time_now, "Present"]
            df.to_csv(attendance_file, index=False)
            marked.add(best_match)

        # draw face box
        box = face.bbox.astype(int)
        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
        if best_match:
            cv2.putText(frame, best_match, (box[0], box[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Live Attendance", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
