// import React, { useEffect, useState } from "react";
// import axios from "axios";

// const StudentList = () => {
//   const [students, setStudents] = useState([]);
//   const [loading, setLoading] = useState(true);
//   const [error, setError] = useState(null);
//   const [sortOrder, setSortOrder] = useState("asc");

//   const fetchStudents = async () => {
//     try {
//       const response = await axios.get("http://127.0.0.1:5000/students");
//       setStudents(response.data);
//       setError(null);
//     } catch (err) {
//       console.error("Fetch error:", err);
//       setError("Failed to connect to backend server.");
//     } finally {
//       setLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchStudents();
//   }, []);

//   const handleSort = () => {
//     const nextOrder = sortOrder === "asc" ? "desc" : "asc";
//     setSortOrder(nextOrder);

//     const sortedData = [...students].sort((a, b) => {
//       const rollA = parseInt(a.roll_no) || 0;
//       const rollB = parseInt(b.roll_no) || 0;
//       return nextOrder === "asc" ? rollA - rollB : rollB - rollA;
//     });

//     setStudents(sortedData);
//   };

//   if (loading)
//     return (
//       <div className="p-10 text-center text-gray-500">
//         Loading Database...
//       </div>
//     );

//   return (
//     <div className="p-8 bg-gray-50 min-h-screen font-sans">
//       <div className="max-w-6xl mx-auto">

//         {/* Header Section */}
//         <div className="flex justify-between items-center mb-8">
//           <div>
//             <h1 className="text-3xl font-extrabold text-gray-900">
//               Registered Students
//             </h1>
//             <p className="text-gray-500 mt-1">
//               Total Enrollment: {students.length}
//             </p>
//           </div>

//           {/* Sort Button - Dark Orange */}
//           <button
//             onClick={handleSort}
//             style={{ backgroundColor: "#ff8c00" }}
//             className="flex items-center text-white px-6 py-2.5 rounded-lg transition-all font-bold shadow-lg active:scale-95 hover:brightness-90"
//           >
//             Sort by Roll No {sortOrder === "asc" ? "↑" : "↓"}
//           </button>
//         </div>

//         {error && (
//           <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 text-red-700 rounded shadow-sm">
//             {error}
//           </div>
//         )}

//         {/* Table */}
//         <div className="bg-white shadow-2xl rounded-2xl overflow-hidden border border-gray-200">
//           <table className="w-full text-left border-collapse">
//             <thead>
//               <tr className="bg-gray-900 text-white text-sm uppercase tracking-wider">
//                 <th className="p-5 font-bold">Registration No</th>
//                 <th className="p-5 font-bold">Name</th>
//                 <th className="p-5 font-bold">Roll No</th>
//                 <th className="p-5 font-bold">Section</th>
//                 <th className="p-5 font-bold">Parent's Email</th>
//               </tr>
//             </thead>
//             <tbody className="divide-y divide-gray-100">
//               {students.length === 0 ? (
//                 <tr>
//                   <td colSpan="5" className="p-20 text-center text-gray-400 italic text-lg">
//                     No students registered in the database yet.
//                   </td>
//                 </tr>
//               ) : (
//                 students.map((student, index) => (
//                   <tr key={index} className="hover:bg-violet-50/50 transition-colors">
//                     <td className="p-5 font-mono text-violet-700 font-bold">
//                       {student.register_no}
//                     </td>
//                     <td className="p-5 text-gray-900 font-semibold italic">
//                       {student.name}
//                     </td>
//                     <td className="p-5 text-gray-900 font-bold text-lg">
//                       {student.roll_no}
//                     </td>
//                     <td className="p-5">
//                       <span className="bg-gray-800 text-gray-100 px-3 py-1 rounded text-xs font-black uppercase tracking-widest">
//                         {student.section}
//                       </span>
//                     </td>
//                     <td className="p-5 text-gray-600 font-medium">
//                       {student.email}
//                     </td>
//                   </tr>
//                 ))
//               )}
//             </tbody>
//           </table>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default StudentList;



import React, { useEffect, useState, useCallback } from "react";
import axios from "axios";

const StudentList = () => {
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortOrder, setSortOrder] = useState("asc");

  // Logic to sort data (defined outside to be reusable)
  const getSortedData = useCallback((data, order) => {
    return [...data].sort((a, b) => {
      const rollA = parseInt(a.roll_no) || 0;
      const rollB = parseInt(b.roll_no) || 0;
      return order === "asc" ? rollA - rollB : rollB - rollA;
    });
  }, []);

  const fetchStudents = async (isInitial = false) => {
    try {
      // Added ?t= timestamp to prevent the browser from caching old data
      const response = await axios.get(`http://127.0.0.1:5000/students?t=${new Date().getTime()}`);
      
      // Keep the current sort order even after refreshing
      const sortedResult = getSortedData(response.data, sortOrder);
      
      setStudents(sortedResult);
      setError(null);
    } catch (err) {
      console.error("Fetch error:", err);
      setError("Failed to connect to backend server.");
    } finally {
      if (isInitial) setLoading(false);
    }
  };

  useEffect(() => {
    // 1. Fetch immediately when page opens
    fetchStudents(true);

    // 2. Setup "Live Connection": Refresh list every 3 seconds
    const interval = setInterval(() => {
      fetchStudents(false);
    }, 3000);

    // 3. Cleanup: Stop refreshing when you leave the page
    return () => clearInterval(interval);
  }, [sortOrder, getSortedData]);

  const handleSort = () => {
    const nextOrder = sortOrder === "asc" ? "desc" : "asc";
    setSortOrder(nextOrder);
    // Sort existing data immediately for better UI feel
    setStudents(getSortedData(students, nextOrder));
  };

  if (loading) return <div className="p-10 text-center text-gray-500">Loading Database...</div>;

  return (
    <div className="p-8 bg-gray-50 min-h-screen font-sans">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-extrabold text-gray-900">Registered Students</h1>
            <div className="flex items-center mt-1">
              <span className="h-2 w-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
              <p className="text-gray-500 text-sm italic">Live Syncing: {students.length} Total</p>
            </div>
          </div>

          <button
            onClick={handleSort}
            style={{ backgroundColor: "#ff8c00" }}
            className="text-white px-6 py-2.5 rounded-lg font-bold shadow-lg active:scale-95 hover:brightness-90"
          >
            Sort by Roll No {sortOrder === "asc" ? "↑" : "↓"}
          </button>
        </div>

        <div className="bg-white shadow-2xl rounded-2xl overflow-hidden border border-gray-200">
          <table className="w-full text-left">
            <thead className="bg-gray-900 text-white text-sm uppercase">
              <tr>
                <th className="p-5 font-bold">Registration No</th>
                <th className="p-5 font-bold">Name</th>
                <th className="p-5 font-bold">Roll No</th>
                <th className="p-5 font-bold">Section</th>
                <th className="p-5 font-bold">Parent's Email</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {students.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-20 text-center text-gray-400 italic">No students registered yet.</td>
                </tr>
              ) : (
                students.map((student, index) => (
                  <tr key={index} className="hover:bg-violet-50/50 transition-colors">
                    <td className="p-5 font-mono text-violet-700 font-bold">{student.register_no}</td>
                    <td className="p-5 text-gray-900 font-semibold italic">{student.name}</td>
                    <td className="p-5 text-gray-900 font-bold text-lg">{student.roll_no}</td>
                    <td className="p-5">
                      <span className="bg-gray-800 text-gray-100 px-3 py-1 rounded text-xs font-black uppercase">{student.section}</span>
                    </td>
                    <td className="p-5 text-gray-600 font-medium">{student.email}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default StudentList;
