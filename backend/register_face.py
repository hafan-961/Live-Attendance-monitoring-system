import cv2
import pandas as pd
import os
from datetime import datetime

print("🔹 Starting face registration script...")

# folders and files
os.makedirs("registered_faces", exist_ok=True)
csv_file = "students.csv"

# camera feed
url = "http://10.168.33.206:8080/video"   # ← your current working link. 
print("Connecting to camera:", url)
cap = cv2.VideoCapture(url)

if not cap.isOpened():
    print("❌ Could not connect to camera!")
    exit()
else:
    print("✅ Camera connected successfully.")

# student details
reg_no = input("Enter Register Number: ")
roll_no = input("Enter Roll Number: ")
section = input("Enter Section: ")

print("🟢 Starting live preview — press 's' to save, 'q' to quit.")

count = 0
while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Could not read frame from camera.")
        break

    # show live feed
    cv2.imshow("Capture Student Face", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        filename = f"registered_faces/{reg_no}_{count}.jpg"
        cv2.imwrite(filename, frame)
        print(f"✅ Saved {filename}")
        count += 1
    elif key == ord('q'):
        print("👋 Exiting capture.")
        break

cap.release()
cv2.destroyAllWindows()

