// Small original transport utilities, independent of any renderer.
export async function consumeSSE(response, onEvent) {
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  if (!response.body)
    throw new Error("This browser did not provide a response stream.");
  const reader = response.body.getReader(),
    decoder = new TextDecoder();
  let buffer = "",
    terminal = false;
  try {
    for (;;) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      buffer = buffer.replace(/\r\n/g, "\n");
      let end;
      while ((end = buffer.indexOf("\n\n")) >= 0) {
        const frame = buffer.slice(0, end);
        buffer = buffer.slice(end + 2);
        const data = frame
          .split("\n")
          .filter((x) => x.startsWith("data:"))
          .map((x) => x.slice(5).trimStart())
          .join("\n");
        if (!data) continue;
        const event = JSON.parse(data);
        if (event.type === "RUN_FINISHED" || event.type === "RUN_ERROR")
          terminal = true;
        await onEvent(event);
      }
      if (done) break;
    }
    if (!terminal)
      throw new Error("The connection ended before the run completed.");
  } finally {
    reader.releaseLock();
  }
}

export function applyPatch(document, patch) {
  // Intentionally bounded RFC 6902 subset for the element-map lesson.
  if (!["add", "replace"].includes(patch.op))
    throw new Error("Unsupported patch operation");
  const parts = patch.path
    .split("/")
    .slice(1)
    .map((x) => x.replace(/~1/g, "/").replace(/~0/g, "~"));
  if (
    !parts.length ||
    parts.some(
      (x) => !x || ["__proto__", "constructor", "prototype"].includes(x),
    )
  )
    throw new Error("Unsafe patch path");
  const next = structuredClone(document);
  let target = next;
  for (const key of parts.slice(0, -1)) {
    if (
      !Object.hasOwn(target, key) ||
      typeof target[key] !== "object" ||
      target[key] === null
    )
      throw new Error("Missing patch parent");
    target = target[key];
  }
  const key = parts.at(-1);
  if (patch.op === "replace" && !Object.hasOwn(target, key))
    throw new Error("Missing replace target");
  target[key] = structuredClone(patch.value);
  return next;
}

export function sandboxDocument(html) {
  return (
    `<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; form-action 'none'; base-uri 'none'">` +
    html
  );
}

export function isAllowedToolMessage(message) {
  return (
    message?.jsonrpc === "2.0" &&
    message.method === "tools/call" &&
    message.params?.name === "campus_venues" &&
    Number.isInteger(message.params.arguments?.attendees) &&
    message.params.arguments.attendees >= 1 &&
    message.params.arguments.attendees <= 500
  );
}
