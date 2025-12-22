
// import React, { useEffect, useState } from "react";
// import axios from "axios";
// import Sidebar from "./Sidebar";
// import AttendanceChart from "./AttendanceChart";
// import RegisterStudent from "./RegisterStudent";
// import LiveAttendance from "./LiveAttendance";
// import StudentList from "./StudentList";

// function App() {
//   const [page, setPage] = useState("dashboard");
//   const [attendance, setAttendance] = useState([]);

//   // Auto-refresh attendance data every 3 seconds
//   useEffect(() => {
//     const fetchData = () => {
//       axios
//         .get("http://127.0.0.1:5000/attendance_data")
//         .then((res) => {
//           // Handle both array and object responses
//           const data = Array.isArray(res.data) ? res.data : [];
//           setAttendance(data);
//         })
//         .catch((err) => console.error("API Error:", err));
//     };

//     fetchData(); // fetch immediately
//     const interval = setInterval(fetchData, 3000); // every 3 seconds

//     return () => clearInterval(interval);
//   }, []);

//   return (
//     <div className="app-layout">
//       {/* Sidebar */}
//       <Sidebar setPage={setPage} />

//       {/* Main Content */}
//       <div className="flex-1 p-10 min-h-screen main-content-area">
//         {/* -------------------- Dashboard Page -------------------- */}
//         {page === "dashboard" && (
//           <div>
//             <h1 className="text-3xl font-bold text-blue-600 mb-6">Dashboard</h1>
//             <div className="text-lg mb-4">
//               Total Attendance Records: <strong>{attendance.length}</strong>
//             </div>
//             {/* Attendance Chart */}
//             <AttendanceChart attendance={attendance} />
//           </div>
//         )}

//         {page === "register" && <RegisterStudent />}
//         {page === "live" && <LiveAttendance />}

//         {/* -------------------- Attendance Records Page -------------------- */}
//         {page === "attendance" && (
//           <div>
//             <h1 className="text-3xl font-bold text-blue-600 mb-6">
//               Attendance Records
//             </h1>
//             <table className="w-full bg-white shadow rounded-lg">
//               <thead>
//                 <tr className="bg-gray-200">
//                   <th className="p-3 text-left">Register No</th>
//                   <th className="p-3 text-left">Time</th>
//                   <th className="p-3 text-left">Status</th>
//                 </tr>
//               </thead>
//               <tbody>
//                 {attendance.map((item, index) => (
//                   <tr key={index} className="border-t">
//                     <td className="p-3">{item.Register_No}</td>
//                     <td className="p-3">{item.Time}</td>
//                     <td className="p-3">
//                       <span
//                         className={`px-2 py-1 text-sm rounded ${item.Status === "Present"
//                           ? "bg-green-200 text-green-800"
//                           : "bg-red-200 text-red-800"
//                           }`}
//                       >
//                         {item.Status}
//                       </span>
//                     </td>
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>
//         )}

//         {/* -------------------- Students List Page -------------------- */}
//         {page === "students" && (
//           <div>
//             <h1 className="text-3xl font-bold text-blue-600 mb-6">Students List</h1>
//             <StudentList />
//           </div>
//         )}

//         {/* -------------------- Settings Page -------------------- */}
//         {page === "settings" && (
//           <h1 className="text-3xl font-bold text-blue-600">Settings</h1>
//         )}
//       </div>
//     </div>
//   );
// }

// export default App;


import React, { useEffect, useState } from "react";
import axios from "axios";
import Sidebar from "./Sidebar";
import AttendanceChart from "./AttendanceChart";
import RegisterStudent from "./RegisterStudent";
import LiveAttendance from "./LiveAttendance";
import StudentList from "./StudentList";

function App() {
  const [page, setPage] = useState("dashboard");
  const [attendance, setAttendance] = useState([]);

  // Flask Backend URL (Changed from FastAPI's 8000 to Flask's 5000)
  const FLASK_BACKEND_URL = "http://127.0.0.1:5000"; 

  // Auto-refresh attendance data every 3 seconds
  useEffect(() => {
    const fetchData = () => {
      axios
        .get(`${FLASK_BACKEND_URL}/attendance_data`) // Corrected endpoint for Flask
        .then((res) => {
          // Handle both array and object responses for robustness
          const data = Array.isArray(res.data) ? res.data : [];
          setAttendance(data);
        })
        .catch((err) => console.error("API Error fetching attendance:", err));
    };

    fetchData(); // fetch immediately
    const interval = setInterval(fetchData, 3000); // every 3 seconds

    return () => clearInterval(interval);
  }, []); // Empty dependency array means this runs once on mount

  return (
    <div className="app-layout"> {/* Custom class for overall layout */}
      {/* Sidebar */}
      <Sidebar setPage={setPage} />

      {/* Main Content Area */}
      <div className="main-content-area"> {/* Custom class for main content */}
        {/* -------------------- Dashboard Page -------------------- */}
        {page === "dashboard" && (
          <div>
            <h1 className="text-3xl font-bold text-blue-600 mb-6">Dashboard</h1>
            <div className="text-lg mb-4">
              Total Attendance Records: <strong>{attendance.length}</strong>
            </div>
            {/* Attendance Chart */}
            <AttendanceChart attendance={attendance} />
          </div>
        )}

        {page === "register" && <RegisterStudent />}
        {page === "live" && <LiveAttendance />}

        {/* -------------------- Attendance Records Page -------------------- */}
        {page === "attendance" && (
          <div>
            <h1 className="text-3xl font-bold text-blue-600 mb-6">
              Attendance Records
            </h1>
            <table className="w-full bg-white shadow rounded-lg">
              <thead>
                <tr className="bg-gray-200">
                  <th className="p-3 text-left">Register No</th>
                  <th className="p-3 text-left">Time</th>
                  <th className="p-3 text-left">Status</th>
                </tr>
              </thead>
              <tbody>
                {attendance.map((item, index) => (
                  <tr key={index} className="border-t">
                    <td className="p-3">{item.Register_No}</td>
                    <td className="p-3">{item.Time}</td>
                    <td className="p-3">
                      <span
                        className={`px-2 py-1 text-sm rounded ${item.Status === "Present"
                          ? "bg-green-200 text-green-800"
                          : "bg-red-200 text-red-800"
                          }`}
                      >
                        {item.Status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* -------------------- Students List Page -------------------- */}
        {page === "students" && (
          <div>
            <h1 className="text-3xl font-bold text-blue-600 mb-6">Students List</h1>
            <StudentList />
          </div>
        )}

        {/* -------------------- Settings Page -------------------- */}
        {page === "settings" && (
          <h1 className="text-3xl font-bold text-blue-600">Settings</h1>
        )}
      </div>
    </div>
  );
}

export default App;