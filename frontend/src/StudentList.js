import React, { useEffect, useState } from "react";
import axios from "axios";

function StudentList() {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        axios
            .get("http://127.0.0.1:8000/students")
            .then((res) => {
                setStudents(res.data);
                setLoading(false);
            })
            .catch((err) => {
                console.error("Error fetching students:", err);
                setError("Failed to load students.");
                setLoading(false);
            });
    }, []);

    if (loading) return <p>Loading students...</p>;
    if (error) return <p className="text-red-500">{error}</p>;

    return (
        <div className="bg-white shadow rounded-lg overflow-hidden">
            <table className="w-full">
                <thead className="bg-gray-200">
                    <tr>
                        <th className="p-3 text-left">Name</th>
                        <th className="p-3 text-left">Register No</th>
                        <th className="p-3 text-left">Roll No</th>
                        <th className="p-3 text-left">Section</th>
                    </tr>
                </thead>
                <tbody>
                    {students.length === 0 ? (
                        <tr>
                            <td colSpan="4" className="p-4 text-center text-gray-500">
                                No students registered yet.
                            </td>
                        </tr>
                    ) : (
                        students.map((student, index) => (
                            <tr key={index} className="border-t hover:bg-gray-50">
                                <td className="p-3 font-medium">{student.name}</td>
                                <td className="p-3">{student.register_no}</td>
                                <td className="p-3">{student.roll_no}</td>
                                <td className="p-3">{student.section}</td>
                            </tr>
                        ))
                    )}
                </tbody>
            </table>
        </div>
    );
}

export default StudentList;
