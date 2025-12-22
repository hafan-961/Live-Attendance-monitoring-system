


import os
import pickle
import cv2
import numpy as np
from insightface.app import FaceAnalysis

print("🔹 Starting embedding generation script...")

# --- Configuration ---
REGISTERED_FACES_DIR = "registered_faces"
EMBEDDINGS_FILE = "embeddings.pkl"
MIN_FACE_SIZE = 80

# --- Initialize InsightFace ---
try:
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640)) 
    print("✅ InsightFace model loaded.")
except Exception as e:
    print(f"❌ Error initializing InsightFace: {e}")
    exit()

embeddings = {}
processed_count = 0
failed_count = 0

if not os.path.exists(REGISTERED_FACES_DIR):
    print(f"❌ '{REGISTERED_FACES_DIR}' not found.")
    exit()

print(f"Scanning images in '{REGISTERED_FACES_DIR}'...")
for filename in os.listdir(REGISTERED_FACES_DIR):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        
        # Robust ID extraction
        parts = filename.split("_")
        if len(parts) > 1:
            reg_no = parts[0]
        else:
            reg_no = os.path.splitext(filename)[0]

        img_path = os.path.join(REGISTERED_FACES_DIR, filename)
        img = cv2.imread(img_path)

        if img is None:
            continue

        faces = app.get(img)

        if faces:
            # 1. Sort by size to get the main person
            faces.sort(key=lambda x: (x.bbox[2] - x.bbox[0]) * (x.bbox[3] - x.bbox[1]), reverse=True)
            target_face = faces[0]

            # 2. Check Size
            w = target_face.bbox[2] - target_face.bbox[0]
            if w < MIN_FACE_SIZE:
                print(f"⚠️ Image too small/blurry: {filename}")
                failed_count += 1
                continue

            # 3. CRITICAL: Normalize Embedding
            embedding = target_face.embedding
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm # Normalize to length 1.0

            embeddings[reg_no] = embedding
            print(f"✅ Registered: {reg_no}")
            processed_count += 1
        else:
            print(f"⚠️ No face found: {filename}")
            failed_count += 1

# --- Save ---
if embeddings:
    with open(EMBEDDINGS_FILE, "wb") as f:
        pickle.dump(embeddings, f)
    print(f"\n✅ DATABASE UPDATED: {processed_count} students saved.")
else:
    print(f"\n❌ No embeddings generated.")