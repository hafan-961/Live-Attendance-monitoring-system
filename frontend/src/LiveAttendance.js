// import React, { useState, useEffect } from 'react';
// import './LiveAttendance.css'; // You might want to create a CSS file for styling

// function LiveAttendance() {
//   const [attendance, setAttendance] = useState({});
//   const [error, setError] = useState(null);
//   const [loading, setLoading] = useState(true);

//   // Configuration for your backend
//   const BACKEND_URL = 'http://localhost:5000'; // Make sure this matches your main.py Flask host and port

//   useEffect(() => {
//     const fetchAttendance = async () => {
//       try {
//         const response = await fetch(`${BACKEND_URL}/attendance_data`);
//         if (!response.ok) {
//           throw new Error(`HTTP error! status: ${response.status}`);
//         }
//         const data = await response.json();
//         setAttendance(data);
//         setError(null); // Clear any previous errors
//       } catch (e) {
//         console.error("Failed to fetch attendance data:", e);
//         setError("Failed to load attendance data. Is the backend running?");
//       } finally {
//         setLoading(false);
//       }
//     };

//     // Fetch initially
//     fetchAttendance();

//     // Set up polling for attendance data
//     const intervalId = setInterval(fetchAttendance, 3000); // Poll every 3 seconds

//     // Cleanup function
//     return () => clearInterval(intervalId);
//   }, []); // Empty dependency array means this runs once on mount and cleans up on unmount

//   return (
//     <div className="live-attendance-container">
//       <h1>Live Class Attendance Monitoring</h1>

//       <div className="video-section">
//         <h2>Live Camera Feed</h2>
//         {error && <p className="error-message">{error}</p>}
//         {/* The src attribute points directly to the MJPEG stream from your Flask backend */}
//         <img
//           src={`${BACKEND_URL}/video_feed`}
//           alt="Live Camera Feed"
//           className="live-video-feed"
//           onError={(e) => {
//             e.target.onerror = null; // Prevent infinite loop
//             setError("Failed to load video feed. Is the backend running and camera active?");
//           }}
//         />
//       </div>

//       <div className="attendance-section">
//         <h2>Attendance Status</h2>
//         {loading ? (
//           <p>Loading attendance data...</p>
//         ) : Object.keys(attendance).length === 0 ? (
//           <p>No attendance recorded yet for this session.</p>
//         ) : (
//           <ul className="attendance-list">
//             {Object.entries(attendance).map(([regNo, record]) => (
//               <li key={regNo} className="attendance-item">
//                 <strong>{regNo}:</strong> <span className="status-present">{record.status}</span> at {new Date(record.timestamp).toLocaleTimeString()}
//               </li>
//             ))}
//           </ul>
//         )}
//       </div>
//     </div>
//   );
// }

// export default LiveAttendance;



// import React, { useState, useEffect } from 'react';
// import './LiveAttendance.css'; 

// function LiveAttendance() {
//   const [attendance, setAttendance] = useState({});
//   const [error, setError] = useState(null);
//   const [loading, setLoading] = useState(true);

//   const BACKEND_URL = 'http://localhost:5000'; 

//   const fetchAttendance = async () => {
//     try {
//       const response = await fetch(`${BACKEND_URL}/attendance_data`);
//       if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
//       const data = await response.json();
//       setAttendance(data);
//       setError(null);
//     } catch (e) {
//       console.error("Failed to fetch attendance data:", e);
//       // Don't show error on screen constantly if just polling fails once
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchAttendance();
//     const intervalId = setInterval(fetchAttendance, 3000); 
//     return () => clearInterval(intervalId);
//   }, []);

//   // --- NEW: Function to handle Reset ---
//   const handleReset = async () => {
//     if (!window.confirm("Are you sure you want to clear the attendance list? This cannot be undone.")) {
//       return;
//     }

//     try {
//       const response = await fetch(`${BACKEND_URL}/reset_attendance`, {
//         method: 'POST',
//       });
//       const data = await response.json();
      
//       if (data.status === 'success') {
//         setAttendance({}); // Clear local state immediately
//         alert("Attendance list cleared successfully!");
//       } else {
//         alert("Failed to reset attendance.");
//       }
//     } catch (e) {
//       alert("Error connecting to server.");
//     }
//   };

//   return (
//     <div className="live-attendance-container">
//       <div className="header-container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
//           <h1>Live Class Attendance</h1>
//           {/* --- NEW: Reset Button --- */}
//           <button 
//             onClick={handleReset}
//             style={{
//               backgroundColor: '#ff4444', 
//               color: 'white', 
//               padding: '10px 20px', 
//               border: 'none', 
//               borderRadius: '5px',
//               cursor: 'pointer',
//               fontWeight: 'bold'
//             }}
//           >
//             Reset Attendance
//           </button>
//       </div>

//       <div className="video-section">
//         <img 
//           src={`${BACKEND_URL}/video_feed`} 
//           alt="Live Camera Feed" 
//           className="live-video-feed" 
//           onError={(e) => { e.target.onerror = null; setError("Video stream disconnected"); }} 
//         />
//       </div>

//       <div className="attendance-section">
//         <h2>Attendance Status</h2>
//         {loading ? (
//           <p>Loading data...</p>
//         ) : Object.keys(attendance).length === 0 ? (
//           <p>No attendance recorded for this session.</p>
//         ) : (
//           <ul className="attendance-list">
//             {Object.entries(attendance).map(([regNo, record]) => (
//               <li key={regNo} className="attendance-item">
//                 <strong>{regNo}:</strong> 
//                 <span className="status-present" style={{color: 'green', marginLeft: '10px'}}>
//                   {record.status}
//                 </span> 
//                 <span style={{marginLeft: 'auto'}}>
//                     at {new Date(record.timestamp).toLocaleTimeString()}
//                 </span>
//               </li>
//             ))}
//           </ul>
//         )}
//       </div>
//     </div>
//   );
// }

// export default LiveAttendance;


import React, { useState, useEffect } from 'react';
import './LiveAttendance.css'; 

function LiveAttendance() {
  const [attendance, setAttendance] = useState({});
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const BACKEND_URL = 'http://localhost:5000'; 

  const fetchAttendance = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/attendance_data`);
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data = await response.json();
      setAttendance(data);
      setError(null);
    } catch (e) {
      console.error("Failed to fetch attendance data:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
    const intervalId = setInterval(fetchAttendance, 3000); 
    return () => clearInterval(intervalId);
  }, []);

  // --- Reset Function ---
  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to clear the attendance list? This cannot be undone.")) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/reset_attendance`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === 'success') {
        setAttendance({}); // Clear local state immediately
        alert("Attendance list cleared successfully!");
      } else {
        alert("Failed to reset attendance: " + data.message);
      }
    } catch (e) {
      alert("Error: " + e.message + "\nPlease check if backend is running.");
    }
  };

  return (
    <div className="live-attendance-container">
      <div className="header-container" style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
          <h1>Live Class Attendance</h1>
          <button 
            onClick={handleReset}
            style={{
              backgroundColor: '#ff4444', 
              color: 'white', 
              padding: '10px 20px', 
              border: 'none', 
              borderRadius: '5px',
              cursor: 'pointer',
              fontWeight: 'bold'
            }}
          >
            Reset Attendance
          </button>
      </div>

      <div className="video-section">
        <img 
          src={`${BACKEND_URL}/video_feed`} 
          alt="Live Camera Feed" 
          className="live-video-feed" 
          onError={(e) => { e.target.onerror = null; setError("Video stream disconnected"); }} 
        />
      </div>

      <div className="attendance-section">
        <h2>Attendance Status</h2>
        {loading ? (
          <p>Loading data...</p>
        ) : Object.keys(attendance).length === 0 ? (
          <p>No attendance recorded for this session.</p>
        ) : (
          <ul className="attendance-list">
            {Object.entries(attendance).map(([regNo, record]) => (
              <li key={regNo} className="attendance-item">
                <strong>{regNo}:</strong> 
                <span className="status-present" style={{color: 'green', marginLeft: '10px'}}>
                  {record.status}
                </span> 
                <span style={{marginLeft: 'auto'}}>
                    at {new Date(record.timestamp).toLocaleTimeString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default LiveAttendance;