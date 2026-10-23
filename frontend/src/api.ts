
import type { Job, JobListResponse } from "./types";
import { apiErrorMessage } from "./apiErrors";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

async function request<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(
      apiErrorMessage(
        payload,
        response.status,
        response.status === 404
          ? "This job is no longer available."
          : `Request failed with status ${response.status}.`,
      ),
    );
  }

  if (payload?.success !== true) {
    throw new Error("The server returned an invalid response.");
  }

  return payload.data as T;
}

export async function getJobs(params: {
  page?: number;
  page_size?: number;
  q?: string;
  location?: string;
} = {}): Promise<JobListResponse> {
  const query = new URLSearchParams();

  query.set("page", String(params.page ?? 1));
  query.set("page_size", String(params.page_size ?? 10));

  if (params.q?.trim()) {
    query.set("q", params.q.trim());
  }

  if (params.location?.trim()) {
    query.set("location", params.location.trim());
  }

  return request<JobListResponse>(`/jobs?${query.toString()}`);
}

export async function getJob(jobId: string): Promise<Job> {
  return request<Job>(`/jobs/${encodeURIComponent(jobId)}`);
}
