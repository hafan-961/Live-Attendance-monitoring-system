

import React, { useState, useEffect } from 'react';
import './LiveAttendance.css'; 

function LiveAttendance() {
  const [attendance, setAttendance] = useState({});
  const [sentiment, setSentiment] = useState({ rating: "...", score: 0, count: 0 });
  const [error, setError] = useState(null);
  
  // Backend on Port 5050
  const BACKEND_URL = 'http://127.0.0.1:5050'; 

  const fetchData = async () => {
    try {
      const resAtt = await fetch(`${BACKEND_URL}/attendance_data?t=${Date.now()}`);
      setAttendance(await resAtt.json());
      
      const resSent = await fetch(`${BACKEND_URL}/class_sentiment?t=${Date.now()}`);
      const dataSent = await resSent.json();
      setSentiment(dataSent);
      
      setError(null);
    } catch (e) { 
      setError("Connecting to backend..."); 
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2500); // Fast sync for the bar
    return () => clearInterval(interval);
  }, []);

  const handleEndSession = async () => {
    if (!window.confirm("End session and email parents of absentees?")) return;
    try {
        const res = await fetch(`${BACKEND_URL}/end_session_notify`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) alert("✅ " + data.message);
        else alert("❌ Error: " + data.message);
    } catch (err) { 
        alert("❌ Error: Could not connect to backend at port 5050."); 
    }
  };

  const handleReset = async () => {
    if (!window.confirm("Clear list?")) return;
    try {
        await fetch(`${BACKEND_URL}/reset_attendance`, { method: 'POST' });
        setAttendance({});
    } catch (err) { alert("Reset failed."); }
  };

  // Dynamic Color Logic for the Bar and Text
  const getVibeColor = (s) => {
    if (s >= 80) return '#4CAF50'; // Green (Excellent)
    if (s >= 55) return '#FF9800'; // Orange (Focused/Good)
    return '#f44336'; // Red (Bored/Low)
  };

  return (
    <div className="live-attendance-container" style={{ backgroundColor: '#1a1a1a', color: 'white', minHeight: '100vh', padding: '20px' }}>
      
      <div style={{ display: 'flex', gap: '20px', marginBottom: '25px' }}>
        
        {/* CLASS VIBE CARD WITH LIVE BAR */}
        <div style={{ 
          flex: 1, 
          backgroundColor: '#2d2d2d', 
          padding: '20px', 
          borderRadius: '12px', 
          borderLeft: `6px solid ${getVibeColor(sentiment.score)}`,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
            <p style={{ margin: 0, color: '#aaa', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>Class Vibe</p>
            <h2 style={{ color: getVibeColor(sentiment.score), margin: '10px 0' }}>
                {sentiment.rating} ({sentiment.score}%)
            </h2>

            {/* THE LIVE PROGRESS BAR */}
            <div style={{ 
              width: '100%', 
              height: '12px', 
              backgroundColor: '#444', 
              borderRadius: '6px', 
              overflow: 'hidden',
              marginTop: '5px'
            }}>
                <div style={{ 
                    width: `${sentiment.score}%`, 
                    height: '100%', 
                    backgroundColor: getVibeColor(sentiment.score), 
                    transition: 'width 1s ease-in-out, background-color 0.5s linear' 
                }}></div>
            </div>
            <p style={{ fontSize: '11px', color: '#777', marginTop: '8px' }}>
                Based on {sentiment.count} detected faces
            </p>
        </div>

        {/* ATTENDANCE SUMMARY CARD */}
        <div style={{ flex: 1, backgroundColor: '#2d2d2d', padding: '20px', borderRadius: '12px', borderLeft: '6px solid #2196F3' }}>
            <p style={{ margin: 0, color: '#aaa', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase' }}>Attendance</p>
            <h2 style={{ color: '#2196F3', margin: '10px 0' }}>{Object.keys(attendance).length} Present</h2>
            <div style={{ marginTop: '10px' }}>
                <button onClick={handleEndSession} style={btnS('#FF9800')}>Notify Absentees</button>
                <button onClick={handleReset} style={{...btnS('#ff4444'), marginLeft: '10px'}}>Reset List</button>
            </div>
        </div>
      </div>

      {/* VIDEO FEED */}
      <div style={{ borderRadius: '15px', overflow: 'hidden', border: '3px solid #333' }}>
        <img src={`${BACKEND_URL}/video_feed`} alt="Feed" style={{ width: '100%', display: 'block' }} />
      </div>

      {/* LOG LIST */}
      <div style={{ marginTop: '25px', backgroundColor: '#2d2d2d', padding: '15px', borderRadius: '12px' }}>
        <h3 style={{ borderBottom: '1px solid #444', paddingBottom: '10px' }}>Live Attendance Log</h3>
        {Object.entries(attendance).map(([regNo, rec]) => (
          <div key={regNo} style={{ padding: '12px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: '16px' }}>{regNo}</strong> 
            <span style={{ color: '#aaa', fontSize: '13px' }}>Detected at {new Date(rec.timestamp).toLocaleTimeString()}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

const btnS = (c) => ({ 
    backgroundColor: c, 
    color: 'white', 
    border: 'none', 
    padding: '10px 18px', 
    borderRadius: '6px', 
    cursor: 'pointer', 
    fontWeight: 'bold',
    fontSize: '13px'
});

export default LiveAttendance;