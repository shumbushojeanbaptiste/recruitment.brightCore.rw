
import { useEffect, useState, type FormEvent } from "react";
import {
  ArrowLeft,
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  Clock3,
  MapPin,
  Search,
  CheckCircle2,
  FileUp,
  LogIn,
  LogOut,
} from "lucide-react";
import {
  BrowserRouter,
  Link,
  Navigate,
  Route,
  Routes,
  useLocation,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";

import { getJob } from "./api";
import type { Job } from "./types";
import "./App.css";
import {
  CandidatePortal,
  CandidateDashboardPage,
} from "./CandidatePortal";
import { AdminPortal } from "./AdminPortal";
import {
  clearCandidateToken,
  fetchAuthenticatedUser,
  getCandidateToken,
} from "./candidateApi";

function formatEmploymentType(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatDate(value: string | null) {
  if (!value) return null;

  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? null
    : date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
}

function salaryRange(job: Job) {
  if (job.salary_min == null && job.salary_max == null) return null;

  const format = (amount: number) =>
    new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 }).format(amount);

  if (job.salary_min != null && job.salary_max != null) {
    return `${format(job.salary_min)} – ${format(job.salary_max)}`;
  }

  return job.salary_min != null
    ? `From ${format(job.salary_min)}`
    : `Up to ${format(job.salary_max!)}`;
}

function Header() {
  const navigate = useNavigate();
  const [isAuthenticated, setIsAuthenticated] = useState(
    () => getCandidateToken() !== null,
  );

  useEffect(() => {
    function updateAuthentication() {
      setIsAuthenticated(getCandidateToken() !== null);
    }

    window.addEventListener("brightcore-auth-change", updateAuthentication);
    return () => {
      window.removeEventListener("brightcore-auth-change", updateAuthentication);
    };
  }, []);

  function signOut() {
    clearCandidateToken();
    navigate("/", { replace: true });
  }

  return (
    <header className="site-header">
      <Link to="/" className="brand" aria-label="BrightCore home">
        <span className="brand-mark">B</span>
        <span>BrightCore<span className="brand-light"> Careers</span></span>
      </Link>

      {!isAuthenticated ? (
        <>
          <nav className="main-nav" aria-label="Main navigation">
            <Link to="/">Find jobs</Link>
            <a href="/#about">About us</a>
            <a href="/#contact">Contact us</a>
          </nav>
          <Link className="header-sign-in" to="/login">
            <LogIn size={16} />
            <span>Sign in</span>
          </Link>
        </>
      ) : (
        <button className="header-sign-in" type="button" onClick={signOut}>
          <LogOut size={16} />
          <span>Sign out</span>
        </button>
      )}
    </header>
  );
}

function JobCard({ job }: { job: Job }) {
  return (
    <article className="job-card">
      <div className="job-card-top">
        <div className="company-mark"><Building2 size={22} /></div>
        <span className="job-type">{formatEmploymentType(job.employment_type)}</span>
      </div>

      <h2>{job.title}</h2>
      <p className="department">{job.department}</p>

      <div className="job-meta">
        <span><MapPin size={15} /> {job.location}</span>
        {formatDate(job.published_at) && (
          <span><Clock3 size={15} /> Posted {formatDate(job.published_at)}</span>
        )}
      </div>

      <p className="job-description">
        {job.description.length > 160
          ? `${job.description.slice(0, 160)}…`
          : job.description}
      </p>

      <div className="job-card-bottom">
        <span className="salary">{salaryRange(job) ?? "Salary not specified"}</span>
        <Link to={`/jobs/${job.id}`} className="text-link">
          View details <ArrowRight size={16} />
        </Link>
      </div>
    </article>
  );
}

function JobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get("q") ?? "");
  const [location, setLocation] = useState(searchParams.get("location") ?? "");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);

  const page = Math.max(1, Number(searchParams.get("page") ?? 1) || 1);
  const pageSize = 10;

  useEffect(() => {
    const controller = new AbortController();

    async function loadJobs() {
      setLoading(true);
      setError("");

      try {
        const query = new URLSearchParams();
        query.set("page", String(page));
        query.set("page_size", String(pageSize));

        const q = searchParams.get("q");
        const loc = searchParams.get("location");

        if (q) query.set("q", q);
        if (loc) query.set("location", loc);

        const response = await fetch(`/api/v1/jobs?${query.toString()}`, {
          signal: controller.signal,
        });
        const payload = await response.json().catch(() => null);

        if (!response.ok) {
          throw new Error(
            payload?.error?.message ??
              `Could not load jobs (HTTP ${response.status}).`,
          );
        }

        if (payload?.success !== true) {
          throw new Error("The server returned an invalid response.");
        }
        const data = payload.data;
        setJobs(data.items ?? []);
        setTotal(data.total ?? data.items?.length ?? 0);
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          setError(err.message || "Something went wrong.");
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    void loadJobs();
    return () => controller.abort();
  }, [searchParams, page]);

  function applySearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const next = new URLSearchParams();
    if (search.trim()) next.set("q", search.trim());
    if (location.trim()) next.set("location", location.trim());

    setSearchParams(next);
  }

  function changePage(nextPage: number) {
    const next = new URLSearchParams(searchParams);
    next.set("page", String(nextPage));
    setSearchParams(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  const pageCount = Math.max(1, Math.ceil(total / pageSize));

  return (
    <>
      <section className="hero">
        <div className="hero-content">
          <span className="eyebrow"><BriefcaseBusiness size={15} /> YOUR NEXT CHAPTER STARTS HERE</span>
          <h1>Find work that<br /><span>moves you forward.</span></h1>
          <p>Discover meaningful opportunities and build your future with BrightCore.</p>

          <form className="search-panel" onSubmit={applySearch}>
            <label className="search-field">
              <Search size={19} />
              <span className="sr-only">Job title or keyword</span>
              <input
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                placeholder="Job title or keyword"
              />
            </label>

            <label className="search-field">
              <MapPin size={19} />
              <span className="sr-only">Location</span>
              <input
                value={location}
                onChange={(event) => setLocation(event.target.value)}
                placeholder="City or location"
              />
            </label>

            <button className="primary-button search-button" type="submit">
              Search jobs
            </button>
          </form>
        </div>
        <div className="hero-decoration" aria-hidden="true">
          <div className="decoration-ring ring-one" />
          <div className="decoration-ring ring-two" />
          <div className="decoration-dot" />
        </div>
      </section>

      <main className="content-section" id="jobs">
        <div className="section-heading">
          <div>
            <span className="eyebrow">OPPORTUNITIES</span>
            <h2>Explore open positions</h2>
            <p>Find a role where your skills can make a difference.</p>
          </div>
          {!loading && !error && (
            <span className="result-count">{total} {total === 1 ? "position" : "positions"}</span>
          )}
        </div>

        {loading && <div className="state-panel">Loading available positions…</div>}

        {!loading && error && (
          <div className="state-panel error-panel">
            <h3>We couldn't load the jobs</h3>
            <p>{error}</p>
            <button className="secondary-button" onClick={() => setSearchParams(new URLSearchParams(searchParams))}>
              Try again
            </button>
          </div>
        )}

        {!loading && !error && jobs.length === 0 && (
          <div className="state-panel">
            <h3>No positions found</h3>
            <p>Try another keyword or location, or check back later.</p>
          </div>
        )}

        {!loading && !error && jobs.length > 0 && (
          <div className="jobs-grid">
            {jobs.map((job) => <JobCard key={job.id} job={job} />)}
          </div>
        )}

        {!loading && !error && pageCount > 1 && (
          <div className="pagination">
            <button
              className="secondary-button"
              disabled={page <= 1}
              onClick={() => changePage(page - 1)}
            >
              <ArrowLeft size={16} /> Previous
            </button>
            <span>Page {page} of {pageCount}</span>
            <button
              className="secondary-button"
              disabled={page >= pageCount}
              onClick={() => changePage(page + 1)}
            >
              Next <ArrowRight size={16} />
            </button>
          </div>
        )}
      </main>

      <section className="about-section" id="about">
        <div className="about-icon"><Building2 size={26} /></div>
        <div className="about-content">
          <span className="eyebrow">ABOUT BRIGHTCORE CAREERS</span>
          <h2>Bringing people and opportunities together.</h2>
          <p>
            BrightCore Careers helps candidates discover open positions and
            submit applications in one place. Find a role that fits your skills,
            apply online, and follow your application progress through your
            candidate portal.
          </p>
          <Link className="text-link" to="#jobs">
            Explore open positions <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <section className="contact-section" id="contact">
        <div className="contact-heading">
          <span className="eyebrow">CONTACT</span>
          <h2>How can we help?</h2>
          <p>Choose the option that best matches what you need.</p>
        </div>
        <div className="contact-options">
          <article className="contact-card">
            <div className="contact-card-icon"><BriefcaseBusiness size={21} /></div>
            <h3>Questions about an application?</h3>
            <p>
              Sign in to check the latest status and any updates from the
              recruitment team.
            </p>
            <Link className="text-link" to="/login">
              Open candidate portal <ArrowRight size={16} />
            </Link>
          </article>
          <article className="contact-card">
            <div className="contact-card-icon"><Search size={21} /></div>
            <h3>Looking for your next role?</h3>
            <p>
              Browse current openings and open a position to review its details
              and application requirements.
            </p>
            <Link className="text-link" to="#jobs">
              Browse open positions <ArrowRight size={16} />
            </Link>
          </article>
        </div>
      </section>
    </>
  );
}


function ApplicationForm({ jobId }: { jobId: string }) {
  const [cvFile, setCvFile] = useState<File | null>(null);
  const [cvError, setCvError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function selectCV(file: File | undefined) {
    setCvError("");
    setError("");

    if (!file) {
      setCvFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setCvFile(null);
      setCvError("Please select a PDF file.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setCvFile(null);
      setCvError("Your CV must not exceed 5 MB.");
      return;
    }

    if (file.size === 0) {
      setCvFile(null);
      setCvError("The selected file is empty.");
      return;
    }

    setCvFile(file);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setCvError("");

    if (!cvFile) {
      setCvError("Please attach your CV as a PDF file.");
      return;
    }

    const form = event.currentTarget;
    const formData = new FormData(form);

    // The field names must match the FastAPI multipart endpoint.
    formData.set("cv", cvFile);

    setSubmitting(true);

    try {
      const response = await fetch(
        `/api/v1/jobs/${encodeURIComponent(jobId)}/applications`,
        {
          method: "POST",
          body: formData,
        },
      );

      const payload = await response.json().catch(() => null);

      if (!response.ok) {
        const error = payload?.error;
        const details = error?.details;

        if (Array.isArray(details)) {
          throw new Error(
            details.map((item: { message?: string }) => item.message ?? "Invalid input")
              .join("; "),
          );
        }

        if (typeof error?.message === "string") {
          throw new Error(error.message);
        }

        if (response.status === 429) {
          throw new Error("Too many attempts. Please wait before trying again.");
        }

        throw new Error(
          `Application submission failed (HTTP ${response.status}).`,
        );
      }

      if (payload?.success !== true) {
        throw new Error("The server returned an invalid response.");
      }

      setSubmitted(true);
      setCvFile(null);
      form.reset();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "We couldn't submit your application. Please try again.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <section className="application-success" aria-live="polite">
        <CheckCircle2 size={38} />
        <h2>Application submitted</h2>
        <p>
          Thank you for applying. Your application has been received.
          Please keep your contact details available in case the recruitment
          team needs to reach you.
        </p>
        <button
          className="secondary-button"
          onClick={() => setSubmitted(false)}
        >
          Back to application form
        </button>
      </section>
    );
  }

  return (
    <section className="application-section" id="apply">
      <div className="application-heading">
        <span className="eyebrow">TAKE THE NEXT STEP</span>
        <h2>Apply for this position</h2>
        <p>Complete the form below and attach your CV in PDF format.</p>
      </div>

      <form className="application-form" onSubmit={handleSubmit}>
        <div className="form-field">
          <label htmlFor="app-full-name">Full name *</label>
          <input
            id="app-full-name"
            name="full_name"
            type="text"
            placeholder="Enter your full name"
            autoComplete="name"
            minLength={2}
            maxLength={150}
            required
            disabled={submitting}
          />
        </div>

        <div className="form-row">
          <div className="form-field">
            <label htmlFor="app-email">Email address *</label>
            <input
              id="app-email"
              name="email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              maxLength={254}
              required
              disabled={submitting}
            />
          </div>

          <div className="form-field">
            <label htmlFor="app-phone">Phone number *</label>
            <input
              id="app-phone"
              name="phone"
              type="tel"
              placeholder="+250 7XX XXX XXX"
              autoComplete="tel"
              maxLength={30}
              required
              disabled={submitting}
            />
          </div>
        </div>

        <div className="form-field">
          <label htmlFor="app-cover-note">Cover note</label>
          <textarea
            id="app-cover-note"
            name="cover_note"
            rows={5}
            maxLength={5000}
            placeholder="Tell us briefly why you are interested in this role..."
            disabled={submitting}
          />
          <span className="field-hint">Optional · Up to 5,000 characters</span>
        </div>

        <div className="form-field">
          <label htmlFor="app-cv">CV / Resume (PDF) *</label>
          <label className="file-drop" htmlFor="app-cv">
            <FileUp size={28} />
            <span className="file-drop-title">
              {cvFile ? cvFile.name : "Choose your CV"}
            </span>
            <span className="field-hint">
              PDF format only · Maximum 5 MB
            </span>
          </label>
          <input
            id="app-cv"
            className="file-input"
            type="file"
            accept=".pdf,application/pdf"
            required
            disabled={submitting}
            onChange={(event) => selectCV(event.target.files?.[0])}
          />
          {cvError && (
            <p className="form-error" role="alert">{cvError}</p>
          )}
        </div>

        {error && (
          <div className="form-error-banner" role="alert">
            <strong>Unable to submit application</strong>
            <p>{error}</p>
          </div>
        )}

        <p className="privacy-note">
          Your CV and contact information will be handled by the recruitment
          system and made available to authorized recruitment staff.
        </p>

        <button
          className="primary-button apply-button"
          type="submit"
          disabled={submitting}
        >
          {submitting ? "Submitting application…" : "Submit application"}
          {!submitting && <CheckCircle2 size={17} />}
        </button>
      </form>
    </section>
  );
}


function JobDetailsPage() {
  const { jobId } = useParams();
  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [isApplying, setIsApplying] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadJob() {
      setLoading(true);
      setError("");

      try {
        if (!jobId) throw new Error("Job ID is missing.");
        const result = await getJob(jobId);
        if (active) setJob(result);
      } catch (err) {
        if (active) {
          setError(err instanceof Error ? err.message : "Could not load this job.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadJob();
    return () => { active = false; };
  }, [jobId]);

  if (loading) {
    return <main className="detail-container"><div className="state-panel">Loading job details…</div></main>;
  }

  if (error || !job) {
    return (
      <main className="detail-container">
        <div className="state-panel error-panel">
          <h2>Job unavailable</h2>
          <p>{error || "This position could not be found."}</p>
          <Link className="text-link" to="/"> <ArrowLeft size={16} /> Back to jobs</Link>
        </div>
      </main>
    );
  }

  if (isApplying) {
    return (
      <main className="detail-container">
        <button
          className="back-link form-back-link"
          type="button"
          onClick={() => setIsApplying(false)}
        >
          <ArrowLeft size={16} /> Back to job details
        </button>
        <ApplicationForm jobId={job.id} />
      </main>
    );
  }

  return (
    <main className="detail-container">
      <Link className="back-link" to="/"><ArrowLeft size={16} /> All positions</Link>

      <article className="detail-card">
        <div className="detail-top">
          <div className="company-mark large"><Building2 size={27} /></div>
          <span className="job-type">{formatEmploymentType(job.employment_type)}</span>
        </div>

        <h1>{job.title}</h1>
        <p className="department">{job.department}</p>

        <div className="job-meta detail-meta">
          <span><MapPin size={16} /> {job.location}</span>
          {formatDate(job.published_at) && <span><Clock3 size={16} /> Posted {formatDate(job.published_at)}</span>}
        </div>

        <div className="detail-salary">{salaryRange(job) ?? "Salary not specified"}</div>

        <div className="detail-divider" />
        <section className="description-block">
          <h2>About the role</h2>
          <p className="long-text">{job.description}</p>
        </section>

        <section className="description-block">
          <h2>Requirements</h2>
          <p className="long-text">{job.requirements || "Please contact the recruitment team for further information."}</p>
        </section>

        {formatDate(job.expires_at) && (
          <p className="expiry-note">Application deadline: {formatDate(job.expires_at)}</p>
        )}

        <button
          className="primary-button apply-button"
          type="button"
          onClick={() => {
            setIsApplying(true);
            window.scrollTo({ top: 0, behavior: "smooth" });
          }}
        >
          Apply for this position <ArrowRight size={17} />
        </button>
      </article>
    </main>
  );
}

function Footer() {
  return (
    <footer className="site-footer" id="footer">
      <Link to="/" className="brand footer-brand">
        <span className="brand-mark">B</span>
        <span>BrightCore<span className="brand-light"> Careers</span></span>
      </Link>
      <span>Discover your next opportunity.</span>
      <span>© {new Date().getFullYear()} BrightCore</span>
    </footer>
  );
}

function AdminRoute() {
  const location = useLocation();
  const [access, setAccess] = useState<"checking" | "granted" | "denied">(
    "checking",
  );

  useEffect(() => {
    let active = true;

    async function verifyAdmin() {
      if (!getCandidateToken()) {
        setAccess("denied");
        return;
      }

      try {
        const user = await fetchAuthenticatedUser();
        if (active) {
          setAccess(user.is_active && user.role === "admin" ? "granted" : "denied");
        }
      } catch {
        clearCandidateToken();
        if (active) setAccess("denied");
      }
    }

    setAccess("checking");
    void verifyAdmin();

    return () => {
      active = false;
    };
  }, [location.pathname]);

  if (access === "checking") {
    return (
      <main className="detail-container">
        <div className="state-panel" role="status">Verifying administrator access…</div>
      </main>
    );
  }

  if (access === "denied") {
    return <Navigate to="/" replace />;
  }

  return <AdminPortal />;
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header />
        <Routes>
          <Route path="/" element={<JobsPage />} />
          <Route path="/jobs/:jobId" element={<JobDetailsPage />} />
          <Route path="/login" element={<CandidatePortal />} />
          <Route path="/candidate/login" element={<Navigate to="/login" replace />} />
          <Route path="/candidate/dashboard" element={<CandidateDashboardPage />} />
          <Route path="/admin/login" element={<Navigate to="/login" replace />} />
          <Route path="/admin" element={<AdminRoute />} />
          <Route path="*" element={
            <main className="detail-container">
              <div className="state-panel">
                <h2>Page not found</h2>
                <Link to="/" className="text-link">Return to open positions</Link>
              </div>
            </main>
          } />
        </Routes>
        <Footer />
      </div>
    </BrowserRouter>
  );
}
