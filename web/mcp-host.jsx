import React, { useEffect, useRef, useState } from "react";
import { isAllowedToolMessage, sandboxDocument } from "./protocol.mjs";

export function McpView({ payload, onTrace }) {
  const frame = useRef(null),
    [html, setHtml] = useState(""),
    [error, setError] = useState("");
  useEffect(() => {
    let alive = true;
    setError("");
    setHtml("");
    async function call(args) {
      const response = await fetch("/api/mcp/call", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: "campus_venues", ...args }),
      });
      if (!response.ok)
        throw new Error(`MCP tool request failed (${response.status})`);
      return response.json();
    }
    async function listen(event) {
      if (
        event.source !== frame.current?.contentWindow ||
        event.data?.jsonrpc !== "2.0"
      )
        return;
      const msg = event.data;
      onTrace({ type: "MCP_BRIDGE", method: msg.method });
      const reply = (result) => {
        if (alive)
          event.source.postMessage({ jsonrpc: "2.0", id: msg.id, result }, "*");
      };
      try {
        if (msg.method === "ui/initialize")
          reply({
            protocolVersion: "2026-01-26",
            hostInfo: { name: "Campus teaching host", version: "1.0.0" },
            hostCapabilities: {},
            hostContext: { theme: "light" },
          });
        else if (msg.method === "ui/notifications/initialized") {
          const result = await call({
            attendees: payload.plan.attendees,
            mode: payload.mode,
            custom_html: payload.html,
          });
          if (alive)
            event.source.postMessage(
              {
                jsonrpc: "2.0",
                method: "ui/notifications/tool-result",
                params: result,
              },
              "*",
            );
        } else if (isAllowedToolMessage(msg))
          reply(await call(msg.params.arguments));
        else if (msg.id !== undefined)
          event.source.postMessage(
            {
              jsonrpc: "2.0",
              id: msg.id,
              error: {
                code: -32601,
                message: "This host only allows the campus capacity tool.",
              },
            },
            "*",
          );
      } catch (e) {
        if (alive) setError(e.message);
        if (msg.id !== undefined && alive)
          event.source.postMessage(
            {
              jsonrpc: "2.0",
              id: msg.id,
              error: { code: -32603, message: "Tool request failed." },
            },
            "*",
          );
      }
    }
    window.addEventListener("message", listen);
    fetch("/api/mcp/discover")
      .then(async (response) => {
        if (!response.ok) throw new Error("MCP resource discovery failed");
        return response.json();
      })
      .then((data) => {
        if (!alive) return;
        onTrace({ type: "MCP_DISCOVERY", tools: data.tools });
        const resource = data.resource.contents.find(
          (c) => c.uri === "ui://campus/venue-explorer.html",
        );
        if (!resource?.text) throw new Error("App resource is missing");
        setHtml(resource.text);
      })
      .catch((e) => {
        if (alive) setError(e.message);
      });
    return () => {
      alive = false;
      window.removeEventListener("message", listen);
    };
  }, [payload.session, payload.plan.attendees, payload.mode]);
  return (
    <>
      {error ? (
        <p role="alert" className="error">
          {error}
        </p>
      ) : html ? (
        <iframe
          className="mcp-frame"
          ref={frame}
          title="MCP campus venue app"
          sandbox="allow-scripts"
          srcDoc={sandboxDocument(html)}
        />
      ) : (
        <p role="status">Discovering the MCP resource…</p>
      )}
    </>
  );
}
