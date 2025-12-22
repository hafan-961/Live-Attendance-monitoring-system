import cv2
import os
from datetime import datetime
import insightface 
from insightface.app import FaceAnalysis

print("🔹 Starting face registration script...")

# --- Configuration ---
REGISTERED_FACES_DIR = "registered_faces"
# csv_file = "students.csv" # Not directly used in this script, but kept for context

# --- Setup Directories ---
os.makedirs(REGISTERED_FACES_DIR, exist_ok=True)

# --- Initialize InsightFace for real-time feedback ---
# Using 'buffalo_l' model, which is a good balance of accuracy and speed.
# ctx_id=0 for GPU, ctx_id=-1 for CPU. Adjust based on your hardware.
try:
    app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    app.prepare(ctx_id=0, det_size=(640, 640)) # Try ctx_id=-1 if you don't have a GPU or face issues
    print("✅ InsightFace model loaded for live detection feedback.")
except Exception as e:
    print(f"❌ Error initializing InsightFace: {e}")
    print("Please ensure insightface is installed and models are downloaded. Falling back to no live detection feedback.")
    app = None # Disable live detection feedback if InsightFace fails

# --- Camera Feed Setup ---

CAMERA_URL = "http://10.215.90.242:8080/video"
print(f"Connecting to camera: {CAMERA_URL}")
cap = cv2.VideoCapture(CAMERA_URL)

if not cap.isOpened():
    print(f"❌ Could not connect to camera at {CAMERA_URL}!")
    print("Please check the camera URL and ensure the camera is active.")
    exit()
else:
    print("✅ Camera connected successfully.")

# --- Student Details Input ---
reg_no = input("Enter Register Number: ").strip()
if not reg_no:
    print("❌ Register Number cannot be empty. Exiting.")
    cap.release()
    exit()



print(f"🟢 Starting live preview for student {reg_no} — press 's' to save, 'q' to quit.")
print("   (Note: Image will only save if a face is detected in the frame.)")

count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Could not read frame from camera. Attempting to reconnect...")
        cap.release()
        cap = cv2.VideoCapture(CAMERA_URL)
        if not cap.isOpened():
            print("❌ Failed to reconnect to camera. Exiting.")
            break
        continue

    display_frame = frame.copy() # Work on a copy for drawing

    detected_face = False
    if app: # Only perform detection if InsightFace was initialized successfully
        faces = app.get(frame) # Detect faces in the original frame
        if faces:
            detected_face = True
            # Draw bounding boxes around detected faces for visual feedback
            for face in faces:
                bbox = face.bbox.astype(int)
                cv2.rectangle(display_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
            cv2.putText(display_frame, "Face Detected!", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
        else:
            cv2.putText(display_frame, "No Face Detected", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
    else:
        cv2.putText(display_frame, "InsightFace not loaded (no live detection feedback)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2, cv2.LINE_AA)


    # Show live feed
    cv2.imshow("Capture Student Face", display_frame)

    key = cv2.waitKey(1) & 0xFF

    if key == ord('s'):
        if detected_face:
            filename = os.path.join(REGISTERED_FACES_DIR, f"{reg_no}_{count}.jpg")
            cv2.imwrite(filename, frame) # Save the original frame
            print(f"✅ Saved {filename}")
            count += 1
        else:
            print("⚠️ No face detected. Cannot save image. Please ensure your face is clearly visible.")
    elif key == ord('q'):
        print("👋 Exiting capture.")
        break

# --- Cleanup ---
cap.release()
cv2.destroyAllWindows()
print("Script finished.")