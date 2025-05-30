import React, { useEffect, useState, useCallback } from 'react';
import { fetchAllUsers, fetchAllDocuments, assignReviewerToDocument } from '../services/api';

const AdminDashboard: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedReviewer, setSelectedReviewer] = useState<string>(''); // Stores reviewer ID for assignment
  const [assignMessage, setAssignMessage] = useState<string | null>(null);

  const token = localStorage.getItem('token') || '';

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setAssignMessage(null); // Clear assignment message on data load
    try {
      const usersData = await fetchAllUsers(token);
      setUsers(usersData);
      console.log("Admin: Users fetched:", usersData);

      const documentsData = await fetchAllDocuments(token);
      setDocuments(documentsData);
      console.log("Admin: Documents fetched:", documentsData);

    } catch (err) {
      console.error("Admin Dashboard failed to load data:", err);
      setError("Failed to load admin data. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAssignReviewer = async (docId: number) => {
    if (!selectedReviewer) {
      setAssignMessage('Please select a reviewer to assign.');
      return;
    }
    setAssignMessage(null); // Clear previous message
    try {
      const reviewerId = parseInt(selectedReviewer);
      await assignReviewerToDocument(token, docId, reviewerId);
      setAssignMessage(`Reviewer assigned to Document ID ${docId} successfully!`);
      setSelectedReviewer(''); // Clear selection after assignment
      loadData(); // Refresh documents to show the updated assignment
    } catch (err: any) {
      console.error("Failed to assign reviewer:", err);
      setAssignMessage(`Failed to assign reviewer: ${err.message || 'Unknown error'}`);
    }
  };

  const reviewers = users.filter(user => user.role === 'reviewer');

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-blue-50">
        <p className="text-lg text-blue-700">Loading Admin Dashboard...</p>
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
    <div className="p-8 bg-blue-50 min-h-screen font-sans">
      <h2 className="text-4xl font-extrabold text-blue-800 mb-8 text-center">
        Admin Dashboard
      </h2>

      {assignMessage && (
        <div className={`p-4 mb-6 rounded-lg shadow-md text-center
          ${assignMessage.includes('successfully') ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'}`}>
          {assignMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* All Users Section */}
        <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-100">
          <h3 className="text-2xl font-bold text-indigo-700 mb-6 border-b pb-3">
            All Users
          </h3>
          {users.length === 0 ? (
            <p className="text-gray-600">No users found in the system.</p>
          ) : (
            <ul className="divide-y divide-blue-100">
              {users.map(user => (
                <li key={user.id} className="py-4 flex flex-col sm:flex-row justify-between items-start sm:items-center hover:bg-blue-50 transition duration-150 ease-in-out px-2 rounded-md">
                  <div>
                    <p className="text-gray-900 font-semibold text-lg">
                      {user.email}
                    </p>
                    <p className="text-gray-600 text-sm">
                      ID: {user.id} | Role: <span className={`font-medium ${user.role === 'admin' ? 'text-purple-700' : user.role === 'reviewer' ? 'text-blue-700' : 'text-green-700'}`}>
                        {user.role.charAt(0).toUpperCase() + user.role.slice(1)}
                      </span>
                    </p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* All Documents Section */}
        <div className="bg-white p-6 rounded-xl shadow-lg border border-blue-100">
          <h3 className="text-2xl font-bold text-indigo-700 mb-6 border-b pb-3">
            All Documents
          </h3>
          {documents.length === 0 ? (
            <p className="text-gray-600">No documents have been uploaded yet.</p>
          ) : (
            <ul className="divide-y divide-blue-100">
              {documents.map(doc => (
                <li key={doc.id} className="py-6 hover:bg-blue-50 transition duration-150 ease-in-out px-2 rounded-md">
                  <div className="mb-4">
                    <p className="text-gray-900 font-bold text-xl mb-1">{doc.title}</p>
                    <p className="text-gray-700 text-sm">
                      <span className="font-semibold">Organization:</span> {doc.organization}
                    </p>
                    <p className="text-gray-700 text-sm">
                      <span className="font-semibold">Uploaded by:</span> {doc.uploaded_by || 'N/A'} (Grantee ID: {doc.grantee_id || 'N/A'})
                    </p>
                    <p className="text-gray-700 text-sm mb-2">
                      <span className="font-semibold">Assigned Reviewer:</span>{' '}
                      <span className="font-medium text-blue-700">
                        {doc.assigned_reviewer_email || 'Not Assigned'}
                        {doc.assigned_reviewer_id && ` (ID: ${doc.assigned_reviewer_id})`}
                      </span>
                    </p>
                    {doc.url && (
                        <a href={doc.url} target="_blank" rel="noreferrer"
                           className="inline-flex items-center text-teal-600 hover:text-teal-800 font-medium transition duration-150 ease-in-out">
                            <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            Download Document
                        </a>
                    )}
                  </div>

                  {/* Reviewer Assignment Section */}
                  <div className="mt-4 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                    <h5 className="text-lg font-semibold text-indigo-800 mb-3">Assign Reviewer</h5>
                    <select
                      className="block w-full p-2.5 border border-indigo-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 bg-white text-gray-800"
                      value={selectedReviewer}
                      onChange={(e) => setSelectedReviewer(e.target.value)}
                    >
                      <option value="">Select Reviewer</option>
                      {reviewers.map(reviewer => (
                        <option key={reviewer.id} value={reviewer.id}>
                          {reviewer.email} (ID: {reviewer.id})
                        </option>
                      ))}
                    </select>
                    <button
                      onClick={() => handleAssignReviewer(doc.id)}
                      className="mt-4 w-full sm:w-auto px-6 py-2 bg-indigo-600 text-white font-semibold rounded-lg shadow-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-150 ease-in-out"
                    >
                      Assign Reviewer
                    </button>
                  </div>

                  {/* Display Evaluations */}
                  <div className="mt-5 p-4 bg-blue-100 rounded-lg border border-blue-200">
                    <h5 className="text-lg font-semibold text-blue-800 mb-3">Evaluations:</h5>
                    {doc.evaluations && doc.evaluations.length > 0 ? (
                      <ul className="space-y-3">
                        {doc.evaluations.map((evaluation: any, evalIdx: number) => (
                          <li key={evalIdx} className="p-3 bg-white rounded-md shadow-sm border border-blue-100">
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
    </div>
  );
};

export default AdminDashboard;
