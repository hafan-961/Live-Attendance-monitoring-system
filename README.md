# Live-Attendance & Sentiment Analytics System

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![React](https://img.shields.io/badge/React-18.0+-61DAFB.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000.svg)
![InsightFace](https://img.shields.io/badge/AI-InsightFace_Buffalo__L-orange.svg)
![DeepFace](https://img.shields.io/badge/FER-DeepFace-red.svg)

An end-to-end **Biometric Attendance System** that leverages Computer Vision and Deep Learning to automate classroom attendance. Beyond simple identification, the system performs **Facial Emotion Recognition (FER)** to provide teachers with real-time "Class Vibe" analytics and automated absentee notifications.

---
## Live Demo 

https://github.com/user-attachments/assets/20396f07-469b-40e5-91f8-3b4326a3f5fd


---
## 🌟 Key Features

| Feature | Description |
|---|---|
| 🎯 **High-Precision Face Recognition** | InsightFace Buffalo_L model with normalized 512-D embeddings and Cosine Similarity |
| 📊 **Real-time Sentiment Analysis** | Integrated DeepFace engine tracking emotions (Happy, Focused, Bored, Confused) in live streams |
| 📈 **Class Vibe Dashboard** | Dynamic "Engagement Bar" with temporal smoothing (deque buffer) for a stable satisfaction score |
| 📧 **Automated Email Alerts** | SMTP-based engine that identifies absentees and alerts parents at session end |
| 📥 **Session Snapshots & Export** | Save class history and export detailed reports (including mood data) to `.xlsx` |
| 🛠️ **Clean Registration Workflow** | Dedicated enrollment mode without detection overlays for high-quality biometric capture |

---

## 🛠 Tech Stack

### AI & Computer Vision
- **[InsightFace (Buffalo_L)](https://github.com/deepinsight/insightface)** — SOTA face detection and 512-D embedding extraction
- **[DeepFace](https://github.com/serengil/deepface)** — Deep CNN for precise emotion classification
- **OpenCV** — Low-latency video frame capture and MJPEG streaming
- **CoreML / ONNX** — Optimized inference for Apple Silicon (M-series)

### Backend (Python)
- **Flask** — Lightweight REST API for AI orchestration
- **Multi-threading** — Concurrent capture, processing, and web serving
- **Pickle & JSON** — Hybrid storage for binary embeddings and student metadata
- **SMTP** - email alerts

### Frontend (JavaScript)
- **React.js** — Single-page dashboard with real-time state synchronization
- **Axios** — Asynchronous API communication
- **SheetJS (XLSX)** — Client-side data parsing and Excel export

---

## 🏗 System Architecture
```
┌─────────────────┐    ┌──────────────────────────────────┐    ┌───────────────────┐
│  Capture Layer  │───▶│           Logic Layer            │───▶│ Persistence Layer │
│  MJPEG Stream   │    │  Thread A: 512D Vector Matching  │    │  JSON + Pickle    │
│  (IP Camera /   │    │  Thread B: Emotion/Engagement    │    │  Atomic Updates   │
│   Phone)        │    │           Scoring                │    └───────────────────┘
└─────────────────┘    └──────────────────────────────────┘             │
                                                                        ▼
                                                               ┌───────────────────┐
                                                               │     UI Layer      │
                                                               │  React Dashboard  │
                                                               │  Polls every 1.5s │
                                                               └───────────────────┘
```

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.13+
- Node.js & npm
- Google App Password (for SMTP email alerts)

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
npm start
```

---

## ⚙️ Configuration

Open `backend/main.py` and update:
```python
CAMERA_URL      = "http://your-ip-camera-url/video"
SENDER_EMAIL    = "your-email@gmail.com"
SENDER_PASSWORD = "your-16-char-app-password"
```

> **Tip:** Generate a Google App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords). Do **not** use your regular Gmail password.

---

## 📊 Analytics Logic

The **Class Vibe Score** is a weighted average of detected emotions across all visible faces, smoothed over a rolling buffer of **40 frames** to eliminate UI jitter.

| Emotion | Score |
|---|:---:|
| 😊 Satisfied | 100 |
| 🤩 Interested | 85 |
| 😐 Focused | 70 |
| 🥱 Bored | 40 |
| 😖 Confused | 25 |





---

## 🤝 Contributors

-  Muhammed hafan
-  Contact : https://www.linkedin.com/in/muhammed-hafan/

