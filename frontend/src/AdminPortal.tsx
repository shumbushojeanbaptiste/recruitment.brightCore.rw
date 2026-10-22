
import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";
import {
  Activity,
  BriefcaseBusiness,
  CheckCircle2,
  ClipboardList,
  Download,
  LayoutDashboard,
  LogOut,
  Plus,
  RefreshCw,
  Search,
  Users,
  X,
} from "lucide-react";
import {
  adminLogout,
  closeAdminJob,
  createAdminJob,
  downloadApplicationCV,
  getDashboardSummary,
  listAdminApplications,
  listAdminJobs,
  publishAdminJob,
  updateAdminJob,
  updateApplicationStatus,
  type AdminApplication,
  type AdminDashboardSummary,
  type AdminJob,
  type JobInput,
} from "./adminApi";
import "./AdminPortal.css";

type Section = "overview" | "jobs" | "applications";

const emptyJob: JobInput = {
  title: "",
  department: "",
  location: "",
  employment_type: "full_time",
  description: "",
  requirements: "",
  salary_min: null,
  salary_max: null,
  expires_at: null,
};

function errorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function MetricCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: number;
  icon: "jobs" | "applications" | "pending" | "accepted" | "rejected";
}) {
  const Icon = {
    jobs: BriefcaseBusiness,
    applications: Users,
    pending: ClipboardList,
    accepted: CheckCircle2,
    rejected: X,
  }[icon];

  return (
    <article className="metric-card">
      <div className={`metric-icon metric-${icon}`}><Icon size={21} /></div>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}

function JobEditor({
  initial,
  onClose,
  onSaved,
}: {
  initial: AdminJob | null;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [form, setForm] = useState<JobInput>(
    initial
      ? {
          title: initial.title,
          department: initial.department,
          location: initial.location,
          employment_type: initial.employment_type,
          description: initial.description,
          requirements: initial.requirements,
          salary_min: initial.salary_min,
          salary_max: initial.salary_max,
          expires_at: initial.expires_at,
        }
      : emptyJob,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function setField<K extends keyof JobInput>(key: K, value: JobInput[K]) {
    setForm((previous) => ({ ...previous, [key]: value }));
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (initial) {
        await updateAdminJob(initial.id, form);
      } else {
        await createAdminJob(form);
      }

      await onSaved();
      onClose();
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="admin-modal-backdrop" role="presentation">
      <section
        className="admin-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="job-editor-title"
      >
        <div className="admin-modal-header">
          <h2 id="job-editor-title">{initial ? "Edit job" : "Create a job"}</h2>
          <button className="icon-button" onClick={onClose} aria-label="Close form">
            <X size={20} />
          </button>
        </div>

        {error && <div className="admin-error" role="alert">{error}</div>}

        <form className="admin-form admin-job-form" onSubmit={submit}>
          <label>
            Job title *
            <input
              value={form.title}
              onChange={(event) => setField("title", event.target.value)}
              required
              maxLength={200}
              disabled={busy}
            />
          </label>

          <div className="admin-form-row">
            <label>
              Department *
              <input
                value={form.department}
                onChange={(event) => setField("department", event.target.value)}
                required
                disabled={busy}
              />
            </label>
            <label>
              Location *
              <input
                value={form.location}
                onChange={(event) => setField("location", event.target.value)}
                required
                disabled={busy}
              />
            </label>
          </div>

          <label>
            Employment type *
            <select
              value={form.employment_type}
              onChange={(event) => setField("employment_type", event.target.value)}
              disabled={busy}
            >
              <option value="full_time">Full-time</option>
              <option value="part_time">Part-time</option>
              <option value="contract">Contract</option>
              <option value="internship">Internship</option>
              <option value="temporary">Temporary</option>
            </select>
          </label>

          <label>
            Job description *
            <textarea
              rows={5}
              value={form.description}
              onChange={(event) => setField("description", event.target.value)}
              required
              disabled={busy}
            />
          </label>

          <label>
            Requirements *
            <textarea
              rows={4}
              value={form.requirements}
              onChange={(event) => setField("requirements", event.target.value)}
              required
              disabled={busy}
            />
          </label>

          <div className="admin-form-row">
            <label>
              Minimum salary
              <input
                type="number"
                min="0"
                value={form.salary_min ?? ""}
                onChange={(event) => setField(
                  "salary_min",
                  event.target.value === "" ? null : Number(event.target.value),
                )}
                disabled={busy}
              />
            </label>
            <label>
              Maximum salary
              <input
                type="number"
                min="0"
                value={form.salary_max ?? ""}
                onChange={(event) => setField(
                  "salary_max",
                  event.target.value === "" ? null : Number(event.target.value),
                )}
                disabled={busy}
              />
            </label>
          </div>

          <label>
            Application deadline
            <input
              type="datetime-local"
              value={form.expires_at ? form.expires_at.slice(0, 16) : ""}
              onChange={(event) => setField(
                "expires_at",
                event.target.value ? new Date(event.target.value).toISOString() : null,
              )}
              disabled={busy}
            />
          </label>

          <div className="admin-modal-actions">
            <button type="button" className="secondary-button" onClick={onClose}>
              Cancel
            </button>
            <button className="primary-button" disabled={busy}>
              {busy ? "Saving…" : initial ? "Save changes" : "Create draft"}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}

function AdminDashboard() {
  const [section, setSection] = useState<Section>("overview");
  const [summary, setSummary] = useState<AdminDashboardSummary | null>(null);
  const [jobs, setJobs] = useState<AdminJob[]>([]);
  const [applications, setApplications] = useState<AdminApplication[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [jobFilter, setJobFilter] = useState("");
  const [editor, setEditor] = useState<AdminJob | null | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState("");

  async function loadOverview() {
    setLoading(true);
    setError("");

    try {
      const result = await getDashboardSummary();
      setSummary(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadJobs() {
    setLoading(true);
    setError("");

    try {
      const result = await listAdminJobs();
      setJobs(result);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadApplications() {
    setLoading(true);
    setError("");

    try {
      const result = await listAdminApplications({
        page: 1,
        page_size: 50,
        status: statusFilter || undefined,
        job_id: jobFilter || undefined,
      });
      setApplications(result.items ?? []);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function refreshCurrentSection() {
    setNotice("");

    if (section === "overview") await loadOverview();
    if (section === "jobs") await loadJobs();
    if (section === "applications") await loadApplications();
  }

  useEffect(() => {
    void loadOverview();
  }, []);

//   useEffect(() => {
//     if (section === "jobs") void loadJobs();
//     if (section === "applications") void loadApplications();
//   }, [section, statusFilter, jobFilter]);

  useEffect(() => {
  if (section === "jobs") {
    void loadJobs();
  }

  if (section === "applications") {
    void loadJobs();
    void loadApplications();
  }
}, [section, statusFilter, jobFilter]);

  async function performJobAction(
    job: AdminJob,
    action: "publish" | "close",
  ) {
    setBusyId(job.id);
    setError("");
    setNotice("");

    try {
      if (action === "publish") {
        await publishAdminJob(job.id);
        setNotice("Job published successfully.");
      } else {
        await closeAdminJob(job.id);
        setNotice("Job closed successfully.");
      }

      await Promise.all([loadJobs(), loadOverview()]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId("");
    }
  }

  async function changeStatus(
    application: AdminApplication,
    status: AdminApplication["status"],
  ) {
    const note = window.prompt(
      `Optional note for this ${status.replaceAll("_", " ")} decision:`,
      application.status_note ?? "",
    );

    if (note === null) return;

    setBusyId(application.id);
    setError("");
    setNotice("");

    try {
      await updateApplicationStatus(application.id, status, note);
      setNotice("Application status updated.");
      await Promise.all([loadApplications(), loadOverview()]);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId("");
    }
  }

  async function downloadCV(application: AdminApplication) {
    setBusyId(application.id);
    setError("");

    try {
      await downloadApplicationCV(application.id);
      setNotice("CV download requested.");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusyId("");
    }
  }

  function logout() {
    adminLogout();
    window.location.assign("/login");
  }

  const navItems: { key: Section; label: string; icon: typeof LayoutDashboard }[] = [
    { key: "overview", label: "Overview", icon: LayoutDashboard },
    { key: "jobs", label: "Jobs", icon: BriefcaseBusiness },
    { key: "applications", label: "Applications", icon: Users },
  ];

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <Link to="/" className="admin-brand">
          <span className="brand-mark">B</span>
          <span>BrightCore<small>RECRUITMENT</small></span>
        </Link>

        <div className="admin-nav-label">WORKSPACE</div>
        <nav className="admin-nav">
          {navItems.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              className={section === key ? "admin-nav-item active" : "admin-nav-item"}
              onClick={() => {
                setSection(key);
                setError("");
                setNotice("");
              }}
            >
              <Icon size={18} /> {label}
            </button>
          ))}
        </nav>

        <div className="admin-sidebar-bottom">
          <Link to="/">View public site ↗</Link>
          <button className="admin-logout" onClick={logout}>
            <LogOut size={17} /> Sign out
          </button>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-topbar">
          <div>
            <span className="admin-topbar-kicker">ADMINISTRATION</span>
            <h1>
              {section === "overview"
                ? "Recruitment overview"
                : section === "jobs"
                  ? "Job management"
                  : "Applicant management"}
            </h1>
          </div>
          <button className="secondary-button" onClick={() => void refreshCurrentSection()}>
            <RefreshCw size={15} /> Refresh
          </button>
        </header>

        {error && <div className="admin-error" role="alert">{error}</div>}
        {notice && <div className="admin-notice" role="status">{notice}</div>}
        {loading && <div className="admin-loading">Loading records…</div>}

        {section === "overview" && summary && !loading && (
          <section className="admin-content">
            <div className="admin-welcome">
              <div>
                <span className="eyebrow">RECRUITMENT INSIGHTS</span>
                <h2>Your hiring activity at a glance</h2>
                <p>Review your current vacancies and candidate pipeline.</p>
              </div>
              <div className="admin-welcome-icon"><Activity size={32} /></div>
            </div>

            <div className="metrics-grid">
              <MetricCard label="Published jobs" value={summary.published_jobs} icon="jobs" />
              <MetricCard label="Total applications" value={summary.total_applications} icon="applications" />
              <MetricCard label="Pending reviews" value={summary.pending_reviews} icon="pending" />
              <MetricCard label="Accepted" value={summary.accepted} icon="accepted" />
              <MetricCard label="Rejected" value={summary.rejected} icon="rejected" />
            </div>

            <div className="admin-quick-actions">
              <div>
                <h2>Quick actions</h2>
                <p>Manage the next step in your recruitment process.</p>
              </div>
              <button
                className="primary-button"
                onClick={() => {
                  setSection("jobs");
                  setEditor(null);
                }}
              >
                <Plus size={17} /> Create job
              </button>
              <button
                className="secondary-button"
                onClick={() => setSection("applications")}
              >
                <Users size={16} /> Review applicants
              </button>
            </div>
          </section>
        )}

        {section === "jobs" && (
          <section className="admin-content">
            <div className="admin-section-heading">
              <div>
                <h2>All jobs</h2>
                <p>Create, edit, publish, or close recruitment opportunities.</p>
              </div>
              <button className="primary-button" onClick={() => setEditor(null)}>
                <Plus size={17} /> Create job
              </button>
            </div>

            {!loading && jobs.length === 0 ? (
              <div className="state-panel">
                <BriefcaseBusiness size={28} />
                <h2>No jobs found</h2>
                <p>Create your first recruitment vacancy.</p>
              </div>
            ) : (
              <div className="admin-table-wrap">
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Position</th>
                      <th>Location</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {jobs.map((job) => (
                      <tr key={job.id}>
                        <td>
                          <strong>{job.title}</strong>
                          <span>{job.department}</span>
                        </td>
                        <td>{job.location}</td>
                        <td><span className={`admin-status status-${job.status}`}>{job.status}</span></td>
                        <td>
                          <div className="admin-row-actions">
                            <button
                              className="table-action"
                              onClick={() => setEditor(job)}
                              disabled={job.status === "closed"}
                            >
                              Edit
                            </button>
                            {job.status === "draft" && (
                              <button
                                className="table-action"
                                disabled={busyId === job.id}
                                onClick={() => void performJobAction(job, "publish")}
                              >
                                Publish
                              </button>
                            )}
                            {job.status === "published" && (
                              <button
                                className="table-action danger"
                                disabled={busyId === job.id}
                                onClick={() => {
                                  if (window.confirm(`Close "${job.title}"?`)) {
                                    void performJobAction(job, "close");
                                  }
                                }}
                              >
                                Close
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        )}

        {section === "applications" && (
          <section className="admin-content">
            <div className="admin-section-heading">
              <div>
                <h2>Applications</h2>
                <p>Review candidate details and record recruitment decisions.</p>
              </div>
            </div>

            <div className="admin-filters">
              <label>
                <Search size={16} />
                <span className="sr-only">Filter by status</span>
                <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                  <option value="">All statuses</option>
                  <option value="submitted">Submitted</option>
                  <option value="under_review">Under review</option>
                  <option value="accepted">Accepted</option>
                  <option value="rejected">Rejected</option>
                </select>
              </label>

              <label>
                <span className="sr-only">Filter by job</span>
                <select value={jobFilter} onChange={(event) => setJobFilter(event.target.value)}>
                  <option value="">All jobs</option>
                  {jobs.map((job) => (
                    <option value={job.id} key={job.id}>{job.title}</option>
                  ))}
                </select>
              </label>
            </div>

            {!loading && applications.length === 0 ? (
              <div className="state-panel">
                <Users size={28} />
                <h2>No applications found</h2>
                <p>Try changing the filters or check again later.</p>
              </div>
            ) : (
              <div className="admin-applicant-list">
                {applications.map((application) => (
                  <ApplicantCard
                    key={application.id}
                    application={application}
                    busy={busyId === application.id}
                    onStatusChange={changeStatus}
                    onDownload={downloadCV}
                  />
                ))}
              </div>
            )}
          </section>
        )}
      </main>

      {editor !== undefined && (
        <JobEditor
          initial={editor}
          onClose={() => setEditor(undefined)}
          onSaved={async () => {
            setNotice(editor ? "Job updated successfully." : "Job created successfully.");
            await Promise.all([loadJobs(), loadOverview()]);
          }}
        />
      )}
    </div>
  );
}

function ApplicantCard({
  application,
  busy,
  onStatusChange,
  onDownload,
}: {
  application: AdminApplication;
  busy: boolean;
  onStatusChange: (
    application: AdminApplication,
    status: AdminApplication["status"],
  ) => Promise<void>;
  onDownload: (application: AdminApplication) => Promise<void>;
}) {
  return (
    <article className="admin-applicant-card">
      <div className="admin-applicant-heading">
        <div className="admin-applicant-avatar">
          {application.full_name.trim().charAt(0).toUpperCase() || "C"}
        </div>
        <div className="admin-applicant-identity">
          <h3>{application.full_name}</h3>
          <p>{application.email} · {application.phone}</p>
          <span>Submitted {new Date(application.created_at).toLocaleDateString()}</span>
        </div>
        <span className={`admin-status status-${application.status}`}>
          {application.status.replaceAll("_", " ")}
        </span>
      </div>

      {application.cover_note && (
        <div className="admin-cover-note">
          <strong>Cover note</strong>
          <p>{application.cover_note}</p>
        </div>
      )}

      {application.status_note && (
        <p className="admin-existing-note">
          Latest note: {application.status_note}
        </p>
      )}

      <div className="admin-applicant-actions">
        <button
          className="secondary-button"
          disabled={busy}
          onClick={() => void onDownload(application)}
        >
          <Download size={15} /> Download CV
        </button>

        <label className="admin-status-select">
          <span>Update status</span>
          <select
            value={application.status}
            disabled={busy || application.status === "accepted" || application.status === "rejected"}
            onChange={(event) => {
              const status = event.target.value as AdminApplication["status"];
              void onStatusChange(application, status);
            }}
          >
            <option value="submitted">Submitted</option>
            <option value="under_review">Under review</option>
            <option value="accepted">Accepted</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>
      </div>
    </article>
  );
}

export function AdminPortal() {
  return <AdminDashboard />;
}
