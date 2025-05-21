import { useEffect, useState } from "react";
import { fetchDashboard, uploadDocument, fetchDocuments } from "../services/api";
import { useNavigate } from "react-router-dom";

export default function Dashboard() {
  const navigate = useNavigate();
  const token = localStorage.getItem("token") || "";

  const [message, setMessage] = useState("");
  const [role, setRole] = useState("");
  const [title, setTitle] = useState("");
  const [organization, setOrganization] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploadMessage, setUploadMessage] = useState("");
  const [documents, setDocuments] = useState<any[]>([]);

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    // 👇 Define and call async logic inside useEffect
    const loadDashboard = async () => {
      try {
        const res = await fetchDashboard(token);
        setMessage(res.message);
        setRole(res.role);

        if (res.role === "reviewer") {
          const docs = await fetchDocuments(token);
          setDocuments(docs);
        }
      } catch (err) {
        console.error("Dashboard load error", err);
        setMessage("Failed to load dashboard");
      }
    };

    loadDashboard();
  }, [token, navigate]);

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !title || !organization) return alert("All fields required");
    try {
      const res = await uploadDocument(title, organization, file, token);
      setUploadMessage(res.message);
    } catch (err) {
      console.error(err);
      setUploadMessage("❌ Upload failed");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Dashboard</h2>
      <p>{message}</p>
      {role && <p><strong>Role:</strong> {role}</p>}

      {role === "grantee" && (
        <form onSubmit={handleUpload}>
          <input
            type="text"
            placeholder="Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <input
            type="text"
            placeholder="Organization"
            value={organization}
            onChange={(e) => setOrganization(e.target.value)}
            required
          />
          <input
            type="file"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            required
          />
          <button type="submit">Upload</button>
          <p>{uploadMessage}</p>
        </form>
      )}

      {role === "reviewer" && (
        <div>
          <h3>📂 Submitted Documents</h3>
          {documents.length === 0 ? (
            <p>No documents found.</p>
          ) : (
            <ul>
              {documents.map((doc, index) => (
                <li key={index}>
                  <strong>{doc.title}</strong> from {doc.organization} by{" "}
                  {doc.submitted_by || doc.owner_email || "Unknown"}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
