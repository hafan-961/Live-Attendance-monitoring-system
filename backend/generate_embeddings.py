# import os
# import pickle
# import cv2
# import numpy as np
# from insightface.app import FaceAnalysis

# print("🔹 Starting embedding generation script...")

# # --- Configuration ---
# REGISTERED_FACES_DIR = "registered_faces"
# EMBEDDINGS_FILE = "embeddings.pkl"

# # --- Initialize InsightFace ---
# # Use the same model and ctx_id as you intend to use in main.py for consistency.
# # ctx_id=0 for GPU, ctx_id=-1 for CPU. Adjust based on your hardware.
# try:
#     app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
#     app.prepare(ctx_id=0, det_size=(640, 640)) # Try ctx_id=-1 if you don't have a GPU or face issues
#     print("✅ InsightFace model loaded for embedding generation.")
# except Exception as e:
#     print(f"❌ Error initializing InsightFace: {e}")
#     print("Please ensure insightface is installed and models are downloaded.")
#     exit()

# embeddings = {}
# processed_count = 0
# failed_count = 0

# if not os.path.exists(REGISTERED_FACES_DIR) or not os.listdir(REGISTERED_FACES_DIR):
#     print(f"❌ No images found in '{REGISTERED_FACES_DIR}'. Please run register_face.py first.")
#     exit()

# print(f"Scanning images in '{REGISTERED_FACES_DIR}'...")
# for filename in os.listdir(REGISTERED_FACES_DIR):
#     # Process only common image file types
#     if filename.lower().endswith((".jpg", ".jpeg", ".png")):
#         # Extract reg_no from filename (e.g., "12345_0.jpg" -> "12345")
#         parts = filename.split("_")
#         if len(parts) > 1:
#             reg_no = parts[0]
#         else:
#             print(f"⚠️ Skipping '{filename}': Filename format not recognized (expected 'reg_no_count.jpg').")
#             failed_count += 1
#             continue

#         img_path = os.path.join(REGISTERED_FACES_DIR, filename)
#         img = cv2.imread(img_path)

#         if img is None:
#             print(f"❌ Could not read image: {img_path}. Skipping.")
#             failed_count += 1
#             continue

#         # InsightFace's app.get() expects BGR format from OpenCV by default.
#         faces = app.get(img)

#         if faces:
#             # If multiple faces are detected, we take the first one.
#             # The improved register_face.py helps ensure only one face is present.
#             embeddings[reg_no] = faces[0].embedding
#             print(f"✅ Saved embedding for {reg_no} from {filename}")
#             processed_count += 1
#         else:
#             print(f"⚠️ No face detected in {filename} for {reg_no}. This student will not be recognized.")
#             failed_count += 1

# # --- Save Embeddings to File ---
# if embeddings:
#     with open(EMBEDDINGS_FILE, "wb") as f:
#         pickle.dump(embeddings, f)
#     print(f"\n✅ All embeddings generated and saved successfully to '{EMBEDDINGS_FILE}'!")
#     print(f"   Processed {processed_count} students, {failed_count} images failed to generate embeddings.")
# else:
#     print(f"\n❌ No embeddings were generated. '{EMBEDDINGS_FILE}' will not be created.")
#     print(f"   {failed_count} images failed to generate embeddings.")

# print("Script finished.")


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