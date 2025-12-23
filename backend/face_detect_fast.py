import cv2, time
from insightface.app import FaceAnalysis

app = FaceAnalysis()
app.prepare(ctx_id=0, det_size=(320, 320))

url = "http://10.6.192.103:8080/video"
cap = cv2.VideoCapture(url)

last_faces = []          # remember last detection
last_time = 0
detect_interval = 1.0    # run detection every 1 second

while True:
    ret, frame = cap.read()
    if not ret:
        print("Camera disconnected.")
        break

    # run detection only once per second
    now = time.time()
    if now - last_time > detect_interval:
        last_faces = app.get(frame)
        last_time = now

    # draw last known boxes (prevents blinking)
    for face in last_faces:
        box = face.bbox.astype(int)
        cv2.rectangle(frame, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)

    cv2.imshow("Smooth Face Detection", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
