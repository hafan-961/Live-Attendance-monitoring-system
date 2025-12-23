import React, { useState, useEffect } from "react";

function AttendanceRecords() {
  const [history, setHistory] = useState([]);
  const [selectedSession, setSelectedSession] = useState(null);
  const BACKEND_URL = "http://127.0.0.1:5050";

  useEffect(() => {
    fetch(`${BACKEND_URL}/get_history?t=${Date.now()}`).then((res) => res.json()).then((data) => setHistory(data));
  }, []);

  return (
    <div style={{ padding: "30px", backgroundColor: "#121212", minHeight: "100vh", color: "white" }}>
      <h1 style={{ color: "#ff8c00" }}>Attendance History</h1>
      <div style={{ display: "flex", gap: "20px", marginTop: "30px" }}>
        <div style={{ flex: "1", display: "flex", flexDirection: "column", gap: "10px" }}>
          {history.map((session) => (
            <div key={session.session_id} onClick={() => setSelectedSession(session)} style={{ padding: "15px", backgroundColor: selectedSession?.session_id === session.session_id ? "#333" : "#1e1e1e", borderRadius: "10px", cursor: "pointer", borderLeft: `5px solid ${session.absent_count > 0 ? "#f44336" : "#4CAF50"}` }}>
              <strong>{session.date} | {session.time}</strong>
              <div style={{ fontSize: "12px", color: "#aaa" }}>P: {session.present_count} | A: {session.absent_count}</div>
            </div>
          ))}
        </div>
        <div style={{ flex: "2", backgroundColor: "#1e1e1e", borderRadius: "15px", padding: "20px" }}>
          {selectedSession ? (
            <div>
              <h3>Report: {selectedSession.date}</h3>
              <table style={{ width: "100%", textAlign: "left" }}>
                <thead><tr style={{ borderBottom: "1px solid #444" }}><th>Reg No</th><th>Name</th><th>Status</th></tr></thead>
                <tbody>
                  {selectedSession.present_list.map(s => <tr key={s.reg_no}><td style={{padding:'8px'}}>{s.reg_no}</td><td>{s.name}</td><td style={{color:"#4CAF50"}}>PRESENT</td></tr>)}
                  {selectedSession.absent_list.map(s => <tr key={s.reg_no}><td style={{padding:'8px'}}>{s.reg_no}</td><td>{s.name}</td><td style={{color:"#f44336"}}>ABSENT</td></tr>)}
                </tbody>
              </table>
            </div>
          ) : <p style={{ color: "#555" }}>Select a session from the left</p>}
        </div>
      </div>
    </div>
  );
}
export default AttendanceRecords;