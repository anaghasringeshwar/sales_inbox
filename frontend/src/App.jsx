import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

const SAMPLE_JSON = {
  candidate_id: "customer@company.com",
  emails: [
    {
      email_id: "email-001",
      thread_id: "thread-001",
      message_index: 0,
      from_name: "John Smith",
      from_email: "john@company.com",
      to: "sales@ourcompany.com",
      cc: [],
      subject: "Enterprise document management RFP",
      body: "Hello, we are evaluating document management solutions for our enterprise. Please send us your pricing, implementation timeline and proposal. Our expected deal value is around INR 2500000.",
      received_at: "2026-08-09T10:00:00",
      attachments: [],
      is_reply: false
    }
  ]
};

function App() {
  const [tasks, setTasks] = useState([]);
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(SAMPLE_JSON, null, 2)
  );

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  // ============================================================
  // LOAD TASKS
  // ============================================================

  const loadTasks = async () => {
    try {
      setError("");

      const response = await fetch(`${API_URL}/tasks/`);

      if (!response.ok) {
        throw new Error(`Could not load tasks (${response.status})`);
      }

      const data = await response.json();

      setTasks(data);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadTasks();
  }, []);

  // ============================================================
  // PROCESS EMAIL
  // ============================================================

  const processEmail = async () => {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      let parsed;

      try {
        parsed = JSON.parse(jsonInput);
      } catch {
        throw new Error("Invalid JSON. Please check the JSON format.");
      }

      const response = await fetch(`${API_URL}/ingest/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(parsed)
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail
            ? JSON.stringify(data.detail)
            : `Request failed (${response.status})`
        );
      }

      setMessage(
        `✓ Processed ${data.processed} email(s) — ${data.tasks_created} task(s) created.`
      );

      await loadTasks();

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ============================================================
  // STATS
  // ============================================================

  const highPriority = tasks.filter(
    (task) => task.priority === "high"
  ).length;

  const enterprise = tasks.filter(
    (task) => task.category === "enterprise_rfp"
  ).length;

  const finance = tasks.filter(
    (task) => task.category === "finance"
  ).length;

  // ============================================================
  // UI
  // ============================================================

  return (
    <div className="app">

      {/* ======================================================
          SIDEBAR
      ====================================================== */}

      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">S</div>

          <div>
            <h2>SalesInbox</h2>
            <span>AI Sales Operations</span>
          </div>
        </div>

        <nav>

          <div className="nav-item active">
            <span>▦</span>
            Dashboard
          </div>

          <div className="nav-item">
            <span>✓</span>
            Tasks
            <b>{tasks.length}</b>
          </div>

          <div className="nav-item">
            <span>✉</span>
            Email Inbox
          </div>

        </nav>

        <div className="sidebar-bottom">

          <div className="ai-status">
            <span className="status-dot"></span>

            <div>
              <strong>Gemini AI</strong>
              <small>Classification active</small>
            </div>
          </div>

          <div className="admin">
            <div className="avatar">A</div>

            <div>
              <strong>Sales Operations</strong>
              <small>Admin</small>
            </div>
          </div>

        </div>

      </aside>


      {/* ======================================================
          MAIN
      ====================================================== */}

      <main className="main">

        <header className="header">

          <div>
            <h1>Sales Dashboard</h1>
            <p>
              AI-powered inbox classification and task routing
            </p>
          </div>

          <div className="header-actions">

            <button
              className="refresh-btn"
              onClick={loadTasks}
            >
              ↻ Refresh
            </button>

          </div>

        </header>


        {/* ====================================================
            ALERTS
        ==================================================== */}

        {message && (
          <div className="success">
            {message}
          </div>
        )}

        {error && (
          <div className="error">
            {error}
          </div>
        )}


        {/* ====================================================
            STATS
        ==================================================== */}

        <section className="stats">

          <div className="stat-card">
            <div className="stat-icon green">✓</div>

            <div>
              <span>Total Tasks</span>
              <strong>{tasks.length}</strong>
              <small>All processed emails</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon red">!</div>

            <div>
              <span>High Priority</span>
              <strong>{highPriority}</strong>
              <small>Requires attention</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon purple">◆</div>

            <div>
              <span>Enterprise RFPs</span>
              <strong>{enterprise}</strong>
              <small>Enterprise opportunities</small>
            </div>
          </div>


          <div className="stat-card">
            <div className="stat-icon orange">₹</div>

            <div>
              <span>Finance</span>
              <strong>{finance}</strong>
              <small>Billing & payments</small>
            </div>
          </div>

        </section>


        {/* ====================================================
            GEMINI INGESTION
        ==================================================== */}

        <section className="ingestion-card">

          <div className="section-heading">

            <div>
              <div className="gemini-label">
                GEMINI AUTOMATION
              </div>

              <h2>
                Turn emails into actionable sales tasks.
              </h2>

              <p>
                Paste an inbound email JSON. Gemini determines
                intent, ownership, priority, deadline and deal value.
              </p>
            </div>

          </div>


          <div className="json-area">

            <div className="json-header">

              <strong>Inbound Email JSON</strong>

              <button
                onClick={() =>
                  setJsonInput(
                    JSON.stringify(SAMPLE_JSON, null, 2)
                  )
                }
              >
                Load example
              </button>

            </div>

            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              spellCheck="false"
            />

          </div>


          <button
            className="process-btn"
            onClick={processEmail}
            disabled={loading}
          >
            {loading
              ? "🤖 Gemini is processing..."
              : "🤖 Process with Gemini"}
          </button>

        </section>


        {/* ====================================================
            TASKS
        ==================================================== */}

        <section className="tasks-section">

          <div className="tasks-heading">

            <div>
              <h2>Recent Tasks</h2>
              <p>
                Latest tasks created from inbound emails
              </p>
            </div>

            <button onClick={loadTasks}>
              View all →
            </button>

          </div>


          {tasks.length === 0 ? (

            <div className="empty-state">

              <div className="empty-icon">
                ✉
              </div>

              <h3>No tasks yet</h3>

              <p>
                Paste an inbound email JSON above to create
                your first AI-routed task.
              </p>

            </div>

          ) : (

            <div className="task-list">

              {tasks.map((task) => (

                <div
                  className="task-card"
                  key={task.id}
                >

                  <div className="task-main">

                    <div className="task-title-row">

                      <h3>{task.title}</h3>

                      <span
                        className={`priority ${task.priority}`}
                      >
                        {task.priority}
                      </span>

                    </div>

                    {task.description && (
                      <p>{task.description}</p>
                    )}

                    <div className="task-meta">

                      <span>
                        👤 {task.assignee_id}
                      </span>

                      <span>
                        🏷️ {task.category}
                      </span>

                      {task.company_name && (
                        <span>
                          🏢 {task.company_name}
                        </span>
                      )}

                      {task.due_date && (
                        <span>
                          📅 {task.due_date}
                        </span>
                      )}

                      {task.deal_value_inr != null && (
                        <span>
                          💰 ₹{task.deal_value_inr.toLocaleString()}
                        </span>
                      )}

                      <span>
                        🎯 {Math.round(task.confidence * 100)}%
                      </span>

                    </div>

                  </div>

                  <div className="task-id">
                    #{task.id}
                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

      </main>

    </div>
  );
}

export default App;