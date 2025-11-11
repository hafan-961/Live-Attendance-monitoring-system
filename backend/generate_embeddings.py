import os
import pickle
import cv2
from insightface.app import FaceAnalysis

# Initialize InsightFace
app = FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))

embeddings = {}

path = "registered_faces"
for filename in os.listdir(path):
    if filename.endswith(".jpg"):
        reg_no = filename.split("_")[0]
        img_path = os.path.join(path, filename)
        img = cv2.imread(img_path)
        faces = app.get(img)
        if faces:
            embeddings[reg_no] = faces[0].embedding
            print(f"✅ Saved embedding for {reg_no}")

# Save embeddings to file
with open("embeddings.pkl", "wb") as f:
    pickle.dump(embeddings, f)

print("\n✅ All embeddings generated and saved successfully!")
