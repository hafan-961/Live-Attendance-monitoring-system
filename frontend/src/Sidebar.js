
import React from "react";

import { 
  MdDashboard, 
  MdBarChart, // For Attendance Records
  MdPersonAdd, 
  MdVideocam, // For Live Attendance
  MdPeople, 
  MdSettings,
  MdHelpOutline, 
  MdNotifications, 
  MdBrightness4 
} from 'react-icons/md';


const lpuLogoPath = '/lpu_logo.png'; 

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