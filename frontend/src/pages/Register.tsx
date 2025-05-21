import { useState } from "react";
import { register } from "../services/api";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("grantee");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null); // Reset any previous error
    try {
      await register(email, password, role);
      alert("Registered successfully!");
      navigate("/login");
    } catch (err: any) {
      setError(err.message || "An unknown error occurred");
    }
  };

  return (
    <form
      onSubmit={handleRegister}
      style={{
        display: "flex",
        flexDirection: "column",
        gap: "10px",
        width: "300px",
        margin: "50px auto",
      }}
    >
      <h2>Register</h2>

      {error && (
        <div style={{ color: "red", fontWeight: "bold" }}>
          ⚠️ {error}
        </div>
      )}

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
      <select value={role} onChange={(e) => setRole(e.target.value)} required>
        <option value="grantee">Grantee</option>
        <option value="reviewer">Reviewer</option>
        <option value="admin">Admin</option>
      </select>
      <button type="submit">Register</button>
      <p>
        Already have an account? <Link to="/login">Login</Link>
      </p>
    </form>
  );
}
