export const API_BASE = "http://localhost:8000";

// ✅ Register a new user
export async function register(email: string, password: string, role: string): Promise<any> {
  const res = await fetch(`${API_BASE}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, role }),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to register");
  }

  return await res.json();
}

// ✅ Login
export async function login(email: string, password: string): Promise<any> {
  const formData = new URLSearchParams();
  formData.append("username", email);
  formData.append("password", password);

  const res = await fetch(`${API_BASE}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: formData.toString(),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Login failed");
  }

  return await res.json(); // { access_token, token_type }
}

// ✅ Dashboard fetch
export async function fetchDashboard(token: string): Promise<any> {
  const res = await fetch(`${API_BASE}/dashboard`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to load dashboard");
  }

  return await res.json();
}

// ✅ Upload document
export async function uploadDocument(
  title: string,
  organization: string,
  file: File,
  token: string
): Promise<any> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("organization", organization);
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/upload-doc`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Upload failed");
  }

  return await res.json();
}

// ✅ Fetch all uploaded documents (for reviewer dashboard)
export async function fetchDocuments(token: string): Promise<any[]> {
  const res = await fetch(`${API_BASE}/documents`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to fetch documents");
  }

  return await res.json();
}

// ✅ NEW: Submit evaluation
export async function submitEvaluation(
  token: string,
  docId: number,
  data: { comment: string; status: string }
): Promise<any> {
  const res = await fetch(`${API_BASE}/documents/${docId}/evaluate`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    const error = await res.json();
    throw new Error(error.detail || "Failed to submit evaluation");
  }

  return await res.json();
}
