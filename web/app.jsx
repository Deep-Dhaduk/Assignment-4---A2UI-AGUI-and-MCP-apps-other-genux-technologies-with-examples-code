import React, { useState, useEffect, useCallback } from "react";
import { createRoot } from "react-dom/client";
import { consumeSSE, applyPatch } from "./protocol.mjs";
import {
  ActionContext,
  OwnRenderer,
  FixedView,
  Sandbox,
} from "./components.jsx";
import { JsonView, OpenView, A2uiView } from "./renderers.jsx";
import { McpView } from "./mcp-host.jsx";

const modes = [
  ["static", "Static", "AI fills a fixed interface"],
  ["declarative", "Declarative", "A component map describes the UI"],
  ["open", "Open-ended", "Custom HTML in an isolated frame"],
  ["mixed", "Mixed", "Catalog + custom region"],
];
const files = {
  foundations: [
    "backend/domain.py",
    "backend/representations.py",
    "web/components.jsx",
  ],
  agui: ["backend/engine.py", "web/protocol.mjs", "backend/main.py"],
  a2ui: [
    "backend/representations.py",
    "web/renderers.jsx",
    "backend/engine.py",
  ],
  openui: [
    "web/renderers.jsx",
    "backend/representations.py",
    "backend/gemini.py",
  ],
  jsonrender: [
    "web/renderers.jsx",
    "web/protocol.mjs",
    "backend/representations.py",
  ],
  mcp: ["backend/mcp_app.py", "web/mcp-app.html", "web/mcp-host.jsx"],
  harness: ["backend/harness.py", "backend/gemini.py", "backend/engine.py"],
};
class RenderBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) {
    return { error: error.message };
  }
  render() {
    return this.state.error ? (
      <p className="error" role="alert">
        Renderer rejected this output: {this.state.error}
      </p>
    ) : (
      this.props.children
    );
  }
}
function App() {
  const [lessons, setLessons] = useState([]),
    [health, setHealth] = useState(null),
    [id, setId] = useState(location.hash.slice(1) || "01.1");
  const [mode, setMode] = useState("static"),
    [source, setSource] = useState("fixture"),
    [prompt, setPrompt] = useState(""),
    [attendees, setAttendees] = useState(80);
  const [busy, setBusy] = useState(false),
    [payload, setPayload] = useState(null),
    [trace, setTrace] = useState([]),
    [tab, setTab] = useState("preview"),
    [error, setError] = useState(""),
    [prose, setProse] = useState("");
  const [openStream, setOpenStream] = useState(""),
    [patchSpec, setPatchSpec] = useState({}),
    [elapsed, setElapsed] = useState(null);
  const lesson = lessons.find((x) => x.id === id) || lessons[0];
  const log = useCallback(
    (event) => setTrace((rows) => [...rows.slice(-199), event]),
    [],
  );
  useEffect(() => {
    Promise.all([
      fetch("/api/lessons").then((r) => r.json()),
      fetch("/api/health").then((r) => r.json()),
    ])
      .then(([l, h]) => {
        setLessons(l);
        setHealth(h);
      })
      .catch(() => setError("Cannot reach the local server."));
  }, []);
  useEffect(() => {
    if (lesson) {
      setMode(lesson.mode);
      setPrompt(lesson.prompt);
      setPayload(null);
      setError("");
      setTrace([]);
      setProse("");
      setOpenStream("");
      setPatchSpec({});
      setElapsed(null);
      location.hash = lesson.id;
    }
  }, [lesson?.id]);
  useEffect(() => {
    const change = () => {
      if (!busy) setId(location.hash.slice(1) || "01.1");
    };
    window.addEventListener("hashchange", change);
    return () => window.removeEventListener("hashchange", change);
  }, [busy]);
  async function run(event) {
    event?.preventDefault();
    if (busy || !lesson) return;
    setBusy(true);
    setError("");
    setPayload(null);
    setTrace([]);
    setProse("");
    setOpenStream("");
    setPatchSpec({});
    setElapsed(null);
    setTab("preview");
    const start = performance.now();
    try {
      const response = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lesson: lesson.id,
          mode,
          source,
          prompt,
          attendees,
        }),
      });
      await consumeSSE(response, (event) => {
        log(event);
        if (event.type === "RUN_ERROR") setError(event.message);
        if (event.type === "TEXT_MESSAGE_CONTENT")
          setProse((text) => text + event.delta);
        if (event.type === "CUSTOM" && event.name === "campus.result")
          setPayload(event.value);
        if (event.type === "CUSTOM" && event.name === "openui.line")
          setOpenStream((text) => text + event.value);
        if (event.type === "CUSTOM" && event.name === "spec.patch")
          setPatchSpec((doc) => applyPatch(doc, event.value));
      });
      setElapsed(((performance.now() - start) / 1000).toFixed(1));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  async function act(action) {
    if (busy || !payload) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch("/api/action", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session: payload.session, action }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Action failed");
      setPayload(data.payload);
      setAttendees(data.payload.plan.attendees);
      data.events.forEach(log);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }
  function surface() {
    if (!payload) {
      if (openStream) return <OpenView program={openStream} streaming={busy} />;
      if (Object.keys(patchSpec).length)
        return (
          <div>
            <p>Receiving element-map patches…</p>
            <pre>{JSON.stringify(patchSpec, null, 2)}</pre>
          </div>
        );
      return (
        <div className="empty">
          <div className="diagram">
            <span>Request</span>
            <i>→</i>
            <span>Agent</span>
            <i>→</i>
            <span>Interface</span>
          </div>
          <h2>Make the response interactive.</h2>
          <p>
            {busy
              ? "Preparing the interface…"
              : "Run this checkpoint to see the interface and inspect the messages behind it."}
          </p>
          <div className="empty-cards">
            <div />
            <div />
            <div />
          </div>
        </div>
      );
    }
    if (payload.theme === "mcp")
      return <McpView payload={payload} onTrace={log} />;
    if (payload.theme === "a2ui")
      return (
        <>
          {payload.mode !== "open" && <A2uiView messages={payload.a2ui} />}
          <button
            className="secondary"
            disabled={busy}
            onClick={() => act("add_attendees")}
          >
            Add 10 attendees
          </button>
          {payload.html && (
            <>
              <p className="micro">
                Host companion region · not part of the A2UI basic catalog
              </p>
              <Sandbox html={payload.html} />
            </>
          )}
        </>
      );
    if (payload.theme === "openui")
      return (
        <>
          <OpenView program={payload.program} />
          {id === "04.3" && (
            <div className="comparison">
              <StatBlock
                label="JSON bytes"
                value={payload.comparison.json_utf8_bytes}
              />
              <StatBlock
                label="OpenUI bytes"
                value={payload.comparison.openui_utf8_bytes}
              />
              <small>
                Same event facts; UTF-8 bytes. This is not a tokenizer or
                latency benchmark.
              </small>
            </div>
          )}
        </>
      );
    if (payload.theme === "jsonrender") return <JsonView spec={payload.spec} />;
    if (payload.mode === "static") return <FixedView plan={payload.plan} />;
    return <OwnRenderer spec={payload.spec} />;
  }
  if (!lesson)
    return (
      <main className="loading">{error || "Opening Campus GenUI Lab…"}</main>
    );
  const groups = [...new Set(lessons.map((x) => x.section))];
  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="#01.1">
          <span className="brand-mark">c/</span>
          <span>
            campus<span className="brand-sub">GENUI LAB</span>
          </span>
        </a>
        <p className="sidebar-intro">
          One campus. Six technologies.
          <br />A different kind of interface.
        </p>
        <nav aria-label="Codelab navigation">
          {groups.map((group, index) => (
            <div className="nav-group" key={group}>
              <div className="nav-heading">
                <span>{String(index + 1).padStart(2, "0")}</span>
                {group}
              </div>
              {lessons
                .filter((x) => x.section === group)
                .map((item) => (
                  <button
                    disabled={busy}
                    key={item.id}
                    className={id === item.id ? "nav-item active" : "nav-item"}
                    onClick={() => setId(item.id)}
                  >
                    <span>{item.id}</span>
                    {item.title}
                  </button>
                ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          Assignment 04<span>Original examples · Python + React</span>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>THE GENERATIVE INTERFACE NOTEBOOK</span>
          <span className="connection">
            <i />
            {health?.gemini_configured
              ? "Gemini key configured"
              : "Offline examples ready"}
          </span>
        </header>
        <section className="intro">
          <div className="eyebrow">
            {lesson.section.toUpperCase()} <span>/ CHECKPOINT {lesson.id}</span>
          </div>
          <div className="intro-row">
            <h1>
              {lesson.title}
              <span>.</span>
            </h1>
            <div className="lesson-count">
              <strong>
                {String(lessons.indexOf(lesson) + 1).padStart(2, "0")}
              </strong>
              <span>/ 23 checkpoints</span>
            </div>
          </div>
          <p>{lesson.objective}</p>
        </section>
        <section className="workspace">
          <form className="controls" onSubmit={run}>
            <div className="control-title">
              <span className="micro">01 / CONFIGURE THE EXPERIENCE</span>
              <span className="tag">Campus event planner</span>
            </div>
            <fieldset className="mode-grid">
              <legend className="sr-only">Generation mode</legend>
              {modes.map(([value, title, description]) => (
                <label
                  className={mode === value ? "mode selected" : "mode"}
                  key={value}
                >
                  <input
                    type="radio"
                    name="mode"
                    value={value}
                    checked={mode === value}
                    disabled={busy}
                    onChange={() => setMode(value)}
                  />
                  <strong>{title}</strong>
                  <span>{description}</span>
                </label>
              ))}
            </fieldset>
            <label className="prompt-label" htmlFor="prompt">
              What should the planner create?
            </label>
            <textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              maxLength={2000}
              required
              disabled={busy}
            />
            <div className="run-row">
              <label>
                Data source
                <select
                  value={source}
                  onChange={(e) => setSource(e.target.value)}
                  disabled={busy}
                >
                  <option value="fixture">
                    Offline fixture · no API calls
                  </option>
                  <option value="gemini" disabled={!health?.gemini_configured}>
                    Live Gemini · uses free-tier quota
                  </option>
                </select>
              </label>
              <label>
                Attendees
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={attendees}
                  onChange={(e) => setAttendees(Number(e.target.value))}
                  disabled={busy}
                  required
                />
              </label>
              <button className="primary" disabled={busy}>
                {busy ? "Running…" : "Run checkpoint"}
                <span>↗</span>
              </button>
            </div>
            <p className="footnote">
              {source === "fixture"
                ? "Offline examples use fixed sample content; the prompt is used only in live mode."
                : "Keep billing disabled in AI Studio. One generation request; harness examples may use up to three extra tool-loop requests."}
            </p>
          </form>
          <section className="output">
            <div className="output-header">
              <div className="tabs" role="tablist" aria-label="Output views">
                {[
                  ["preview", "Interface"],
                  ["protocol", `Protocol (${trace.length})`],
                  ["walkthrough", "Walkthrough"],
                ].map(([name, label]) => (
                  <button
                    key={name}
                    role="tab"
                    aria-selected={tab === name}
                    onClick={() => setTab(name)}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <span className="result-state">
                {busy
                  ? "● Running"
                  : payload
                    ? payload.source === "fixture"
                      ? "● Offline fixture"
                      : "● Gemini output"
                    : "○ Ready"}
                {elapsed && ` · ${elapsed}s`}
              </span>
            </div>
            {error && (
              <div role="alert" className="error">
                {error}
              </div>
            )}
            <div className="output-body" role="tabpanel">
              {tab === "preview" && (
                <ActionContext.Provider value={act}>
                  <RenderBoundary
                    key={`${payload?.session}-${payload?.plan.attendees}-${lesson.id}`}
                  >
                    {surface()}
                  </RenderBoundary>
                  {payload?.action_note && (
                    <p className="footnote">{payload.action_note}</p>
                  )}
                  {payload?.trace?.length > 0 && (
                    <details className="tool-details">
                      <summary>
                        Agent tool execution ({payload.trace.length})
                      </summary>
                      <pre>{JSON.stringify(payload.trace, null, 2)}</pre>
                    </details>
                  )}
                </ActionContext.Provider>
              )}
              {tab === "protocol" && (
                <>
                  <p className="footnote">
                    SSE delivery is paced for teaching after generation
                    completes; this is not raw Gemini token streaming.
                  </p>
                  <details>
                    <summary>Generated representation</summary>
                    <pre>
                      {payload
                        ? JSON.stringify(
                            payload.theme === "a2ui"
                              ? payload.a2ui
                              : payload.theme === "openui"
                                ? payload.program
                                : payload.spec,
                            null,
                            2,
                          )
                        : "Run a checkpoint first."}
                    </pre>
                  </details>
                  <div className="event-log">
                    {trace.map((event, index) => (
                      <details key={index}>
                        <summary>
                          <span>{String(index + 1).padStart(2, "0")}</span>
                          {event.type}
                          {event.name && ` / ${event.name}`}
                        </summary>
                        <pre>{JSON.stringify(event, null, 2)}</pre>
                      </details>
                    ))}
                  </div>
                </>
              )}
              {tab === "walkthrough" && (
                <div className="walkthrough">
                  <h2>Explain the request, then trace the result.</h2>
                  <p>{lesson.objective}</p>
                  <ol>
                    <li>
                      Show the selected mode and predict what the agent
                      controls.
                    </li>
                    <li>
                      Open the source files below and explain the input,
                      validation, and rendering.
                    </li>
                    <li>
                      Run the checkpoint. Compare the interface with its
                      protocol messages.
                    </li>
                    <li>
                      Change attendance or mode and explain the difference.
                    </li>
                    <li>
                      State whether this run used an offline fixture or live
                      Gemini.
                    </li>
                  </ol>
                  <div className="file-list">
                    {files[lesson.theme].map((file) => (
                      <code key={file}>{file}</code>
                    ))}
                  </div>
                  <p>
                    Read the matching chapter in{" "}
                    <code>docs/WALKTHROUGH.md</code> for the recording sequence
                    and expected behavior.
                  </p>
                  {lesson.theme === "a2ui" && (
                    <p>
                      A2UI uses its official Lit renderer for the basic catalog.
                      Open-ended HTML is a host companion region, not a native
                      A2UI capability.
                    </p>
                  )}
                  {lesson.theme === "harness" && (
                    <p>
                      This is our local tool loop. It does not use or simulate
                      TrueForge.
                    </p>
                  )}
                </div>
              )}
            </div>
            {prose && tab === "preview" && (
              <div className="prose">
                <span className="micro">PLANNER NOTE</span>
                <p>{prose}</p>
              </div>
            )}
          </section>
        </section>
        <footer>
          <span>Built to understand, not just to watch.</span>
          <span>
            23 checkpoints · 4 generation modes · original implementation
          </span>
        </footer>
      </main>
    </div>
  );
}
function StatBlock({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
createRoot(document.getElementById("root")).render(<App />);
