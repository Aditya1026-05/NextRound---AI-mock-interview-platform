/**
 * apiFetch — Authenticated fetch wrapper with automatic token refresh.
 *
 * On any 401 response it attempts a token refresh via POST /auth/refresh.
 * If the refresh succeeds, the original request is retried once with the new token.
 * If the refresh fails, the user is logged out and redirected to /login.
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = 'ApiError';
  }
}

async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refreshToken');
  if (!refreshToken) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    if (!data.access_token) return null;

    // Persist the new tokens
    localStorage.setItem('token', data.access_token);
    if (data.refresh_token) {
      localStorage.setItem('refreshToken', data.refresh_token);
    }

    return data.access_token;
  } catch {
    return null;
  }
}

function logoutAndRedirect() {
  localStorage.removeItem('token');
  localStorage.removeItem('refreshToken');
  localStorage.removeItem('profile');
  // Hard redirect to login — Zustand state will clear on re-init
  window.location.href = '/login';
}

/**
 * Drop-in replacement for fetch() that:
 * - Attaches the current Bearer token automatically
 * - Refreshes the token and retries on 401
 * - Throws ApiError on non-2xx responses
 */
export async function apiFetch(
  path: string,
  options: RequestInit = {},
  retried = false,
): Promise<Response> {
  const token = localStorage.getItem('token');

  const headers = new Headers(options.headers ?? {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!headers.has('Content-Type') && options.body) {
    headers.set('Content-Type', 'application/json');
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  // Token expired — attempt refresh once
  if (res.status === 401 && !retried) {
    const newToken = await tryRefreshToken();
    if (newToken) {
      // Retry with new token
      return apiFetch(path, options, true);
    } else {
      logoutAndRedirect();
      throw new ApiError(401, 'Session expired. Please log in again.');
    }
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.clone().json();
      detail = body.detail || body.message || detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res;
}
