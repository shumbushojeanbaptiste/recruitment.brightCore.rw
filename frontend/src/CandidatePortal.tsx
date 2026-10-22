
import { useEffect, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BriefcaseBusiness,
  CircleUserRound,
  RefreshCw,
} from "lucide-react";
import {
  fetchCandidateApplications,
  getCandidateToken,
  loginCandidate,
  registerCandidate,
  type CandidateApplication,
} from "./candidateApi";
import "./CandidatePortal.css";

function messageOf(error: unknown) {
  return error instanceof Error ? error.message : "Something went wrong.";
}

function CandidateAuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setNotice("");

    try {
      if (mode === "register") {
        await registerCandidate({
          full_name: fullName.trim(),
          email: email.trim(),
          password,
        });

        setMode("login");
        setNotice("Account created. Sign in to view your candidate portal.");
        setPassword("");
        return;
      }

      const user = await loginCandidate({
        email: email.trim(),
        password,
      });

      navigate(
        user.role === "admin" ? "/admin" : "/candidate/dashboard",
        { replace: true },
      );
    } catch (err) {
      setError(messageOf(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="candidate-auth-page">
      <section className="candidate-auth-card">
        <div className="candidate-auth-icon"><CircleUserRound size={29} /></div>
        <span className="eyebrow">BRIGHTCORE ACCOUNT</span>
        <h1>{mode === "login" ? "Welcome back" : "Create your account"}</h1>
        <p className="candidate-muted">
          {mode === "login"
            ? "Sign in to access your BrightCore portal."
            : "Create an account to access your candidate portal."}
        </p>

        {notice && <div className="candidate-notice">{notice}</div>}
        {error && <div className="candidate-error" role="alert">{error}</div>}

        <form onSubmit={submit} className="candidate-form">
          {mode === "register" && (
            <label>
              Full name
              <input
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                minLength={2}
                maxLength={150}
                autoComplete="name"
                required
                disabled={busy}
              />
            </label>
          )}

          <label>
            Email address
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              maxLength={254}
              disabled={busy}
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              minLength={12}
              maxLength={128}
              required
              disabled={busy}
            />
            {mode === "register" && (
              <span className="candidate-hint">Use at least 12 characters.</span>
            )}
          </label>

          <button className="primary-button candidate-submit" disabled={busy}>
            {busy
              ? "Please wait…"
              : mode === "login"
                ? "Sign in"
                : "Create account"}
            <ArrowRight size={17} />
          </button>
        </form>

        <p className="candidate-switch">
          {mode === "login" ? "New to BrightCore?" : "Already registered?"}{" "}
          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
              setNotice("");
            }}
          >
            {mode === "login" ? "Create an account" : "Sign in"}
          </button>
        </p>

        <Link to="/" className="candidate-back">Browse open positions</Link>
      </section>
    </main>
  );
}

function statusLabel(status: CandidateApplication["status"]) {
  return status.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function CandidateDashboard() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState<CandidateApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadDashboard() {
    setLoading(true);
    setError("");

    try {
      const applicationsResult = await fetchCandidateApplications();
      setApplications(applicationsResult.items);
    } catch (err) {
      setError(messageOf(err));

      if (!getCandidateToken()) {
        navigate("/candidate/login", { replace: true });
      }
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  return (
    <main className="candidate-dashboard">
      <div className="candidate-dashboard-header">
        <div>
          <span className="eyebrow">YOUR CAREER SPACE</span>
          <h1>Candidate dashboard</h1>
          <p>Track your applications and stay informed about your progress.</p>
        </div>

      </div>

      {loading && <div className="state-panel">Loading your candidate portal…</div>}

      {!loading && error && (
        <div className="state-panel error-panel">
          <h2>We couldn't load your dashboard</h2>
          <p>{error}</p>
          <button className="secondary-button" onClick={() => void loadDashboard()}>
            <RefreshCw size={15} /> Try again
          </button>
        </div>
      )}

      {!loading && !error && (
        <>
          <section className="candidate-applications-section">
            <div className="candidate-section-heading">
              <div>
                <span className="eyebrow">APPLICATION HISTORY</span>
                <h2>Your applications</h2>
              </div>
              <span className="candidate-total">
                {applications.length} {applications.length === 1 ? "application" : "applications"}
              </span>
            </div>

            {applications.length === 0 ? (
              <div className="state-panel">
                <BriefcaseBusiness size={28} />
                <h2>No applications yet</h2>
                <p>Explore open positions and submit your first application.</p>
                <Link to="/" className="primary-button candidate-browse">
                  Browse jobs <ArrowRight size={16} />
                </Link>
              </div>
            ) : (
              <div className="candidate-application-list">
                {applications.map((application) => (
                  <article className="candidate-application-card" key={application.id}>
                    <div className="candidate-application-top">
                      <div className="candidate-application-icon">
                        <BriefcaseBusiness size={21} />
                      </div>
                      <span className={`application-status status-${application.status}`}>
                        {statusLabel(application.status)}
                      </span>
                    </div>

                    <h3>{application.job_title}</h3>
                    <p className="candidate-muted">
                      Submitted {new Date(application.created_at).toLocaleDateString()}
                    </p>
                    <p className="candidate-job-id">
                      Reference: {application.id}
                    </p>

                    {application.status_note && (
                      <div className="candidate-status-note">
                        <strong>Recruitment update</strong>
                        <p>{application.status_note}</p>
                      </div>
                    )}

                    <Link
                      className="text-link"
                      to={`/jobs/${application.job_id}`}
                    >
                      View job details <ArrowRight size={15} />
                    </Link>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </main>
  );
}

export function CandidatePortal() {
  return <CandidateAuthPage />;
}

export function CandidateDashboardPage() {
  return <CandidateDashboard />;
}
