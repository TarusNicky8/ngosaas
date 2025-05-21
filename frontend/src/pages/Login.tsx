import { useState } from "react";
import { login, fetchDashboard } from "../services/api";
import { useNavigate, Link } from "react-router-dom";

interface LoginProps {
  onLogin: () => void; // Passed from App.tsx to update token/role state
}

export default function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      // Call login API to get token and (optionally) role if your backend returns role here
      const res = await login(email, password);

      // Save token in localStorage
      localStorage.setItem("token", res.access_token);

      // Fetch dashboard data to get role info
      const dashboardData = await fetchDashboard(res.access_token);

      // Save role in localStorage
      localStorage.setItem("role", dashboardData.role);

      // Notify parent (App.tsx) that login happened so it updates state
      onLogin();

      // Navigate to dashboard route
      navigate("/dashboard");
    } catch (error) {
      alert("Login failed. Check credentials or server.");
      console.error(error);
    }
  };

  return (
    <form
      onSubmit={handleLogin}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        width: "300px",
        margin: "50px auto",
      }}
    >
      <h2>Login</h2>
      <input
        placeholder="Email"
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        placeholder="Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <button type="submit">Login</button>
      <p>
        Don't have an account? <Link to="/register">Register</Link>
      </p>
    </form>
  );
}
