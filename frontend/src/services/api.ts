let rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Safely handle if the user accidentally pasted "KEY=value" in the hosting platform's value field
if (rawApiUrl.startsWith('VITE_API_URL=')) {
  rawApiUrl = rawApiUrl.replace('VITE_API_URL=', '');
}
// Strip any accidental quotes
rawApiUrl = rawApiUrl.replace(/^["']|["']$/g, '');
// Remove trailing slash if present
if (rawApiUrl.endsWith('/')) {
  rawApiUrl = rawApiUrl.slice(0, -1);
}

const API_BASE_URL = rawApiUrl;

class ApiClient {
  private getHeaders(): HeadersInit {
    const token = localStorage.getItem('access_token') || localStorage.getItem('supabase_access_token');
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  async get<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    if (res.status === 401) {
      // If unauthorized, clear invalid token
      localStorage.removeItem('access_token');
      localStorage.removeItem('is_authenticated');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  async post<T>(endpoint: string, body?: any): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('is_authenticated');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  async postStream(endpoint: string, body?: any): Promise<Response> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('is_authenticated');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res;
  }

  async put<T>(endpoint: string, body?: any): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('is_authenticated');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }

  async delete<T>(endpoint: string): Promise<T> {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    if (res.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('is_authenticated');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || `Request failed with status ${res.status}`);
    }
    return res.json();
  }
}

export const api = new ApiClient();
