import React, { useEffect, useState, useCallback } from "react";
import { fetchDashboard } from "../services/api";
import { useNavigate } from "react-router-dom";
import GranteeDashboard from './GranteeDashboard';
import ReviewerDashboard from './ReviewerDashboard'; // Ensure this is imported
import AdminDashboard from './AdminDashboard'; // Ensure this is imported

export default function Dashboard() {
  const navigate = useNavigate();
  const [role, setRole] = useState<string | null>(null); // Initialize role as null
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const token = localStorage.getItem("token") || "";

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    setError(null);
    if (!token) {
      navigate("/login");
      return;
    }

    try {
      const res = await fetchDashboard(token);
      setRole(res.role);
    } catch (err) {
      console.error("Dashboard load error", err);
      setError("Failed to load dashboard. Please try logging in again.");
      localStorage.removeItem('token'); // Clear invalid token
      localStorage.removeItem('role');
      navigate("/login"); // Redirect to login on error
    } finally {
      setLoading(false);
    }
  }, [token, navigate]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-100">
        <p className="text-lg text-gray-700">Loading your dashboard...</p>
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

  // Render specific dashboard based on role
  switch (role) {
    case "grantee":
      return <GranteeDashboard />;
    case "reviewer":
      return <ReviewerDashboard />;
    case "admin":
      return <AdminDashboard />;
    default:
      return (
        <div className="flex items-center justify-center min-h-screen bg-gray-100">
          <p className="text-lg text-gray-700">No role assigned or invalid role.</p>
        </div>
      );
  }
}
