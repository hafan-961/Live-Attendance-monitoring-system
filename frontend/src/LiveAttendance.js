
import React, { useState, useEffect } from 'react';
import './LiveAttendance.css'; 

function LiveAttendance() {
  const [attendance, setAttendance] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  // Use 127.0.0.1 to avoid common 'localhost' network resolution issues
  const BACKEND_URL = 'http://127.0.0.1:5000'; 

  const fetchAttendance = async () => {
    try {
      // Added timestamp ?t= to force the browser to get NEW data every time
      const response = await fetch(`${BACKEND_URL}/attendance_data?t=${Date.now()}`);
      if (!response.ok) throw new Error(`HTTP error!`);
      const data = await response.json();
      setAttendance(data);
      setError(null);
    } catch (e) { 
      console.error("Fetch Error:", e);
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => {
    fetchAttendance();
    const intervalId = setInterval(fetchAttendance, 3000); 
    return () => clearInterval(intervalId);
  }, []);

  const handleReset = async () => {
    if (!window.confirm("Are you sure? This will clear all current attendance.")) return;
    
    try {
        const response = await fetch(`${BACKEND_URL}/reset_attendance`, { method: 'POST' });
        const data = await response.json();
        if (data.status === 'success') {
            setAttendance({});
            alert("Attendance list cleared!");
        }
    } catch (err) {
        alert("Reset failed: Could not connect to server.");
    }
  };

  const handleEndSession = async () => {
    if (!window.confirm("End session and email parents of absent students?")) return;
    
    try {
        const response = await fetch(`${BACKEND_URL}/end_session_notify`, { method: 'POST' });
        const data = await response.json();
        
        if (response.ok) {
            alert(data.message);
        } else {
            alert("Server Error: " + (data.message || "Unknown error"));
        }
    } catch (e) {
        alert("Failed to trigger email system. Check if Backend is running.");
    }
  };

  return (
    <div className="live-attendance-container" style={{ backgroundColor: '#1a1a1a', color: 'white', minHeight: '100vh', padding: '20px' }}>
      <div className="header-container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px'}}>
          <h1 style={{ margin: 0 }}>Live Class Attendance</h1>
          
          <div>
            <button onClick={handleEndSession} style={btnStyle('#FF9800')}>
                End Session & Notify Absentees
            </button>
            <button onClick={handleReset} style={{...btnStyle('#ff4444'), marginLeft: '10px'}}>
                Reset List
            </button>
          </div>
      </div>

      <div className="video-section" style={{ border: '2px solid #333', borderRadius: '10px', overflow: 'hidden', marginBottom: '20px', backgroundColor: '#000' }}>
        <img 
          src={`${BACKEND_URL}/video_feed`} 
          alt="Live Camera Feed" 
          style={{ width: '100%', display: 'block' }}
          onError={() => setError("Video stream disconnected")} 
        />
      </div>

      <div className="attendance-section" style={{ backgroundColor: '#2d2d2d', padding: '20px', borderRadius: '10px' }}>
        <h2 style={{ borderBottom: '1px solid #444', paddingBottom: '10px' }}>Attendance Status</h2>
        {Object.keys(attendance).length === 0 ? (
          <p style={{ color: '#888', fontStyle: 'italic' }}>No attendance recorded yet.</p>
        ) : (
          <ul className="attendance-list" style={{ listStyle: 'none', padding: 0 }}>
            {Object.entries(attendance).map(([regNo, record]) => (
              <li key={regNo} className="attendance-item" style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid #3d3d3d' }}>
                <span style={{ fontWeight: 'bold' }}>{regNo}: <span style={{ color: '#4CAF50' }}>Present</span></span> 
                <span style={{ color: '#aaa' }}>{new Date(record.timestamp).toLocaleTimeString()}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

const btnStyle = (color) => ({
    backgroundColor: color, 
    color: 'white', 
    padding: '12px 24px', 
    border: 'none', 
    borderRadius: '6px',
    cursor: 'pointer',
    fontWeight: 'bold',
    fontSize: '14px'
});



export default LiveAttendance;


