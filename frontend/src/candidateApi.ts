
const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";
const TOKEN_KEY = "brightcore_candidate_token";
const AUTH_CHANGE_EVENT = "brightcore-auth-change";

export interface CandidateProfile {
  id: string;
  full_name: string;
  email: string;
  role: string;
  created_at: string;
}

export interface AuthenticatedUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface CandidateApplication {
  id: string;
  job_id: string;
  job_title: string;
  full_name: string;
  email: string;
  status: "submitted" | "under_review" | "accepted" | "rejected";
  status_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface CandidateApplicationsResponse {
  items: CandidateApplication[];
  total: number;
}

export function getCandidateToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function saveCandidateToken(token: string) {
  sessionStorage.setItem(TOKEN_KEY, token);
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

export function clearCandidateToken() {
  sessionStorage.removeItem(TOKEN_KEY);
  window.dispatchEvent(new Event(AUTH_CHANGE_EVENT));
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  authenticated = false,
): Promise<T> {
  const headers = new Headers(options.headers);

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const token = getCandidateToken();

    if (!token) {
      throw new Error("Please sign in to continue.");
    }

    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error("Your session may have expired. Please sign in again.");
    }

    const message = payload?.error?.message;
    throw new Error(
      typeof message === "string"
        ? message
        : `Request failed (HTTP ${response.status}).`,
    );
  }

  if (payload?.success !== true) {
    throw new Error("The server returned an invalid response.");
  }

  return payload.data as T;
}

export async function registerCandidate(input: {
  full_name: string;
  email: string;
  password: string;
}) {
  return apiRequest<CandidateProfile>("/auth/register", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export async function loginCandidate(input: {
  email: string;
  password: string;
}) {
  const result = await apiRequest<{
    access_token: string;
    token_type: string;
  }>("/auth/login", {
    method: "POST",
    body: JSON.stringify(input),
  });

  saveCandidateToken(result.access_token);

  try {
    const user = await fetchAuthenticatedUser();

    if (!user.is_active || !["candidate", "admin"].includes(user.role)) {
      throw new Error("This account does not have access to a portal.");
    }

    return user;
  } catch (error) {
    clearCandidateToken();
    throw error;
  }
}

export function fetchCandidateProfile() {
  return apiRequest<CandidateProfile>("/candidate/profile", {}, true);
}

export function fetchAuthenticatedUser() {
  return apiRequest<AuthenticatedUser>("/auth/me", {}, true);
}

export function fetchCandidateApplications() {
  return apiRequest<CandidateApplicationsResponse>(
    "/candidate/applications",
    {},
    true,
  );
}
