import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard"; // general dashboard or fallback
import ReviewerDashboard from "./pages/ReviewerDashboard";
import Navbar from "./components/Navbar";

function App() {
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<string | null>(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    setToken(savedToken);
    setRole(savedRole);
  }, []);

  const handleLogin = () => {
    const savedToken = localStorage.getItem("token");
    const savedRole = localStorage.getItem("role");
    setToken(savedToken);
    setRole(savedRole);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    setToken(null);
    setRole(null);
  };

  // Function to render dashboard based on role
  function renderDashboard() {
    if (!token || !role) return <Navigate to="/login" />;
    if (role === "reviewer") return <ReviewerDashboard />;
    // Add other roles here like grantee, admin
    return <Dashboard />; // fallback/general dashboard
  }

  return (
    <Router>
      <Navbar token={token} onLogout={handleLogout} />
      <Routes>
        <Route path="/" element={<Navigate to="/login" />} />
        <Route
          path="/login"
          element={!token ? <Login onLogin={handleLogin} /> : <Navigate to="/dashboard" />}
        />
        <Route
          path="/register"
          element={!token ? <Register /> : <Navigate to="/dashboard" />}
        />
        <Route path="/dashboard" element={renderDashboard()} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Router>
  );
}

export default App;
