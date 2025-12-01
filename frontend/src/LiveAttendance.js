import React, { useState, useEffect, useRef, useCallback } from "react";

function LiveAttendance() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [cameraLoaded, setCameraLoaded] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);
  const imgRef = useRef(null);
  const [cameraUrl, setCameraUrl] = useState("");

  const BACKEND_URL = "http://127.0.0.1:8000";

  // Fetch camera URL on mount
  useEffect(() => {
    setCameraUrl(`${BACKEND_URL}/camera_feed`);
  }, []);

  // ------------------ LIVE IMAGE STREAM ------------------
  useEffect(() => {
    if (!cameraUrl || !imgRef.current) return;

    let interval;
    let previousUrl = null;

    const update = async () => {
      try {
        const res = await fetch(cameraUrl);
        if (!res.ok) throw new Error("Camera feed error");

        const data = await res.json();

        if (data.content) {
          const base64String = data.content;
          const byteCharacters = atob(base64String);
          const byteNumbers = new Array(byteCharacters.length);

          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }

          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: "image/jpeg" });

          if (previousUrl) {
            URL.revokeObjectURL(previousUrl);
          }

          const url = URL.createObjectURL(blob);
          previousUrl = url;

          if (imgRef.current) {
            imgRef.current.src = url;
            setCameraLoaded(true);
          }
          setErrorMsg("");
        } else if (data.error) {
          setErrorMsg(`Camera error: ${data.error}`);
          setCameraLoaded(false);
        }
      } catch (err) {
        console.error("Camera update error:", err);
        setErrorMsg(`Camera feed error: ${err.message}`);
        setCameraLoaded(false);
      }
    };

    update();
    interval = setInterval(update, 100);

    return () => {
      clearInterval(interval);
      if (previousUrl) {
        URL.revokeObjectURL(previousUrl);
      }
    };
  }, [cameraUrl]);

  // Start attendance marking
  const startAttendance = useCallback(async (isAuto = false) => {
    if (!cameraLoaded) {
      if (!isAuto) setErrorMsg("Camera not loaded yet. Please wait...");
      return;
    }

    try {
      setLoading(true);
      if (!isAuto) setErrorMsg("");

      console.log("📤 Sending attendance request to:", `${BACKEND_URL}/start_attendance`);

      const res = await fetch(`${BACKEND_URL}/start_attendance`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      console.log("📥 Response status:", res.status);

      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }

      const data = await res.json();
      console.log("📦 Response data:", data);

      if (data.status === "success") {
        if (data.detected && data.detected.length > 0) {
          console.log("✅ Students detected:", data.detected.length);
          
          setResults(prevResults => {
            const existingMap = new Map(prevResults.map(item => [item.Register_No, item]));
            data.detected.forEach(student => {
              existingMap.set(student.Register_No, student);
            });
            return Array.from(existingMap.values());
          });

          setErrorMsg("");
        } else {
          console.log("⚠️ No students detected in this frame");
          if (!isAuto) setErrorMsg("No registered students detected in the frame");
        }
      } else if (data.status === "no_face") {
        console.log("⚠️ No face detected");
        if (!isAuto) setErrorMsg("No face detected in the frame");
      } else if (data.error) {
        console.error("❌ Error from backend:", data.error);
        if (!isAuto) setErrorMsg(`Error: ${data.error}`);
      }

      setLoading(false);
    } catch (err) {
      console.error("❌ Attendance request failed:", err);
      setLoading(false);
      if (!isAuto) {
        setErrorMsg(`❌ Failed to start attendance: ${err.message}`);
      }
    }
  }, [cameraLoaded, BACKEND_URL]);

  // Live Mode Effect
  useEffect(() => {
    let interval;
    if (isLiveMode) {
      console.log("🔴 Live mode started");
      if (cameraLoaded) startAttendance(true);

      interval = setInterval(() => {
        if (cameraLoaded) {
          startAttendance(true);
        }
      }, 3000); // Check every 3 seconds
    } else {
      console.log("⏹ Live mode stopped");
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLiveMode, cameraLoaded, startAttendance]);

  return (
    <div style={{ padding: "32px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
        <h1 style={{ fontSize: "30px", fontWeight: "bold", color: "#2563eb", margin: 0 }}>
          Live Attendance
        </h1>

        {/* Live Mode Toggle */}
        <button
          onClick={() => setIsLiveMode(!isLiveMode)}
          style={{
            padding: "12px 24px",
            fontSize: "16px",
            fontWeight: "bold",
            color: "white",
            backgroundColor: isLiveMode ? "#ef4444" : "#3b82f6",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            transition: "background-color 0.3s"
          }}
        >
          {isLiveMode ? "⏹ Stop Live Mode" : "🔴 Start Live Mode"}
        </button>
      </div>

      {errorMsg && (
        <p style={{
          color: "red",
          fontWeight: "bold",
          marginBottom: "10px",
          whiteSpace: "pre-wrap",
          padding: "12px",
          backgroundColor: "#fee",
          borderRadius: "6px"
        }}>
          {errorMsg}
        </p>
      )}

      {!cameraLoaded && (
        <p style={{ 
          color: "#f59e0b", 
          fontWeight: "bold", 
          marginBottom: "10px",
          padding: "12px",
          backgroundColor: "#fef3c7",
          borderRadius: "6px"
        }}>
          📷 Loading camera...
        </p>
      )}

      {/* Live Camera Feed */}
      <div style={{ position: "relative", width: "640px", margin: "0 auto 20px" }}>
        <img
          ref={imgRef}
          alt="Camera Feed"
          width={640}
          height={480}
          style={{
            border: isLiveMode ? "4px solid #ef4444" : "2px solid black",
            background: "black",
            display: "block",
            borderRadius: "8px"
          }}
        />
        {isLiveMode && (
          <div style={{
            position: "absolute",
            top: "10px",
            right: "10px",
            backgroundColor: "rgba(239, 68, 68, 0.9)",
            color: "white",
            padding: "6px 12px",
            borderRadius: "4px",
            fontWeight: "bold",
            fontSize: "14px",
            animation: "pulse 2s infinite"
          }}>
            🔴 LIVE
          </div>
        )}
        {loading && (
          <div style={{
            position: "absolute",
            bottom: "10px",
            left: "50%",
            transform: "translateX(-50%)",
            backgroundColor: "rgba(0, 0, 0, 0.7)",
            color: "white",
            padding: "6px 12px",
            borderRadius: "4px",
            fontSize: "14px"
          }}>
            Scanning...
          </div>
        )}
      </div>

      {/* Manual Scan Button */}
      <div style={{ textAlign: "center", marginBottom: "20px" }}>
        <button
          onClick={() => startAttendance(false)}
          disabled={loading || !cameraLoaded || isLiveMode}
          style={{
            padding: "12px 32px",
            fontSize: "16px",
            fontWeight: "bold",
            color: "white",
            backgroundColor: (loading || !cameraLoaded || isLiveMode) ? "#9ca3af" : "#10b981",
            border: "none",
            borderRadius: "6px",
            cursor: (loading || !cameraLoaded || isLiveMode) ? "not-allowed" : "pointer",
            transition: "background-color 0.3s"
          }}
        >
          {loading ? "⏳ Scanning..." : "📸 Scan Now"}
        </button>
        <p style={{ marginTop: "8px", color: "#6b7280", fontSize: "14px" }}>
          {isLiveMode ? "Stop live mode to use manual scan" : "Click to manually detect faces"}
        </p>
      </div>

      {/* Debug Status */}
      <div style={{ 
        textAlign: "center", 
        marginBottom: "24px", 
        padding: "16px", 
        backgroundColor: "#f3f4f6", 
        borderRadius: "8px" 
      }}>
        <p style={{ fontWeight: "bold", marginBottom: "8px" }}>Debug Info:</p>
        <p>🎥 Live Mode: {isLiveMode ? "ON" : "OFF"}</p>
        <p>📷 Camera: {cameraLoaded ? "Ready" : "Loading..."}</p>
        <p>⚡ Status: {loading ? "Scanning..." : "Idle"}</p>
        <p>📊 Detected: {results.length} student(s)</p>
      </div>

      {/* Results */}
      <div style={{ marginTop: "32px" }}>
        <h2 style={{ fontSize: "24px", fontWeight: "600", marginBottom: "16px" }}>
          Detected Students: ({results.length})
        </h2>
        {results.length === 0 ? (
          <p style={{ color: "#6b7280", fontSize: "18px" }}>
            No detections yet. {isLiveMode ? "Live scanning in progress..." : "Click 'Start Live Mode' or 'Scan Now' to detect faces."}
          </p>
        ) : (
          <div style={{ display: "grid", gap: "12px" }}>
            {results.map((item, idx) => (
              <div
                key={idx}
                style={{
                  padding: "16px",
                  backgroundColor: "white",
                  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
                  borderRadius: "8px",
                  borderLeft: "4px solid #22c55e"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <p style={{ fontWeight: "bold", fontSize: "18px", margin: "0 0 8px 0" }}>
                      {item.Name}
                    </p>
                    <p style={{ color: "#666", margin: "4px 0" }}>
                      Reg: {item.Register_No} | Roll: {item.Roll_No}
                    </p>
                    <p style={{ color: "#666", margin: "4px 0" }}>
                      Section: {item.Section}
                    </p>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <p style={{ fontSize: "14px", color: "#999", margin: "0 0 8px 0" }}>
                      {item.Time}
                    </p>
                    <span style={{ color: "#22c55e", fontWeight: "bold", fontSize: "18px" }}>
                      ✅ {item.Status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default LiveAttendance;