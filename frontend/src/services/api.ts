const API_URL = "http://127.0.0.1:8000";

// ✅ Helper to get stored JWT token
function getToken() {
  return localStorage.getItem("token");
}

// ✅ Login function: sends email and password as form data, receives JWT
export async function login(email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData.toString(),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }

  return res.json(); // { access_token, token_type }
}

// ✅ Registration endpoint: sends JSON
export async function register(email: string, password: string) {
  const res = await fetch(`${API_URL}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Registration failed");
  }

  return res.json();
}

// ✅ Example: Fetch a protected route (e.g., /dashboard)
export async function fetchDashboardData() {
  const token = getToken();
  const res = await fetch(`${API_URL}/dashboard`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    throw new Error("Unauthorized or failed to fetch dashboard data");
  }

  return res.json();
}
