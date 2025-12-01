import cv2
import numpy as np
import os

img_path = "debug_no_face.jpg"

if not os.path.exists(img_path):
    print("File not found")
    exit()

img = cv2.imread(img_path)
if img is None:
    print("Failed to load image")
    exit()

print(f"Resolution: {img.shape[1]}x{img.shape[0]}")
print(f"Mean Brightness: {np.mean(img):.2f}")
print(f"Standard Deviation: {np.std(img):.2f}")
