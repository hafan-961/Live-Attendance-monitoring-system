import React, { useEffect, useRef, useState } from "react";

export default function RegisterStudent() {
  const imgRef = useRef(null);
  const canvasRef = useRef(null);

  const [cameraUrl, setCameraUrl] = useState("");
  const [capturedImage, setCapturedImage] = useState("");
  const [name, setName] = useState("");
  const [regNo, setRegNo] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [section, setSection] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [loading, setLoading] = useState(true);

  // BACKEND URL - Change this if your backend is on a different address
  const BACKEND_URL = "http://127.0.0.1:8000";

  // ------------------ GET CAMERA URL (from backend) ------------------
  useEffect(() => {
    async function loadCameraUrl() {
      try {
        console.log("Fetching camera URL from:", `${BACKEND_URL}/camera_url`);
        const res = await fetch(`${BACKEND_URL}/camera_url`);
        console.log("Response status:", res.status);
        
        if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        
        const data = await res.json();
        console.log("Camera URL response:", data);
        
        if (data.image_url) {
          setCameraUrl(data.image_url);
          setErrorMsg("");
          setLoading(false);
          console.log("✅ Camera URL loaded successfully");
        } else {
          setErrorMsg("Camera URL not found in backend response.");
          setLoading(false);
        }
      } catch (err) {
        console.error("Error:", err);
        setErrorMsg(
          `❌ Failed to connect to backend!\n\nMake sure:\n1. Backend is running on ${BACKEND_URL}\n2. Error: ${err.message}`
        );
        setLoading(false);
      }
    }

    loadCameraUrl();
  }, []);

  // ------------------ LIVE IMAGE STREAM ------------------
  useEffect(() => {
    if (!cameraUrl || !imgRef.current) return;

    let interval;
    const update = async () => {
      try {
        const res = await fetch(cameraUrl);
        if (!res.ok) throw new Error("Camera feed error");
        
        const data = await res.json();
        
        if (data.content) {
          // Convert base64 to blob and create object URL
          const base64String = data.content;
          const byteCharacters = atob(base64String);
          const byteNumbers = new Array(byteCharacters.length);
          
          for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
          }
          
          const byteArray = new Uint8Array(byteNumbers);
          const blob = new Blob([byteArray], { type: "image/jpeg" });
          const url = URL.createObjectURL(blob);
          
          imgRef.current.src = url;
          setErrorMsg("");
        } else if (data.error) {
          setErrorMsg(`Camera error: ${data.error}`);
        }
      } catch (err) {
        console.error("Camera update error:", err);
        setErrorMsg(`Camera feed error: ${err.message}`);
      }
    };

    update();
    interval = setInterval(update, 100); // Update every 500ms

    return () => {
      clearInterval(interval);
    };
  }, [cameraUrl]);

  // ------------------ CAPTURE IMAGE ------------------
  const captureFace = () => {
    if (!imgRef.current || !imgRef.current.src) {
      alert("Camera feed not ready. Please wait...");
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = imgRef.current;

    // Use naturalWidth and naturalHeight to get the actual image dimensions
    // This ensures we capture the full image, not just the displayed size
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

    if (!name || !regNo || !rollNo || !section) {
      alert("Please fill all student details!");
      return;
    }

    try {
      const blob = await (await fetch(capturedImage)).blob();
      const formData = new FormData();

      formData.append("name", name);
      formData.append("reg_no", regNo);
      formData.append("roll_no", rollNo);
      formData.append("section", section);
      formData.append("image", blob, "face.jpg");

      const res = await fetch(`${BACKEND_URL}/register`, {
        method: "POST",
        body: formData,
      });

      const data = await res.json();

      if (data.status === "success") {
        alert(data.message || "Registered successfully!");
        setName("");
        setRegNo("");
        setRollNo("");
        setSection("");
        setCapturedImage("");
      } else {
        alert(data.error || "Registration failed.");
      }
    } catch (err) {
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

      {/* LIVE CAMERA FEED */}
      <img
        ref={imgRef}
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
        style={{
          padding: "10px 20px",
          background: "#4CAF50",
          color: "white",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
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
        value={regNo}
        onChange={(e) => setRegNo(e.target.value)}
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
        style={{
          background: "blue",
          color: "white",
          padding: "10px 20px",
          border: "none",
          borderRadius: "5px",
          cursor: "pointer",
          marginTop: "10px",
        }}
      >
        Submit
      </button>
    </div>
  );
}