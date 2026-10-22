
import {
  clearCandidateToken,
  getCandidateToken,
} from "./candidateApi";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export interface AdminDashboardSummary {
  rejected_applications: number;
  accepted_applications: number;
  published_jobs: number;
  total_applications: number;
  pending_reviews: number;
  accepted: number;
  rejected: number;
}

export interface AdminJob {
  id: string;
  title: string;
  department: string;
  location: string;
  employment_type: string;
  description: string;
  requirements: string;
  salary_min: number | null;
  salary_max: number | null;
  status: "draft" | "published" | "closed";
  published_at: string | null;
  expires_at: string | null;
}

export interface AdminApplication {
  id: string;
  job_id: string;
  full_name: string;
  email: string;
  phone: string;
  cover_note: string | null;
  status: "submitted" | "under_review" | "accepted" | "rejected";
  status_note: string | null;
  created_at: string;
  updated_at: string;
}

export interface PageResponse<T> {
  items: T[];
  total: number;
  page?: number;
  page_size?: number;
}

export interface JobInput {
  title: string;
  department: string;
  location: string;
  employment_type: string;
  description: string;
  requirements: string;
  salary_min: number | null;
  salary_max: number | null;
  expires_at: string | null;
}

async function adminRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getCandidateToken();

  if (!token) {
    throw new Error("Please sign in with an administrator account.");
  }

  const headers = new Headers(options.headers);
  headers.set("Authorization", `Bearer ${token}`);

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return undefined as T;
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error(
        "Access denied. Check that you are signed in with an administrator account.",
      );
    }

    throw new Error(
      typeof payload?.error?.message === "string"
        ? payload.error.message
        : `Request failed (HTTP ${response.status}).`,
    );
  }

  if (payload?.success !== true) {
    throw new Error("The server returned an invalid response.");
  }

  return payload.data as T;
}

export function adminLogout() {
  clearCandidateToken();
}

export function getDashboardSummary() {
  return adminRequest<AdminDashboardSummary>("/admin/dashboard/summary");
}

export function listAdminJobs() {
  return adminRequest<AdminJob[]>("/admin/jobs");
}

export function createAdminJob(input: JobInput) {
  return adminRequest<AdminJob>("/admin/jobs", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateAdminJob(id: string, input: Partial<JobInput>) {
  return adminRequest<AdminJob>(`/admin/jobs/${encodeURIComponent(id)}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function publishAdminJob(id: string) {
  return adminRequest<AdminJob>(
    `/admin/jobs/${encodeURIComponent(id)}/publish`,
    { method: "POST" },
  );
}

export function closeAdminJob(id: string) {
  return adminRequest<AdminJob>(
    `/admin/jobs/${encodeURIComponent(id)}/close`,
    { method: "POST" },
  );
}

export function listAdminApplications(params: {
  page?: number;
  page_size?: number;
  status?: string;
  job_id?: string;
} = {}) {
  const query = new URLSearchParams();
  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.page_size ?? 20));

  if (params.status) query.set("status", params.status);
  if (params.job_id) query.set("job_id", params.job_id);

  return adminRequest<PageResponse<AdminApplication>>(
    `/admin/applications?${query.toString()}`,
  );
}

export function getAdminApplication(id: string) {
  return adminRequest<AdminApplication>(
    `/admin/applications/${encodeURIComponent(id)}`,
  );
}

export function updateApplicationStatus(
  id: string,
  status: AdminApplication["status"],
  note: string,
) {
  return adminRequest<AdminApplication>(
    `/admin/applications/${encodeURIComponent(id)}/status`,
    {
      method: "PATCH",
      body: JSON.stringify({ status, note }),
    },
  );
}

export async function downloadApplicationCV(id: string) {
  const token = getCandidateToken();

  if (!token) throw new Error("Please sign in again.");

  const response = await fetch(
    `${API_BASE}/admin/applications/${encodeURIComponent(id)}/cv`,
    { headers: { Authorization: `Bearer ${token}` } },
  );

  if (!response.ok) {
    throw new Error(`CV download failed (HTTP ${response.status}).`);
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = objectUrl;
  anchor.download = `candidate-${id}-cv.pdf`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
