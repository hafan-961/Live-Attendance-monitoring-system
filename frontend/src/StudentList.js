

// import React, { useEffect, useState, useCallback } from "react";
// import axios from "axios";

// const StudentList = () => {
//   const [students, setStudents] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [sortOrder, setSortOrder] = useState("asc");
//   const BACKEND_URL = "http://127.0.0.1:5050";

//   const fetchStudents = async () => {
//     try {
//       const response = await axios.get(`${BACKEND_URL}/students?t=${Date.now()}`);
//       const sorted = [...response.data].sort((a, b) => {
//         return sortOrder === "asc" ? a.roll_no - b.roll_no : b.roll_no - a.roll_no;
//       });
//       setStudents(sorted);
//       setLoading(false);
//     } catch (err) { console.error(err); }
//   };

//   useEffect(() => {
//     fetchStudents();
//     const interval = setInterval(fetchStudents, 5000);
//     return () => clearInterval(interval);
//   }, [sortOrder]);

//   // --- NEW DELETE FUNCTION ---
//   const handleDelete = async (regNo) => {
//     if (window.confirm(`Are you sure you want to delete Registration No: ${regNo}?`)) {
//       try {
//         await axios.delete(`${BACKEND_URL}/delete_student/${regNo}`);
//         alert("Student deleted successfully");
//         fetchStudents(); // Refresh the list
//       } catch (err) {
//         alert("Failed to delete student");
//       }
//     }
//   };

//   if (loading) return <div style={{color:'white', padding:'50px'}}>Loading...</div>;

//   return (
//     <div style={{ padding: '40px', backgroundColor: '#1a1a1a', minHeight: '100vh', color: 'white' }}>
//       <h1 style={{ textAlign: 'center', color: '#ff8c00' }}>Registered Students</h1>
      
//       <table style={{ width: '100%', marginTop: '30px', borderCollapse: 'collapse', backgroundColor: '#262626' }}>
//         <thead>
//           <tr style={{ backgroundColor: '#333', color: '#ff8c00', textAlign: 'left' }}>
//             <th style={tS}>Registration No</th>
//             <th style={tS}>Name</th>
//             <th style={tS}>Roll No</th>
//             <th style={tS}>Section</th>
//             <th style={tS}>Parent's Email</th>
//             <th style={tS}>Action</th> {/* New Column */}
//           </tr>
//         </thead>
//         <tbody>
//           {students.map((student) => (
//             <tr key={student.register_no} style={{ borderBottom: '1px solid #444' }}>
//               <td style={tS}>{student.register_no}</td>
//               <td style={tS}>{student.name}</td>
//               <td style={tS}>{student.roll_no}</td>
//               <td style={tS}>{student.section}</td>
//               <td style={tS}>{student.email}</td>
//               <td style={tS}>
//                 <button 
//                   onClick={() => handleDelete(student.register_no)}
//                   style={{ backgroundColor: '#ff4444', color: 'white', border: 'none', padding: '5px 10px', borderRadius: '4px', cursor: 'pointer' }}
//                 >
//                   Delete
//                 </button>
//               </td>
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   );
// };

// const tS = { padding: '15px', border: '1px solid #333' };

// export default StudentList;





import React, { useEffect, useState } from "react";
import axios from "axios";

const StudentList = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sortOrder, setSortOrder] = useState("asc");
  const BACKEND_URL = "http://127.0.0.1:5050";

  const fetchStudents = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/students?t=${Date.now()}`);
      const sorted = [...response.data].sort((a, b) => {
        const rollA = parseInt(a.roll_no) || 0;
        const rollB = parseInt(b.roll_no) || 0;
        return sortOrder === "asc" ? rollA - rollB : rollB - rollA;
      });
      setStudents(sorted);
      setLoading(false);
    } catch (err) { 
      console.error("Fetch error:", err); 
    }
  };

  useEffect(() => {
    fetchStudents();
    const interval = setInterval(fetchStudents, 5000);
    return () => clearInterval(interval);
  }, [sortOrder]);

  const handleDelete = async (regNo) => {
    if (window.confirm(`Are you sure you want to delete Registration No: ${regNo}?`)) {
      try {
        const response = await axios.delete(`${BACKEND_URL}/delete_student/${regNo}`);
        if (response.data.status === "success") {
          alert("✅ Student deleted successfully");
          fetchStudents(); 
        }
      } catch (err) {
        console.error("Delete error:", err);
        alert("❌ Failed to delete student from Backend.");
      }
    }
  };

  if (loading) return <div style={{color:'white', padding:'50px', textAlign:'center'}}>Loading Database...</div>;

  return (
    <div style={{ padding: '40px', backgroundColor: '#1a1a1a', minHeight: '100vh', color: 'white', fontFamily: 'sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flexDirection: 'column' }}>
        <h2 style={{ color: '#ff8c00', marginBottom: '5px' }}>Students List</h2>
        <h1 style={{ marginTop: '0', marginBottom: '20px' }}>Registered Students</h1>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <span style={{ color: '#aaa', fontSize: '14px' }}>Live Syncing: {students.length} Total</span>
        <button 
          onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")} 
          style={{ backgroundColor: "#ff8c00", color: 'white', border: 'none', padding: '10px 15px', borderRadius: '5px', fontWeight: 'bold', cursor: 'pointer' }}
        >
          Sort by Roll No {sortOrder === "asc" ? "↑" : "↓"}
        </button>
      </div>
      
      <div style={{ borderRadius: '10px', overflow: 'hidden', border: '1px solid #333' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', backgroundColor: '#262626' }}>
          <thead>
            <tr style={{ backgroundColor: '#333', color: '#ff8c00', textAlign: 'left' }}>
              <th style={tS}>Registration No</th>
              <th style={tS}>Name</th>
              <th style={tS}>Roll No</th>
              <th style={tS}>Section</th>
              <th style={tS}>Parent's Email</th>
              <th style={{...tS, textAlign: 'center'}}>Action</th>
            </tr>
          </thead>
          <tbody>
            {students.map((student) => (
              <tr key={student.register_no} style={{ borderBottom: '1px solid #444' }}>
                <td style={tS}>{student.register_no}</td>
                <td style={tS}>{student.name}</td>
                <td style={tS}>{student.roll_no}</td>
                <td style={tS}>{student.section}</td>
                <td style={tS}>{student.email}</td>
                <td style={{...tS, textAlign: 'center'}}>
                  <button 
                    onClick={() => handleDelete(student.register_no)}
                    style={{ backgroundColor: '#dc2626', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold', fontSize: '12px' }}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const tS = { padding: '15px', fontSize: '14px' };

export default StudentList;

