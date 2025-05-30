import React, { useEffect, useState, useCallback } from 'react';
import Upload from '../components/Upload'; // Assuming Upload component is in components folder
import { fetchGranteeDocuments } from '../services/api';

const GranteeDashboard: React.FC = () => {
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const token = localStorage.getItem('token') || '';

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGranteeDocuments(token);
      console.log("Grantee documents fetched:", data);
      setDocuments(data);
    } catch (error) {
      console.error("Failed to fetch documents", error);
      setError("Failed to load documents. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-blue-50">
        <p className="text-lg text-blue-700">Loading Your Documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-red-50">
        <p className="text-lg text-red-700 font-medium">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="p-8 bg-gradient-to-br from-blue-50 to-indigo-100 min-h-screen font-sans">
      <h2 className="text-4xl font-extrabold text-indigo-800 mb-8 text-center">
        Your Grantee Dashboard
      </h2>

      {/* Upload Document Section */}
      <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-100 mb-8">
        <h3 className="text-2xl font-bold text-blue-700 mb-6 border-b pb-3">
          Upload New Document
        </h3>
        <Upload onUploadSuccess={loadDocuments} />
      </div>

      {/* Your Submitted Documents Section */}
      <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-100">
        <h3 className="text-2xl font-bold text-blue-700 mb-6 border-b pb-3">
          Your Submitted Documents
        </h3>
        {!loading && documents.length === 0 ? (
          <p className="text-gray-600">You haven't uploaded any documents yet.</p>
        ) : (
          <ul className="divide-y divide-blue-100">
            {documents.map((doc) => (
              <li key={doc.id} className="py-6 hover:bg-blue-50 transition duration-150 ease-in-out px-2 rounded-md">
                <div className="mb-4">
                  <p className="text-gray-900 font-bold text-xl mb-1">{doc.title}</p>
                  <p className="text-gray-700 text-sm">
                    <span className="font-semibold">Organization:</span> {doc.organization}
                  </p>
                  <p className="text-gray-700 text-sm">
                    <span className="font-semibold">Uploaded by:</span> {doc.uploaded_by || 'N/A'}
                  </p>
                  {doc.url && (
                    <a href={doc.url} target="_blank" rel="noreferrer"
                       className="inline-flex items-center text-teal-600 hover:text-teal-800 font-medium transition duration-150 ease-in-out mt-2">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        Download Document
                    </a>
                  )}
                </div>

                {/* Display Evaluations */}
                <div className="mt-5 p-4 bg-purple-50 rounded-lg border border-purple-100">
                  <h5 className="text-lg font-semibold text-purple-800 mb-3">Evaluations:</h5>
                  {doc.evaluations && doc.evaluations.length > 0 ? (
                    <ul className="space-y-3">
                      {doc.evaluations.map((evaluation: any, evalIdx: number) => (
                        <li key={evalIdx} className="p-3 bg-white rounded-md shadow-sm border border-purple-100">
                          <p className="text-gray-900 font-medium">
                            <span className="font-semibold">Reviewer:</span> {evaluation.reviewer_email || 'N/A'}
                          </p>
                          <p className="text-gray-700 text-sm">
                            <span className="font-semibold">Status:</span>{' '}
                            <span className={`font-medium ${evaluation.status === 'approved' ? 'text-green-600' : evaluation.status === 'needs revision' ? 'text-orange-600' : 'text-red-600'}`}>
                              {evaluation.status.charAt(0).toUpperCase() + evaluation.status.slice(1)}
                            </span>
                          </p>
                          <p className="text-gray-700 text-sm">
                            <span className="font-semibold">Comment:</span> {evaluation.comment}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            Date: {new Date(evaluation.created_at).toLocaleDateString()}
                          </p>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-600">No evaluations yet for this document.</p>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default GranteeDashboard;
