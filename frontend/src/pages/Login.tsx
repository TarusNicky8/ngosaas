import React, { useState } from "react";
import { login, fetchDashboard } from "../services/api";
import { useNavigate, Link } from "react-router-dom";

interface LoginProps {
  onLogin: () => void; // Passed from App.tsx to update token/role state
}

export default function Login({ onLogin }: LoginProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null); // Clear previous errors

    try {
      const res = await login(email, password);
      localStorage.setItem("token", res.access_token);

      const dashboardData = await fetchDashboard(res.access_token);
      localStorage.setItem("role", dashboardData.role);

      onLogin(); // Notify parent (App.tsx) that login happened
      navigate("/dashboard");
    } catch (err: any) {
      console.error("Login failed:", err);
      setError("Login failed. Please check your credentials or try again later.");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 px-4">
      <form
        onSubmit={handleLogin}
        className="bg-white p-8 rounded-lg shadow-xl border border-gray-200 w-full max-w-md space-y-6"
      >
        <h2 className="text-3xl font-extrabold text-center text-gray-900 mb-6">Login</h2>

        {error && (
          <div className="p-3 bg-red-100 text-red-700 rounded-md text-sm font-medium border border-red-200">
            ⚠️ {error}
          </div>
        )}

        <div>
          <label htmlFor="email" className="sr-only">Email address</label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Email address"
            className="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-base"
          />
        </div>
        <div>
          <label htmlFor="password" className="sr-only">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Password"
            className="appearance-none relative block w-full px-4 py-3 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-base"
          />
        </div>

        <button
          type="submit"
          className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-lg font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition duration-150 ease-in-out"
        >
          Sign In
        </button>

        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="font-medium text-indigo-600 hover:text-indigo-500">
            Register Here
          </Link>
        </p>
      </form>
    </div>
  );
}
