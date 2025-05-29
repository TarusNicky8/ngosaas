import React, { useEffect, useState, useCallback } from 'react'; // Import useCallback
import Upload from '../components/Upload';
import { fetchGranteeDocuments } from '../services/api';

const GranteeDashboard: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const token = localStorage.getItem('token') || '';

  // Wrapped loadDocuments in useCallback to make it stable across renders
  // This resolves the react-hooks/exhaustive-deps warning
  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGranteeDocuments(token);
      console.log("Grantee documents fetched:", data);
      // --- IMPORTANT DEBUGGING STEP ---
      data.forEach((doc: any) => {
        if (doc.evaluations && doc.evaluations.length > 0) {
          console.log(`Document ID ${doc.id} has evaluations:`, doc.evaluations);
        } else {
          console.log(`Document ID ${doc.id} has NO evaluations or evaluations array is empty.`);
        }
      });
      // --- END DEBUGGING STEP ---
      setDocuments(data);
    } catch (error) {
      console.error("Failed to fetch documents", error);
      setError("Failed to load documents.");
    } finally {
      setLoading(false);
    }
  }, [token]); // 'token' is a dependency of loadDocuments

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]); // Now 'loadDocuments' is correctly included in the dependency array

  return (
    <div>
      <h2>Grantee Dashboard</h2>
      <Upload onUploadSuccess={loadDocuments} />

      <h3>Your Documents</h3>
      {loading && <p>Loading documents...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}

      {!loading && documents.length === 0 && <p>No uploaded documents found.</p>}

      <ul>
        {documents.map((doc) => (
          <li key={doc.id} style={{ marginBottom: '20px' }}>
            <strong>Title:</strong> {doc.title}<br />
            <strong>Organization:</strong> {doc.organization}<br />
            {/* Assuming doc.url is correct for download */}
            <a href={doc.url} target="_blank" rel="noreferrer">Download Document</a>
            <h4>Evaluations:</h4>
            {/* Check if doc.evaluations exists and has length > 0 */}
            {doc.evaluations && doc.evaluations.length > 0 ? (
              <ul>
                {doc.evaluations.map((evaluation: any, idx: number) => (
                  <li key={idx} style={{ border: '1px solid #eee', padding: '10px', marginBottom: '5px' }}>
                    <strong>Reviewer:</strong> {evaluation.reviewer_email} <br />
                    <strong>Status:</strong> {evaluation.status} <br />
                    <strong>Comment:</strong> {evaluation.comment} <br />
                    {/* OPTIONAL: Display created_at */}
                    <strong>Date:</strong> {new Date(evaluation.created_at).toLocaleDateString()}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No evaluations yet.</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default GranteeDashboard;
