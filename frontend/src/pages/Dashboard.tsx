import { useEffect, useState } from "react";
// Removed 'uploadDocument' as it's no longer used directly in this component
import { fetchDashboard, fetchDocuments } from "../services/api";
import { useNavigate } from "react-router-dom";
import GranteeDashboard from './GranteeDashboard';
import AdminDashboard from './AdminDashboard'; // Import the new AdminDashboard component

export default function Dashboard() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token") || "";

  const [message, setMessage] = useState("");
  const [role, setRole] = useState("");
  const [documents, setDocuments] = useState<any[]>([]); // For reviewer documents

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    const loadDashboard = async () => {
      try {
        const res = await fetchDashboard(token);
        setMessage(res.message);
        setRole(res.role);

        // If the user is a reviewer, fetch all documents for review
        // AdminDashboard will fetch its own documents
        if (res.role === "reviewer") {
          const docs = await fetchDocuments(token); // This should ideally be fetchReviewerDocuments from api.ts
          setDocuments(docs);
        }
      } catch (err) {
        console.error("Dashboard load error", err);
        setMessage("Failed to load dashboard");
      }
    };

    loadDashboard();
  }, [token, navigate]); // Added navigate to dependency array as per ESLint best practice

  return (
    <div style={{ padding: 20 }}>
      <h2>Dashboard</h2>
      <p>{message}</p>
      {role && <p><strong>Role:</strong> {role}</p>}

      {/* Conditionally render dashboards based on role */}
      {role === "grantee" && <GranteeDashboard />}
      {role === "reviewer" && (
        <div>
          <h3>📂 Submitted Documents (for Reviewer)</h3>
          {documents.length === 0 ? (
            <p>No documents found for review.</p>
          ) : (
            <ul>
              {documents.map((doc, index) => (
                <li key={index}>
                  <strong>{doc.title}</strong> from {doc.organization} by{" "}
                  {doc.submitted_by || doc.owner_email || "Unknown"}
                  {/* You might want to add a link to review the document here */}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {role === "admin" && <AdminDashboard />} {/* Render AdminDashboard for admin role */}
    </div>
  );
}
