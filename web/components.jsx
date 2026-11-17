import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import { sandboxDocument } from "./protocol.mjs";

export const ActionContext = createContext(() => {});
export function Panel({ title, children }) {
  return (
    <section className="event-panel">
      <h2>{title}</h2>
      <div className="event-grid">{children}</div>
    </section>
  );
}
export function Stat({ label, value }) {
  return (
    <div className="stat">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
export function Note({ text }) {
  return <p className="event-note">{text}</p>;
}
export function Agenda({ items }) {
  return (
    <ol className="agenda">
      {items.map((item, i) => (
        <li key={i}>
          <span>{String(i + 1).padStart(2, "0")}</span>
          {item}
        </li>
      ))}
    </ol>
  );
}
export function Action({ label, action }) {
  const onAction = useContext(ActionContext);
  return (
    <button className="secondary" onClick={() => onAction(action)}>
      {label}
    </button>
  );
}
export function Sandbox({ html }) {
  const ref = useRef(null);
  const [price, setPrice] = useState(null);
  useEffect(() => {
    const listen = (e) => {
      if (
        e.source === ref.current?.contentWindow &&
        e.data?.kind === "campus-preview" &&
        Number.isFinite(e.data.price) &&
        e.data.price >= 0 &&
        e.data.price <= 1000
      )
        setPrice(e.data.price);
    };
    window.addEventListener("message", listen);
    return () => window.removeEventListener("message", listen);
  }, []);
  return (
    <div className="sandbox-wrap">
      <div className="micro">
        ISOLATED CUSTOM REGION {price !== null && `· ticket $${price}`}
      </div>
      <iframe
        ref={ref}
        title="Generated ticket calculator"
        sandbox="allow-scripts"
        srcDoc={sandboxDocument(html)}
      />
    </div>
  );
}
const components = { Panel, Stat, Note, Agenda, Action, Sandbox };
export function OwnRenderer({ spec, id = spec?.root, depth = 0 }) {
  if (!spec?.elements?.[id] || depth > 12) return null;
  const element = spec.elements[id],
    Component = components[element.type];
  if (!Component) return <p role="alert">Unknown component: {element.type}</p>;
  return (
    <Component {...element.props}>
      {element.children?.map((child) => (
        <OwnRenderer key={child} spec={spec} id={child} depth={depth + 1} />
      ))}
    </Component>
  );
}
export function FixedView({ plan }) {
  return (
    <Panel title={plan.title}>
      <Stat label="Attendees" value={String(plan.attendees)} />
      <Stat label="Budget" value={`$${plan.budget.toLocaleString()}`} />
      <Stat label="Venue" value={plan.venue} />
      <Agenda items={plan.agenda} />
      <Note text={plan.summary} />
      <Action label="Add 10 attendees" action="add_attendees" />
    </Panel>
  );
}
