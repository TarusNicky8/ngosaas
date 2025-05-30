import React, { useEffect, useState, useCallback } from "react";
import { fetchDocuments, submitEvaluation } from "../services/api";

interface Evaluation {
  reviewer_email: string; // Changed from 'reviewer' to 'reviewer_email'
  comment: string;
  status: string;
  created_at: string;
}

interface Document {
  id: number;
  title: string;
  organization: string;
  filename: string;
  uploaded_by: string;
  url: string;
  evaluations: Evaluation[];
  assigned_reviewer_id: number | null; // Added for filtering
  assigned_reviewer_email: string | null; // Added for display
}

export default function ReviewerDashboard() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [comments, setComments] = useState<{ [key: number]: string }>({});
  const [statuses, setStatuses] = useState<{ [key: number]: string }>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);

  const token = localStorage.getItem("token");

  // Helper to decode JWT token payload, extract email
  const getEmailFromToken = useCallback((token: string | null): string | null => {
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
      return JSON.parse(jsonPayload).sub; // 'sub' field typically holds the email
    } catch {
      return null;
    }
  }, []);

  // Helper to get current reviewer ID from token
  const getCurrentReviewerId = useCallback((token: string | null): number | null => {
    if (!token) return null;
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return payload.id || null; // Assuming 'id' field in token payload is the user ID
    } catch (e) {
      console.error("Error decoding token for reviewer ID:", e);
      return null;
    }
  }, []);

  const loadDocuments = useCallback(async () => {
    setLoading(true);
    setError(null);
    setSubmitMessage(null); // Clear messages on load
    if (!token) {
      setError("Authentication token not found.");
      setLoading(false);
      return;
    }

    try {
      const res = await fetchDocuments(token);
      setDocuments(res);

      const initialComments: { [key: number]: string } = {};
      const initialStatuses: { [key: number]: string } = {};
      const currentReviewerEmail = getEmailFromToken(token);

      res.forEach((doc: Document) => {
        const myEval = doc.evaluations.find(
          (ev) => ev.reviewer_email === currentReviewerEmail // Changed from 'reviewer' to 'reviewer_email'
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
      setError("Failed to load documents for review. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [token, getEmailFromToken]); // Added getEmailFromToken to dependency array

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  const handleSubmit = async (docId: number) => {
    if (!token) return;
    if (!statuses[docId]) {
      setSubmitMessage("Please select a status for the evaluation.");
      return;
    }
    if (!comments[docId]) {
      setSubmitMessage("Please add a comment for the evaluation.");
      return;
    }
    setSubmitMessage(null); // Clear previous message
    try {
      await submitEvaluation(token, docId, {
        comment: comments[docId],
        status: statuses[docId],
      });
      setSubmitMessage("Evaluation submitted successfully!");
      loadDocuments(); // Reload documents to show updated evaluation
    } catch (err: any) {
      console.error("Failed to submit evaluation", err);
      setSubmitMessage(`Failed to submit evaluation: ${err.message || 'Unknown error'}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-lg text-gray-700">Loading documents for review...</p>
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

  const currentReviewerId = getCurrentReviewerId(token);

  // Filter documents to show only those assigned to the current reviewer
  const documentsToReview = documents.filter(doc =>
    doc.assigned_reviewer_id === currentReviewerId
  );

  return (
    <div className="p-8 bg-gradient-to-br from-purple-50 to-pink-100 min-h-screen font-sans">
      <h2 className="text-4xl font-extrabold text-purple-800 mb-8 text-center">
        Reviewer Dashboard
      </h2>

      {submitMessage && (
        <div className={`p-4 mb-6 rounded-lg shadow-md text-center
          ${submitMessage.includes('successfully') ? 'bg-green-100 text-green-800 border border-green-200' : 'bg-red-100 text-red-800 border border-red-200'}`}>
          {submitMessage}
        </div>
      )}

      <div className="bg-white p-6 rounded-xl shadow-lg border border-purple-100">
        <h3 className="text-2xl font-bold text-purple-700 mb-6 border-b pb-3">
          Documents for Your Review
        </h3>
        {documentsToReview.length === 0 ? (
          <p className="text-gray-600">No documents assigned for your review yet.</p>
        ) : (
          <ul className="divide-y divide-purple-100">
            {documentsToReview.map((doc) => (
              <li key={doc.id} className="py-6 hover:bg-purple-50 transition duration-150 ease-in-out px-2 rounded-md">
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
                       className="inline-flex items-center text-blue-600 hover:text-blue-800 font-medium transition duration-150 ease-in-out mt-2">
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                        Download Document
                    </a>
                  )}
                </div>

                {/* Previous Evaluations */}
                <div className="mt-5 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">Previous Evaluations:</h4>
                  {doc.evaluations.length === 0 ? (
                    <p className="text-gray-600">No previous evaluations for this document.</p>
                  ) : (
                    <ul className="space-y-3">
                      {doc.evaluations.map((ev, idx) => (
                        <li key={idx} className="p-3 bg-white rounded-md shadow-sm border border-gray-100">
                          <p className="text-gray-900 font-medium">
                            <span className="font-semibold">Reviewer:</span> {ev.reviewer_email}
                          </p>
                          <p className="text-gray-700 text-sm">
                            <span className="font-semibold">Status:</span>{' '}
                            <span className={`font-medium ${ev.status === 'approved' ? 'text-green-600' : ev.status === 'needs revision' ? 'text-orange-600' : 'text-red-600'}`}>
                              {ev.status.charAt(0).toUpperCase() + ev.status.slice(1)}
                            </span>
                          </p>
                          <p className="text-gray-700 text-sm">
                            <span className="font-semibold">Comment:</span> {ev.comment}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            Date: {new Date(ev.created_at).toLocaleDateString()}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>

                {/* Your Evaluation Section */}
                <div className="mt-5 p-4 bg-purple-50 rounded-lg border border-purple-200">
                  <h4 className="text-lg font-semibold text-purple-800 mb-3">Your Evaluation</h4>
                  <select
                    className="block w-full p-2.5 border border-purple-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-800"
                    value={statuses[doc.id] || ""}
                    onChange={(e) => setStatuses({ ...statuses, [doc.id]: e.target.value })}
                  >
                    <option value="">Select status</option>
                    <option value="approved">Approved</option>
                    <option value="needs revision">Needs Revision</option>
                    <option value="rejected">Rejected</option> {/* Added Rejected option */}
                  </select>
                  <textarea
                    placeholder="Add your comment"
                    value={comments[doc.id] || ""}
                    onChange={(e) => setComments({ ...comments, [doc.id]: e.target.value })}
                    className="block w-full p-2.5 mt-3 border border-purple-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 bg-white text-gray-800 min-h-[80px]"
                  />
                  <button
                    onClick={() => handleSubmit(doc.id)}
                    className="mt-4 w-full sm:w-auto px-6 py-2 bg-purple-600 text-white font-semibold rounded-lg shadow-md hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition duration-150 ease-in-out"
                  >
                    Submit Evaluation
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
