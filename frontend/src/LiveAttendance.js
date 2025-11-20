import React, { useState, useEffect } from "react";
import axios from "axios";

function LiveAttendance() {
  const [results, setResults] = useState([]);

  // Your fixed phone camera URL (match backend!)
  const CAMERA_URL = "http://10.208.138.152:8080/video";

  useEffect(() => {
    // Auto-load camera stream when page opens
    const imgElement = document.getElementById("live_camera_feed");
    if (imgElement) {
      imgElement.src = CAMERA_URL;
    }
  }, []);

  const startAttendance = async () => {
    try {
      const res = await axios.post("http://127.0.0.1:8000/start-attendance");
      if (res.data.detected) {
        setResults(res.data.detected);
      }
    } catch (err) {
      console.error("Error starting attendance:", err);
    }
  };

  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-blue-600 mb-4">
        Live Attendance
      </h1>

      {/* Live phone camera feed */}
      <img
        id="live_camera_feed"
        alt="Camera Feed"
        className="w-96 h-64 bg-black rounded shadow mb-4"
      />

      {/* Start Attendance Button */}
      <button
        onClick={startAttendance}
        className="bg-green-600 text-white px-4 py-2 rounded"
      >
        Start Attendance
      </button>

      {/* Results */}
      <div className="mt-6">
        <h2 className="text-xl font-semibold">Detected Students:</h2>

        {results.length === 0 && (
          <p className="text-gray-500">No detections yet…</p>
        )}

        {results.map((item, idx) => (
          <div
            key={idx}
            className="p-4 bg-white shadow rounded mt-3 text-lg"
          >
            <strong>{item.Register_No}</strong> – {item.Time}
            <span className="text-green-600 font-semibold">
              {" "}({item.Status})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default LiveAttendance;
