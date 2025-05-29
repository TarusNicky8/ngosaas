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
      // Fetch all users
      const usersData = await fetchAllUsers(token);
      setUsers(usersData);
      console.log("Admin: Users fetched:", usersData);

      // Fetch all documents
      const documentsData = await fetchAllDocuments(token);
      setDocuments(documentsData);
      console.log("Admin: Documents fetched:", documentsData);

    } catch (err) {
      console.error("Admin Dashboard failed to load data:", err);
      setError("Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAssignReviewer = async (docId: number) => {
    if (!selectedReviewer) {
      setAssignMessage('Please select a reviewer.');
      return;
    }
    setAssignMessage(null);
    try {
      const reviewerId = parseInt(selectedReviewer);
      const updatedDoc = await assignReviewerToDocument(token, docId, reviewerId);
      setAssignMessage(`Reviewer assigned to document ID ${docId} successfully!`);
      console.log('Assigned reviewer:', updatedDoc);
      // Refresh documents to show the updated assignment
      loadData();
    } catch (err: any) {
      console.error("Failed to assign reviewer:", err);
      setAssignMessage(`Failed to assign reviewer: ${err.message || 'Unknown error'}`);
    }
  };

  // Filter users to get only reviewers for the dropdown
  const reviewers = users.filter(user => user.role === 'reviewer');

  if (loading) {
    return <p>Loading Admin Dashboard...</p>;
  }

  if (error) {
    return <p style={{ color: 'red' }}>Error: {error}</p>;
  }

  return (
    <div className="p-6 bg-gray-100 min-h-screen rounded-lg shadow-md">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Admin Dashboard</h2>

      {assignMessage && (
        <div className={`p-4 mb-4 rounded-md ${assignMessage.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
          {assignMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* All Users Section */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xl font-semibold text-gray-700 mb-4">All Users</h3>
          {users.length === 0 ? (
            <p>No users found.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {users.map(user => (
                <li key={user.id} className="py-2">
                  <p className="text-gray-800"><strong>ID:</strong> {user.id}</p>
                  <p className="text-gray-800"><strong>Email:</strong> {user.email}</p>
                  <p className="text-gray-600"><strong>Role:</strong> {user.role}</p>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* All Documents Section */}
        <div className="bg-white p-4 rounded-lg shadow">
          <h3 className="text-xl font-semibold text-gray-700 mb-4">All Documents</h3>
          {documents.length === 0 ? (
            <p>No documents found.</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {documents.map(doc => (
                <li key={doc.id} className="py-4">
                  <p className="text-gray-800"><strong>ID:</strong> {doc.id}</p>
                  <p className="text-gray-800"><strong>Title:</strong> {doc.title}</p>
                  <p className="text-gray-600"><strong>Organization:</strong> {doc.organization}</p>
                  <p className="text-gray-600"><strong>Uploaded by:</strong> {doc.uploaded_by || 'N/A'}</p>
                  <p className="text-gray-600"><strong>Assigned Reviewer:</strong> {doc.assigned_reviewer_email || 'Not Assigned'}</p>
                  <a href={doc.url} target="_blank" rel="noreferrer" className="text-blue-500 hover:underline">Download</a>

                  {/* Reviewer Assignment Section */}
                  <div className="mt-3 p-3 bg-gray-50 rounded-md">
                    <h5 className="text-md font-medium text-gray-700 mb-2">Assign Reviewer</h5>
                    <select
                      className="block w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
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
                      className="mt-2 px-4 py-2 bg-blue-600 text-white font-semibold rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      Assign
                    </button>
                  </div>

                  {/* Display Evaluations */}
                  <div className="mt-4">
                    <h5 className="text-md font-medium text-gray-700 mb-2">Evaluations:</h5>
                    {doc.evaluations && doc.evaluations.length > 0 ? (
                      <ul className="ml-4 list-disc list-inside text-gray-700">
                        {doc.evaluations.map((evaluation: any, evalIdx: number) => (
                          <li key={evalIdx} className="mb-1">
                            <p><strong>Reviewer:</strong> {evaluation.reviewer_email || 'N/A'}</p>
                            <p><strong>Status:</strong> {evaluation.status}</p>
                            <p><strong>Comment:</strong> {evaluation.comment}</p>
                            <p className="text-sm text-gray-500">Date: {new Date(evaluation.created_at).toLocaleDateString()}</p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-gray-500">No evaluations yet.</p>
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
