import React, { useState, useEffect, useRef } from "react";

function RegisterStudent() {
  const imgRef = useRef(null);
  const canvasRef = useRef(null);

  const [cameraUrl, setCameraUrl] = useState(""); // This will now hold the backend proxy URL
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState("");
  const [capturedImage, setCapturedImage] = useState(null);

  // Form fields
  const [name, setName] = useState("");
  const [registerNo, setRegisterNo] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [section, setSection] = useState("");

  // Corrected BACKEND_URL to match your Flask server
  const BACKEND_URL = "http://localhost:5000";

  // ------------------ Setup Camera Proxy URL ------------------
  useEffect(() => {
    // This useEffect simply sets the URL for the proxy endpoint
    // No actual fetch is needed here, just setting the state.
    setCameraUrl(`${BACKEND_URL}/register_camera_frame`);
    setLoading(false); // We are no longer "loading" a URL, just setting it.
    console.log("✅ Camera proxy URL set for fetching frames.");
  }, []); // Run once on mount

  // ------------------ LIVE IMAGE STREAM (from backend proxy) ------------------
  useEffect(() => {
    if (!cameraUrl || !imgRef.current) return;

    let interval;
    let previousObjectUrl = null; // To manage Blob URLs for memory efficiency

    const updateFrame = async () => {
      try {
        const res = await fetch(cameraUrl); // Fetch from the backend proxy endpoint
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);

        const data = await res.json();

        if (data.content) {
          const base64String = data.content;
          // Convert base64 to Blob and create Object URL
          const byteCharacters = atob(base64String);
          const byteNumbers = new Array(byteCharacters.length);
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: "image/jpeg" });

          // Revoke previous Object URL to prevent memory leaks
          if (previousObjectUrl) {
            URL.revokeObjectURL(previousObjectUrl);
          }

          const newObjectUrl = URL.createObjectURL(blob);
          previousObjectUrl = newObjectUrl;

          if (imgRef.current) {
            imgRef.current.src = newObjectUrl;
          }
          setErrorMsg(""); // Clear error if successful
        } else if (data.error) {
          setErrorMsg(`Backend camera proxy error: ${data.error}`);
        }
      } catch (err) {
        console.error("Camera frame update error:", err);
        setErrorMsg(`Camera feed error: ${err.message}`);
      }
    };

    // Start fetching frames repeatedly
    updateFrame(); // Fetch immediately
    interval = setInterval(updateFrame, 100); // Update every 100ms (10 FPS)

    return () => {
      clearInterval(interval); // Clear interval on component unmount
      if (previousObjectUrl) {
        URL.revokeObjectURL(previousObjectUrl); // Revoke last object URL
      }
    };
  }, [cameraUrl]); // Re-run if cameraUrl changes

  // ------------------ CAPTURE IMAGE ------------------
  const captureFace = () => {
    if (!imgRef.current || !imgRef.current.src || imgRef.current.src.startsWith('data:image/gif')) { // Check for actual image data
      alert("Camera feed not ready or no image loaded. Please wait...");
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = imgRef.current;

    if (!img.complete) {
      alert("Image not fully loaded. Please wait a moment.");
      return;
    }

    canvas.width = img.naturalWidth || img.width || 640;
    canvas.height = img.naturalHeight || img.height || 480;

    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    const base64data = canvas.toDataURL("image/jpeg", 0.95);
    setCapturedImage(base64data);
    console.log(`Captured image: ${canvas.width}x${canvas.height}`);
  };

  // ------------------ SUBMIT REGISTRATION ------------------
  const handleSubmit = async () => {
    if (!capturedImage) {
      alert("Please capture a face first!");
      return;
    }

    if (!name || !registerNo || !rollNo || !section) {
      alert("Please fill all student details!");
      return;
    }

    try {
      const response = await fetch(capturedImage);
      const blob = await response.blob();

      const formData = new FormData();
      formData.append("name", name);
      formData.append("reg_no", registerNo);
      formData.append("roll_no", rollNo);
      formData.append("section", section);
      formData.append("image", blob, `${registerNo}.jpg`);

      const res = await fetch(`${BACKEND_URL}/register`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.status === "success") {
        alert(data.message || "Registered successfully!");
        setName("");
        setRegisterNo("");
        setRollNo("");
        setSection("");
        setCapturedImage(null);
      } else {
        alert(data.message || data.error || "Registration failed.");
      }
    } catch (err) {
      console.error("Registration error:", err);
      alert(`Registration error: ${err.message}`);
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h1>Register Student</h1>

      {errorMsg && (
        <p style={{ color: "red", fontWeight: "bold", whiteSpace: "pre-wrap" }}>
          {errorMsg}
        </p>
      )}
      {loading && <p style={{ color: "orange" }}>Loading camera...</p>}

      {/* LIVE CAMERA FEED - src will be updated by useEffect */}
      <img
        ref={imgRef}
        src="" // Start with empty src, useEffect will update it with blob URLs
        alt="Live Camera"
        width={640}
        height={480}
        style={{
          border: "2px solid black",
          background: "black",
          display: "block",
          marginBottom: 10,
        }}
      />

      <button
        onClick={captureFace}
        disabled={!cameraUrl || loading}
        style={{
          padding: "10px 20px",
          background: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          opacity: (!cameraUrl || loading) ? 0.5 : 1,
        }}
      >
        Capture Face
      </button>

      <h3>Captured Image</h3>
      {capturedImage ? (
        <img src={capturedImage} alt="Captured" width={400} style={{ border: "2px solid green" }} />
      ) : (
        <p>No image captured</p>
      )}

      <canvas ref={canvasRef} style={{ display: "none" }} />

      <h3>Student Details</h3>

      <input
        placeholder="Full Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={{ padding: "8px", marginBottom: "10px", width: "200px" }}
      />
      <br />

      <input
        placeholder="Register Number"
        value={registerNo}
        onChange={(e) => setRegisterNo(e.target.value)}
        style={{ padding: "8px", marginBottom: "10px", width: "200px" }}
      />
      <br />

      <input
        placeholder="Roll Number"
        value={rollNo}
        onChange={(e) => setRollNo(e.target.value)}
        style={{ padding: "8px", marginBottom: "10px", width: "200px" }}
      />
      <br />

      <input
        placeholder="Section"
        value={section}
        onChange={(e) => setSection(e.target.value)}
        style={{ padding: "8px", marginBottom: "10px", width: "200px" }}
      />
      <br />

      <button
        onClick={handleSubmit}
        disabled={!capturedImage || !name || !registerNo || !rollNo || !section}
        style={{
          background: "blue",
          color: "white",
          padding: "10px 20px",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          marginTop: "10px",
          opacity: (!capturedImage || !name || !registerNo || !rollNo || !section) ? 0.5 : 1,
        }}
      >
        Submit
      </button>
    </div>
  );
}

export default RegisterStudent;