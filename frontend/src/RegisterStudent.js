


import React, { useState, useEffect, useRef } from "react";

function RegisterStudent() {
  const imgRef = useRef(null);
  const canvasRef = useRef(null);
  const BACKEND_URL = "http://127.0.0.1:5050"; 

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [capturedImage, setCapturedImage] = useState(null);

  const [name, setName] = useState("");
  const [registerNo, setRegisterNo] = useState("");
  const [email, setEmail] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [section, setSection] = useState("");

  useEffect(() => {
    if (imgRef.current) {
      imgRef.current.src = `${BACKEND_URL}/video_feed_clean`;
    }
  }, []);

  const captureFace = () => {
    if (!imgRef.current || !imgRef.current.complete || imgRef.current.naturalWidth === 0) {
      alert("Camera feed not ready.");
      return;
    }
    const canvas = canvasRef.current;
    canvas.width = imgRef.current.naturalWidth;
    canvas.height = imgRef.current.naturalHeight;
    canvas.getContext("2d").drawImage(imgRef.current, 0, 0);
    setCapturedImage(canvas.toDataURL("image/jpeg", 0.95));
  };

  const handleSubmit = async () => {
    if (!capturedImage || !name || !registerNo) {
      alert("Please capture photo and fill Name/Reg No.");
      return;
    }
    try {
      setLoading(true);
      const blob = await (await fetch(capturedImage)).blob();
      const formData = new FormData();
      formData.append("name", name);
      formData.append("reg_no", registerNo);
      formData.append("email", email);
      formData.append("roll_no", rollNo);
      formData.append("section", section);
      formData.append("image", blob, `${registerNo}.jpg`);

      const res = await fetch(`${BACKEND_URL}/register`, { 
        method: "POST", 
        body: formData 
      });

      const data = await res.json();
      if (res.ok) {
        alert("Registration Success: " + data.message);
        setName(""); setRegisterNo(""); setEmail(""); setRollNo(""); setSection("");
        setCapturedImage(null);
      } else {
        alert("Server Error: " + (data.message || "Unknown error"));
      }
    } catch (err) {
      console.error(err);
      alert("Connection Failed. Make sure main.py is running on port 5050.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{backgroundColor: '#121212', minHeight: '100vh', padding: '20px', color: 'white'}}> 
      <div style={{maxWidth: '500px', margin: '0 auto', backgroundColor: '#1e1e1e', padding: '30px', borderRadius: '20px', border: '1px solid #333'}}> 
        <h1 style={{textAlign: 'center', marginBottom: '20px'}}>Register Student</h1>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <img ref={imgRef} alt="Feed" style={{ width: '100%', borderRadius: '15px', backgroundColor: '#000' }} crossOrigin="anonymous" />
          <button onClick={captureFace} style={{marginTop: '15px', backgroundColor: '#22c55e', color: 'white', padding: '10px 20px', border: 'none', borderRadius: '8px', cursor: 'pointer'}}>Capture Face</button>
        </div>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          {capturedImage && <img src={capturedImage} alt="Captured" style={{ width: '120px', height: '120px', borderRadius: '50%', objectFit: 'cover', border: '3px solid #22c55e' }} />}
        </div>
        <canvas ref={canvasRef} style={{ display: "none" }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <input placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} style={inS} />
          <input placeholder="Register Number" value={registerNo} onChange={(e) => setRegisterNo(e.target.value)} style={inS} />
          <input placeholder="Parent Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} style={inS} />
          <input placeholder="Roll Number" value={rollNo} onChange={(e) => setRollNo(e.target.value)} style={inS} />
          <input placeholder="Section" value={section} onChange={(e) => setSection(e.target.value)} style={inS} />
          <button onClick={handleSubmit} disabled={loading} style={{...btnS, backgroundColor: loading ? '#555' : '#d97706'}}>{loading ? "Registering..." : "Submit Registration"}</button>
        </div>
      </div>
    </div>
  );
}

const inS = { width: '100%', padding: '12px', borderRadius: '8px', border: '1px solid #333', backgroundColor: '#2a2a2a', color: 'white' };
const btnS = { marginTop: '10px', padding: '15px', border: 'none', borderRadius: '8px', color: 'white', fontWeight: 'bold', cursor: 'pointer' };

export default RegisterStudent;