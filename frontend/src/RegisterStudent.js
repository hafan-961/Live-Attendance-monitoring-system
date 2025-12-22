// import React, { useState, useEffect, useRef } from "react";
// // We don't need to import a specific CSS file here if we put styles in index.css

// function RegisterStudent() {
//   const imgRef = useRef(null);
//   const canvasRef = useRef(null);

//   const [cameraUrl, setCameraUrl] = useState("");
//   const [loading, setLoading] = useState(true);
//   const [errorMsg, setErrorMsg] = useState("");
//   const [capturedImage, setCapturedImage] = useState(null);

//   // Form fields
//   const [name, setName] = useState("");
//   const [registerNo, setRegisterNo] = useState("");
//   const [email, setEmail] = useState("");
//   const [rollNo, setRollNo] = useState("");
//   const [section, setSection] = useState("");

//   const BACKEND_URL = "http://127.0.0.1:8000"; // Assuming FastAPI is on 8000

//   // ------------------ Fetch Camera URL from FastAPI ------------------
//   useEffect(() => {
//     async function fetchCameraEndpoint() {
//       try {
//         setLoading(true);
//         const res = await fetch(`${BACKEND_URL}/camera_url`); // Call your FastAPI endpoint
//         if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
//         const data = await res.json();
//         if (data.image_url) {
//           setCameraUrl(data.image_url); // This is the IP Webcam URL
//           setErrorMsg(""); // Clear any previous errors
//         } else {
//           setErrorMsg("Camera URL not found in backend response.");
//         }
//       } catch (err) {
//         console.error("Failed to fetch camera URL from backend:", err);
//         setErrorMsg(`Failed to get camera URL. Is the backend running? (${err.message})`);
//       } finally {
//         setLoading(false);
//       }
//     }
//     fetchCameraEndpoint();
//   }, []);

//   // ------------------ LIVE IMAGE STREAM (from actual camera URL) ------------------
//   useEffect(() => {
//     if (!cameraUrl || !imgRef.current) return;

//     let interval;
//     // We don't need blob URLs here anymore because cameraUrl is directly a JPEG stream

//     const updateFrame = () => {
//       // Appending a timestamp breaks browser caching and forces a fresh image from the camera stream
//       if (imgRef.current) {
//         imgRef.current.src = `${cameraUrl}?t=${Date.now()}`;
//       }
//     };

//     updateFrame(); // Fetch immediately
//     interval = setInterval(updateFrame, 300); // Update every 300ms (adjust as needed for fluidity vs. network load)

//     return () => clearInterval(interval); // Clear interval on component unmount
//   }, [cameraUrl]);

//   // ------------------ CAPTURE IMAGE ------------------
//   const captureFace = () => {
//     if (!imgRef.current || !imgRef.current.src || imgRef.current.src.startsWith('data:image/gif')) {
//       alert("Camera feed not ready or no image loaded. Please wait...");
//       return;
//     }

//     const canvas = canvasRef.current;
//     const ctx = canvas.getContext("2d");
//     const img = imgRef.current;

//     // Ensure image is fully loaded before drawing
//     if (!img.complete) {
//         alert("Image not fully loaded. Please wait a moment.");
//         return;
//     }

//     // Use natural dimensions if available, fallback to display size or fixed
//     canvas.width = img.naturalWidth || img.width || 640;
//     canvas.height = img.naturalHeight || img.height || 480;

//     ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
//     const base64data = canvas.toDataURL("image/jpeg", 0.95);
//     setCapturedImage(base64data);
//     console.log(`Captured image: ${canvas.width}x${canvas.height}`);
//   };

//   // ------------------ SUBMIT REGISTRATION ------------------
//   const handleSubmit = async () => {
//     if (!capturedImage) {
//       alert("Please capture a face first!");
//       return;
//     }
//     if (!name || !registerNo || !email || !rollNo || !section) {
//       alert("Please fill all student details including Email!");
//       return;
//     }

//     try {
//       const response = await fetch(capturedImage);
//       const blob = await response.blob();

//       const formData = new FormData();
//       formData.append("name", name);
//       formData.append("reg_no", registerNo);
//       formData.append("email", email);
//       formData.append("roll_no", rollNo);
//       formData.append("section", section);
//       formData.append("image", blob, `${registerNo}.jpg`);

//       const res = await fetch(`${BACKEND_URL}/register`, {
//         method: "POST",
//         body: formData,
//       });

//       const data = await res.json();

//       if (res.ok) { // Check for HTTP success status (200-299)
//         alert(data.message || "Registered successfully!");
//         setName("");
//         setRegisterNo("");
//         setEmail("");
//         setRollNo("");
//         setSection("");
//         setCapturedImage(null);
//       } else {
//         alert(data.message || data.error || "Registration failed.");
//       }
//     } catch (err) {
//       console.error("Registration error:", err);
//       alert(`Registration error: ${err.message}`);
//     }
//   };

//   return (
//     <div className="register-student-page"> {/* Main page container */}
//       <div className="form-card"> {/* Card container for the form */}
//         <h1 className="form-title">Register Student</h1>

//         {errorMsg && (
//           <p className="error-message">
//             {errorMsg}
//           </p>
//         )}
//         {loading && <p className="loading-message">Loading camera...</p>}

//         <div className="camera-section">
//           <img
//             ref={imgRef}
//             src=""
//             alt="Live Camera Feed"
//             className="live-camera-feed"
//             width={640} // You can manage these with CSS max-width now
//             height={480} // but keeping for initial sizing
//           />
//           <button
//             onClick={captureFace}
//             disabled={!cameraUrl || loading}
//             className="btn-primary capture-button"
//           >
//             Capture Face
//           </button>
//         </div>

//         <div className="captured-image-section">
//           <h3 className="section-title">Captured Image</h3>
//           {capturedImage ? (
//             <img src={capturedImage} alt="Captured" className="captured-image" />
//           ) : (
//             <p className="no-image-message">No image captured</p>
//           )}
//         </div>

//         <canvas ref={canvasRef} style={{ display: "none" }} /> {/* Hidden canvas */}

//         <div className="student-details-section">
//           <h3 className="section-title">Student Details</h3>
//           <div className="input-group">
//             <input
//               placeholder="Full Name"
//               value={name}
//               onChange={(e) => setName(e.target.value)}
//               className="themed-input"
//             />
//           </div>
//           <div className="input-group">
//             <input
//               placeholder="Register Number"
//               value={registerNo}
//               onChange={(e) => setRegisterNo(e.target.value)}
//               className="themed-input"
//             />
//           </div>
//           <div className="input-group">
//             <input
//               placeholder="Parent Email"
//               type="email"
//               value={email}
//               onChange={(e) => setEmail(e.target.value)}
//               className="themed-input"
//             />
//           </div>
//           <div className="input-group">
//             <input
//               placeholder="Roll Number"
//               value={rollNo}
//               onChange={(e) => setRollNo(e.target.value)}
//               className="themed-input"
//             />
//           </div>
//           <div className="input-group">
//             <input
//               placeholder="Section"
//               value={section}
//               onChange={(e) => setSection(e.target.value)}
//               className="themed-input"
//             />
//           </div>

//           <button
//             onClick={handleSubmit}
//             disabled={!capturedImage || !name || !registerNo || !email || !rollNo || !section}
//             className="btn-primary submit-button"
//           >
//             Submit Registration
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default RegisterStudent;



















// import React, { useState, useEffect, useRef } from "react";

// function RegisterStudent() {
//   const imgRef = useRef(null);
//   const canvasRef = useRef(null);

//   // --- CONFIGURATION ---
//   // Updated to 5000 to match your Flask main.py
//   const BACKEND_URL = "http://127.0.0.1:5000"; 

//   const [loading, setLoading] = useState(false);
//   const [errorMsg, setErrorMsg] = useState("");
//   const [capturedImage, setCapturedImage] = useState(null);

//   // Form fields
//   const [name, setName] = useState("");
//   const [registerNo, setRegisterNo] = useState("");
//   const [email, setEmail] = useState("");
//   const [rollNo, setRollNo] = useState("");
//   const [section, setSection] = useState("");

//   // ------------------ Initialize Camera Stream ------------------
//   useEffect(() => {
//     // We don't need to fetch a URL first. 
//     // Your Flask backend serves the stream directly at /video_feed
//     const streamUrl = `${BACKEND_URL}/video_feed`;
    
//     if (imgRef.current) {
//       imgRef.current.src = streamUrl;
//     }

//     // Check if the backend is reachable
//     fetch(`${BACKEND_URL}/students`)
//       .then(() => setErrorMsg(""))
//       .catch(() => setErrorMsg("Cannot connect to Backend. Is main.py running on port 5000?"));
//   }, []);

//   // ------------------ CAPTURE IMAGE ------------------
//   const captureFace = () => {
//     if (!imgRef.current || !imgRef.current.complete || imgRef.current.naturalWidth === 0) {
//       alert("Camera feed not ready. Please wait for the video to appear.");
//       return;
//     }

//     const canvas = canvasRef.current;
//     const ctx = canvas.getContext("2d");
//     const img = imgRef.current;

//     // Use actual dimensions of the stream
//     canvas.width = img.naturalWidth;
//     canvas.height = img.naturalHeight;

//     ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    
//     // Convert canvas to base64 for preview
//     const base64data = canvas.toDataURL("image/jpeg", 0.95);
//     setCapturedImage(base64data);
//   };

//   // ------------------ SUBMIT REGISTRATION ------------------
//   const handleSubmit = async () => {
//     if (!capturedImage) {
//       alert("Please capture a face first!");
//       return;
//     }
//     if (!name || !registerNo || !email || !rollNo || !section) {
//       alert("Please fill all student details!");
//       return;
//     }

//     try {
//       setLoading(true);
//       // Convert base64 preview to a Blob file for upload
//       const response = await fetch(capturedImage);
//       const blob = await response.blob();

//       const formData = new FormData();
//       formData.append("name", name);
//       formData.append("reg_no", registerNo);
//       formData.append("email", email);
//       formData.append("roll_no", rollNo);
//       formData.append("section", section);
//       // Key must be 'image' to match your main.py: request.files['image']
//       formData.append("image", blob, `${registerNo}.jpg`);

//       const res = await fetch(`${BACKEND_URL}/register`, {
//         method: "POST",
//         body: formData,
//       });

//       const data = await res.json();

//       if (res.ok) {
//         alert(data.message || "Registered successfully!");
//         // Clear Form
//         setName(""); setRegisterNo(""); setEmail(""); setRollNo(""); setSection("");
//         setCapturedImage(null);
//       } else {
//         alert(data.message || "Registration failed.");
//       }
//     } catch (err) {
//       console.error("Registration error:", err);
//       alert("Server Error: Could not submit registration.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   return (
//     <div className="register-student-page"> 
//       <div className="form-card"> 
//         <h1 className="form-title">Register Student</h1>

//         {errorMsg && (
//           <p className="error-message" style={{ color: 'white', backgroundColor: '#ef4444', padding: '10px', borderRadius: '5px', marginBottom: '15px' }}>
//             {errorMsg}
//           </p>
//         )}

//         <div className="camera-section" style={{ textAlign: 'center' }}>
//           <img
//             ref={imgRef}
//             alt="Live Camera Feed"
//             className="live-camera-feed"
//             style={{ width: '100%', borderRadius: '10px', backgroundColor: 'black', minHeight: '300px' }}
//             crossOrigin="anonymous"
//             onError={() => setErrorMsg("Camera Stream Offline. Check if main.py is running.")}
//           />
//           <button
//             onClick={captureFace}
//             className="btn-primary capture-button"
//             style={{ marginTop: '15px', backgroundColor: '#22c55e', padding: '10px 20px', borderRadius: '5px', color: 'white' }}
//           >
//             Capture Face
//           </button>
//         </div>

//         <div className="captured-image-section" style={{ marginTop: '20px', textAlign: 'center' }}>
//           <h3 className="section-title">Captured Image</h3>
//           {capturedImage ? (
//             <img src={capturedImage} alt="Captured" className="captured-image" style={{ width: '150px', borderRadius: '10px', border: '2px solid #22c55e' }} />
//           ) : (
//             <p className="no-image-message" style={{ color: '#9ca3af' }}>No image captured</p>
//           )}
//         </div>

//         <canvas ref={canvasRef} style={{ display: "none" }} />

//         <div className="student-details-section" style={{ marginTop: '30px' }}>
//           <h3 className="section-title">Student Details</h3>
//           <div className="input-group">
//             <input placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} className="themed-input" />
//           </div>
//           <div className="input-group">
//             <input placeholder="Register Number" value={registerNo} onChange={(e) => setRegisterNo(e.target.value)} className="themed-input" />
//           </div>
//           <div className="input-group">
//             <input placeholder="Parent Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="themed-input" />
//           </div>
//           <div className="input-group">
//             <input placeholder="Roll Number" value={rollNo} onChange={(e) => setRollNo(e.target.value)} className="themed-input" />
//           </div>
//           <div className="input-group">
//             <input placeholder="Section" value={section} onChange={(e) => setSection(e.target.value)} className="themed-input" />
//           </div>

//           <button
//             onClick={handleSubmit}
//             disabled={loading || !capturedImage || !name || !registerNo}
//             className="btn-primary submit-button"
//             style={{ width: '100%', marginTop: '20px', backgroundColor: loading ? '#9ca3af' : '#d97706', padding: '15px', borderRadius: '5px', color: 'white', fontWeight: 'bold' }}
//           >
//             {loading ? "Registering..." : "Submit Registration"}
//           </button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default RegisterStudent;









import React, { useState, useEffect, useRef } from "react";

function RegisterStudent() {
  const imgRef = useRef(null);
  const canvasRef = useRef(null);

  const BACKEND_URL = "http://127.0.0.1:5000"; 

  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [capturedImage, setCapturedImage] = useState(null);

  const [name, setName] = useState("");
  const [registerNo, setRegisterNo] = useState("");
  const [email, setEmail] = useState("");
  const [rollNo, setRollNo] = useState("");
  const [section, setSection] = useState("");

  // ------------------ Initialize Camera Stream ------------------
  useEffect(() => {
    // --- CHANGED: Now using the "Clean" feed without boxes ---
    const streamUrl = `${BACKEND_URL}/video_feed_clean`;
    
    if (imgRef.current) {
      imgRef.current.src = streamUrl;
    }

    fetch(`${BACKEND_URL}/students`)
      .then(() => setErrorMsg(""))
      .catch(() => setErrorMsg("Cannot connect to Backend. Is main.py running?"));
  }, []);

  // ------------------ CAPTURE IMAGE ------------------
  const captureFace = () => {
    if (!imgRef.current || !imgRef.current.complete || imgRef.current.naturalWidth === 0) {
      alert("Camera feed not ready.");
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const img = imgRef.current;

    canvas.width = img.naturalWidth;
    canvas.height = img.naturalHeight;
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    
    const base64data = canvas.toDataURL("image/jpeg", 0.95);
    setCapturedImage(base64data);
  };

  const handleSubmit = async () => {
    if (!capturedImage || !name || !registerNo) {
      alert("Please fill details and capture a face!");
      return;
    }
    try {
      setLoading(true);
      const response = await fetch(capturedImage);
      const blob = await response.blob();
      const formData = new FormData();
      formData.append("name", name);
      formData.append("reg_no", registerNo);
      formData.append("email", email);
      formData.append("roll_no", rollNo);
      formData.append("section", section);
      formData.append("image", blob, `${registerNo}.jpg`);

      const res = await fetch(`${BACKEND_URL}/register`, { method: "POST", body: formData });
      const data = await res.json();
      if (res.ok) {
        alert(data.message || "Registered successfully!");
        setName(""); setRegisterNo(""); setEmail(""); setRollNo(""); setSection("");
        setCapturedImage(null);
      } else { alert(data.message || "Failed."); }
    } catch (err) { alert("Server Error."); } finally { setLoading(false); }
  };

  return (
    <div className="register-student-page"> 
      <div className="form-card"> 
        <h1 className="form-title">Register Student</h1>
        {errorMsg && <p className="error-message" style={{ color: 'white', backgroundColor: '#ef4444', padding: '10px', borderRadius: '5px', marginBottom: '15px' }}>{errorMsg}</p>}

        <div className="camera-section" style={{ textAlign: 'center' }}>
          <img
            ref={imgRef}
            alt="Live Camera Feed"
            className="live-camera-feed"
            style={{ width: '100%', borderRadius: '10px', backgroundColor: 'black', minHeight: '300px' }}
            crossOrigin="anonymous"
          />
          <button onClick={captureFace} className="btn-primary capture-button" style={{ marginTop: '15px', backgroundColor: '#22c55e', padding: '10px 20px', borderRadius: '5px', color: 'white' }}>
            Capture Face
          </button>
        </div>

        <div className="captured-image-section" style={{ marginTop: '20px', textAlign: 'center' }}>
          <h3 className="section-title">Captured Image</h3>
          {capturedImage ? <img src={capturedImage} alt="Captured" style={{ width: '150px', borderRadius: '10px', border: '2px solid #22c55e' }} /> : <p style={{ color: '#9ca3af' }}>No image captured</p>}
        </div>

        <canvas ref={canvasRef} style={{ display: "none" }} />
        <div className="student-details-section" style={{ marginTop: '30px' }}>
          <h3 className="section-title">Student Details</h3>
          <input placeholder="Full Name" value={name} onChange={(e) => setName(e.target.value)} className="themed-input" style={{ width: '100%', marginBottom: '10px', padding: '10px' }} />
          <input placeholder="Register Number" value={registerNo} onChange={(e) => setRegisterNo(e.target.value)} className="themed-input" style={{ width: '100%', marginBottom: '10px', padding: '10px' }} />
          <input placeholder="Parent Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="themed-input" style={{ width: '100%', marginBottom: '10px', padding: '10px' }} />
          <input placeholder="Roll Number" value={rollNo} onChange={(e) => setRollNo(e.target.value)} className="themed-input" style={{ width: '100%', marginBottom: '10px', padding: '10px' }} />
          <input placeholder="Section" value={section} onChange={(e) => setSection(e.target.value)} className="themed-input" style={{ width: '100%', marginBottom: '20px', padding: '10px' }} />
          <button onClick={handleSubmit} disabled={loading || !capturedImage || !name || !registerNo} className="btn-primary submit-button" style={{ width: '100%', backgroundColor: loading ? '#9ca3af' : '#d97706', padding: '15px', borderRadius: '5px', color: 'white', fontWeight: 'bold' }}>
            {loading ? "Registering..." : "Submit Registration"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default RegisterStudent;