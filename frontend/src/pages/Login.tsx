import { useState } from "react";
import { login } from "../services/api"; // Your API call to backend
import { useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("Submitting login with:", email, password); // ✅ Debug log

    try {
      const res = await login(email, password);
      console.log("Login success:", res); // ✅ Debug log
      localStorage.setItem("token", res.access_token);
      navigate("/dashboard");
    } catch (err) {
      console.error("Login failed:", err); // ✅ Debug log
      alert("Login failed. Check credentials or server.");
    }
  };

  return (
    <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "10px", width: "300px", margin: "auto" }}>
      <h2>Login</h2>
      <input
        placeholder="Email"
        type="email"
        value={email}
        onChange={e => setEmail(e.target.value)}
        required
      />
      <input
        placeholder="Password"
        type="password"
        value={password}
        onChange={e => setPassword(e.target.value)}
        required
      />
      <button type="submit">Login</button>
    </form>
  );
}
