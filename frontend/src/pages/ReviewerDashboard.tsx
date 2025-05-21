import { useEffect, useState } from "react";
import { fetchDocuments, submitEvaluation } from "../services/api";

interface Evaluation {
  reviewer: string;
  comment: string;
  status: string;
}

interface Document {
  id: number;
  title: string;
  organization: string;
  filename: string;
  uploaded_by: string;
  url: string;
  evaluations: Evaluation[]; // Added evaluations here
}

export default function ReviewerDashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [comments, setComments] = useState<{ [key: number]: string }>({});
  const [statuses, setStatuses] = useState<{ [key: number]: string }>({});
  const token = localStorage.getItem("token");

  useEffect(() => {
    const loadDocuments = async () => {
      if (!token) return;
      try {
        const res = await fetchDocuments(token);
        setDocuments(res);

        // Prefill evaluations by current reviewer if any
        const initialComments: { [key: number]: string } = {};
        const initialStatuses: { [key: number]: string } = {};

        const email = getEmailFromToken(token);

        res.forEach((doc: Document) => {
          const myEval = doc.evaluations.find(
            (ev) => ev.reviewer === email
          );
          if (myEval) {
            initialComments[doc.id] = myEval.comment;
            initialStatuses[doc.id] = myEval.status;
          }
        });

        setComments(initialComments);
        setStatuses(initialStatuses);
      } catch (err) {
        console.error("Failed to load documents", err);
      }
    };
    loadDocuments();
  }, [token]);

  // Helper to decode JWT token payload, extract email
  function getEmailFromToken(token: string | null): string | null {
    if (!token) return null;
    try {
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(base64)
          .split('')
          .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      return JSON.parse(jsonPayload).sub;
    } catch {
      return null;
    }
  }

  const handleSubmit = async (docId: number) => {
    if (!token) return;
    if (!statuses[docId]) {
      alert("Please select a status.");
      return;
    }
    if (!comments[docId]) {
      alert("Please add a comment.");
      return;
    }
    try {
      await submitEvaluation(token, docId, {
        comment: comments[docId],
        status: statuses[docId],
      });
      alert("Evaluation submitted");
      // Optionally reload documents or update state here
    } catch (err) {
      alert("Failed to submit evaluation");
    }
  };

  return (
    <div style={{ padding: 20 }}>
      <h2>Reviewer Dashboard</h2>
      {documents.length === 0 ? (
        <p>No documents uploaded yet.</p>
      ) : (
        documents.map((doc) => (
          <div
            key={doc.id}
            style={{ marginBottom: 20, border: "1px solid #ccc", padding: 12, borderRadius: 6 }}
          >
            <strong>{doc.title}</strong> ({doc.organization}) — uploaded by {doc.uploaded_by} —{" "}
            <a
              href={doc.url}
              target="_blank"
              rel="noopener noreferrer"
              download
              style={{ marginLeft: 10, color: "blue", textDecoration: "underline" }}
            >
              Download
            </a>

            <div style={{ marginTop: 10 }}>
              <h4>Previous Evaluations:</h4>
              {doc.evaluations.length === 0 ? (
                <p>No evaluations yet.</p>
              ) : (
                <ul>
                  {doc.evaluations.map((ev, idx) => (
                    <li key={idx}>
                      <strong>{ev.reviewer}</strong>: {ev.status} - {ev.comment}
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div style={{ marginTop: 10 }}>
              <h4>Your Evaluation</h4>
              <select
                value={statuses[doc.id] || ""}
                onChange={(e) => setStatuses({ ...statuses, [doc.id]: e.target.value })}
              >
                <option value="">Select status</option>
                <option value="approved">Approved</option>
                <option value="needs revision">Needs Revision</option>
              </select>
              <br />
              <textarea
                placeholder="Add your comment"
                value={comments[doc.id] || ""}
                onChange={(e) => setComments({ ...comments, [doc.id]: e.target.value })}
                style={{ width: "100%", height: 60, marginTop: 5 }}
              />
              <br />
              <button onClick={() => handleSubmit(doc.id)}>Submit Evaluation</button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// Add this line to fix TS1208 if needed
export {};
