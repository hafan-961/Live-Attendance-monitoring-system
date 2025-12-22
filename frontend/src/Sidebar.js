// import React from "react";

// function Sidebar({ setPage }) {
//   return (
//     <div className="w-64 h-screen bg-white shadow-lg p-6">
//       <h2 className="text-2xl font-bold text-blue-600 mb-8">AI Attendance</h2>

//       <ul className="space-y-4 text-gray-700 font-medium">
//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("dashboard")}
//         >
//           Dashboard
//         </li>

//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("attendance")}
//         >
//           Attendance Records
//         </li>

//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("register")}
//         >
//           Register Student
//         </li>

//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("live")}
//         >
//           Live Attendance
//         </li>



//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("students")}
//         >
//           Students List
//         </li>

//         <li 
//           className="cursor-pointer hover:text-blue-600"
//           onClick={() => setPage("settings")}
//         >
//           Settings
//         </li>
//       </ul>
//     </div>
//   );
// }

// export default Sidebar;



import React from "react";
// Import icons from react-icons. We'll pick some suitable ones from Material Design (Md)
import { 
  MdDashboard, 
  MdBarChart, // For Attendance Records
  MdPersonAdd, 
  MdVideocam, // For Live Attendance
  MdPeople, 
  MdSettings,
  MdHelpOutline, // Example for bottom icons
  MdNotifications, // Example for bottom icons
  MdBrightness4 // Example for bottom icons (Dark/Light mode toggle)
} from 'react-icons/md';

// Assuming your LPU logo is in 'public' folder:
const lpuLogoPath = '/lpu_logo.png'; // Adjust if your logo is named differently or in a subfolder of public/

function Sidebar({ setPage }) {
  // Define your navigation items with icons
  const navItems = [
    { name: 'dashboard', label: 'Dashboard', icon: <MdDashboard /> },
    { name: 'attendance', label: 'Attendance Records', icon: <MdBarChart /> },
    { name: 'register', label: 'Register Student', icon: <MdPersonAdd /> },
    { name: 'live', label: 'Live Attendance', icon: <MdVideocam /> },
    { name: 'students', label: 'Students List', icon: <MdPeople /> },
  ];

  return (
    <div className="sidebar-container">
      <div className="sidebar-header">
        <img src={lpuLogoPath} alt="LPU Logo" className="sidebar-logo" />
      </div>

      <nav className="sidebar-nav">
        <ul>
          {navItems.map((item) => (
            <li key={item.name}>
              <button
                className="sidebar-nav-item"
                onClick={() => setPage(item.name)}
              >
                <span className="sidebar-icon">{item.icon}</span>
                <span className="sidebar-label">{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>

      {/* This area for icons at the bottom of your example (e.g., settings, moon, bell) */}
      
    </div>
    
  );
}

export default Sidebar;