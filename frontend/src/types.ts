
export type EmploymentType =
  | "full_time"
  | "part_time"
  | "contract"
  | "internship"
  | "temporary";

export interface Job {
  id: string;
  title: string;
  department: string;
  location: string;
  employment_type: EmploymentType;
  description: string;
  requirements: string;
  salary_min: number | null;
  salary_max: number | null;
  published_at: string | null;
  expires_at: string | null;
}

export interface JobListResponse {
  items: Job[];
  page: number;
  page_size: number;
  total: number;
}
