// frontend/services/api.ts
import axios from 'axios';

export const API_BASE = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
});

// Register a new user
export async function register(email: string, password: string, role: string): Promise<any> {
  try {
    const res = await api.post('/register', { email, password, role });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to register');
  }
}

// Login
export async function login(email: string, password: string): Promise<any> {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);

  try {
    const res = await api.post('/login', formData.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Login failed');
  }
}

// Fetch dashboard
export async function fetchDashboard(token: string): Promise<any> {
  try {
    const res = await api.get('/dashboard', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to load dashboard');
  }
}

// Upload document (Grantee specific)
export async function uploadDocument(
  title: string,
  organization: string,
  file: File,
  token: string
): Promise<any> {
  const formData = new FormData();
  formData.append('title', title);
  formData.append('organization', organization);
  formData.append('file', file);

  try {
    const res = await api.post('/grantee/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Upload failed');
  }
}

// Fetch documents for reviewers
export async function fetchDocuments(token: string): Promise<any[]> {
  try {
    // CORRECTED: Call the reviewer-specific endpoint
    const res = await api.get('/reviewer/documents', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch reviewer documents');
  }
}

// Submit evaluation (Reviewer specific)
export async function submitEvaluation(
  token: string,
  docId: number,
  data: { comment: string; status: string }
): Promise<any> {
  try {
    const res = await api.post(`/reviewer/documents/${docId}/evaluate`, data, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to submit evaluation');
  }
}

// Fetch grantee documents
export const fetchGranteeDocuments = async (token: string) => {
  try {
    const res = await api.get('/grantee/documents', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch grantee documents');
  }
};

// Fetch evaluations (Grantee)
export async function fetchEvaluations(token: string, docId: number): Promise<any[]> {
  try {
    const res = await api.get(`/grantee/documents/${docId}/evaluations`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch evaluations');
  }
}

// Admin API Calls
export async function fetchAllUsers(token: string): Promise<any[]> {
  try {
    const res = await api.get('/admin/users', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch all users (Admin)');
  }
}

export async function fetchAllDocuments(token: string): Promise<any[]> {
  try {
    const res = await api.get('/admin/documents', {
      headers: { Authorization: `Bearer ${token}` },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to fetch all documents (Admin)');
  }
}

export async function assignReviewerToDocument(token: string, docId: number, reviewerId: number): Promise<any> {
  try {
    const res = await api.post(`/admin/documents/${docId}/assign-reviewer`, { reviewer_id: reviewerId }, {
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
    return res.data;
  } catch (error: any) {
    throw new Error(error.response?.data?.detail || 'Failed to assign reviewer');
  }
}

export default api;
