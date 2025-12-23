import React, { useState, useEffect } from 'react';
import './LiveAttendance.css';
import * as XLSX from 'xlsx';

function LiveAttendance() {
  const [attendance, setAttendance] = useState({});
  const [sentiment, setSentiment] = useState({ rating: "...", score: 0 });
  const [isStarted, setIsStarted] = useState(false);
  const BACKEND_URL = 'http://127.0.0.1:5050';

  const fetchData = async () => {
    try {
      const resAtt = await fetch(`${BACKEND_URL}/attendance_data?t=${Date.now()}`);
      setAttendance(await resAtt.json());
      const resSent = await fetch(`${BACKEND_URL}/class_sentiment?t=${Date.now()}`);
      setSentiment(await resSent.json());
    } catch { console.error("Fetch error"); }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2500);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSession = async () => {
    if (!isStarted) {
      await fetch(`${BACKEND_URL}/start_session`, { method: 'POST' });
      setIsStarted(true);
      setAttendance({});
    } else {
      if (!window.confirm("End session and save report?")) return;
      const res = await fetch(`${BACKEND_URL}/end_session_notify`, { method: 'POST' });
      const data = await res.json();
      alert(data.message);
      setIsStarted(false);
      setAttendance({});
    }
  };

  const downloadExcel = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/students`);
      const allStudents = await res.json();
      const presentIds = Object.keys(attendance);
      const reportData = allStudents.map(student => {
        const isPresent = presentIds.includes(String(student.register_no));
        return {
          "Registration No": student.register_no,
          "Name": student.name,
          "Section": student.section,
          "Status": isPresent ? "PRESENT" : "ABSENT",
          "Time": isPresent ? new Date(attendance[student.register_no].timestamp).toLocaleTimeString() : "N/A"
        };
      });
      const ws = XLSX.utils.json_to_sheet(reportData);
      const wb = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(wb, ws, "Report");
      XLSX.writeFile(wb, `Attendance_${new Date().toLocaleDateString()}.xlsx`);
    } catch (err) { alert("Excel Error: " + err.message); }
  };

  const getVibeColor = (s) => (s >= 80 ? '#4CAF50' : s >= 55 ? '#FF9800' : '#f44336');

  return (
    <div className="live-attendance-container" style={{ backgroundColor: '#1a1a1a', minHeight: '100vh', padding: '20px', color: 'white' }}>
      <div style={{ display: 'flex', gap: '20px', marginBottom: '25px' }}>
        <div style={{ flex: 1, backgroundColor: '#2d2d2d', padding: '20px', borderRadius: '12px', borderLeft: `6px solid ${getVibeColor(sentiment.score)}` }}>
          <p style={{ fontSize: '12px', color: '#aaa', fontWeight: 'bold' }}>CLASS VIBE</p>
          <h2 style={{ color: getVibeColor(sentiment.score) }}>{sentiment.rating} ({sentiment.score}%)</h2>
          <div style={{ height: '10px', background: '#444', borderRadius: '5px' }}>
            <div style={{ width: `${sentiment.score}%`, height: '100%', background: getVibeColor(sentiment.score), transition: 'width 1s' }} />
          </div>
        </div>
        <div style={{ flex: 1, backgroundColor: '#2d2d2d', padding: '20px', borderRadius: '12px', borderLeft: '6px solid #2196F3' }}>
          <p style={{ fontSize: '12px', color: '#aaa', fontWeight: 'bold' }}>CONTROLS</p>
          <h2>{Object.keys(attendance).length} Present</h2>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={handleToggleSession} style={{ ...btn('#4CAF50'), flex: 2 }}>{isStarted ? "⏹ End Session" : "▶ Start"}</button>
            <button onClick={downloadExcel} style={{ ...btn('#2196F3'), flex: 1 }}>📊 Excel</button>
          </div>
        </div>
      </div>
      <img src={`${BACKEND_URL}/video_feed`} alt="Live Feed" style={{ width: '100%', borderRadius: '15px', border: '3px solid #333' }} />
      <div style={{ marginTop: '20px', backgroundColor: '#2d2d2d', padding: '20px', borderRadius: '12px' }}>
        <h3>{isStarted ? "🔴 Live Log" : "⚪ Paused"}</h3>
        <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
          {Object.entries(attendance).reverse().map(([reg, rec]) => (
            <div key={reg} style={{ background: '#333', padding: '15px', borderRadius: '10px', marginBottom: '10px', display: 'flex', justifyContent: 'space-between', borderLeft: '4px solid #4CAF50' }}>
              <strong>{reg}</strong>
              <span style={{ color: '#4CAF50', fontWeight: 'bold' }}>Present <span style={{ color: '#aaa', fontWeight: 'normal' }}>({new Date(rec.timestamp).toLocaleTimeString()})</span></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
const btn = (bg) => ({ background: bg, color: 'white', border: 'none', padding: '10px', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' });
export default LiveAttendance;