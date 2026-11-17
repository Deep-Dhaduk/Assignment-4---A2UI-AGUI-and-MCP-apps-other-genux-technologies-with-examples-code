import test from "node:test";
import assert from "node:assert/strict";
import {
  applyPatch,
  consumeSSE,
  isAllowedToolMessage,
  sandboxDocument,
} from "../web/protocol.mjs";

test("SSE reader handles split frames and CRLF", async () => {
  const encoder = new TextEncoder();
  const pieces = [
    'data: {"type":"RUN_STA',
    'RTED"}\r\n\r\n',
    'data: {"type":"RUN_FINISHED"}\n\n',
  ];
  const response = new Response(
    new ReadableStream({
      start(c) {
        pieces.forEach((x) => c.enqueue(encoder.encode(x)));
        c.close();
      },
    }),
  );
  const events = [];
  await consumeSSE(response, (e) => events.push(e));
  assert.equal(events.length, 2);
});
test("SSE truncation is not success", async () => {
  await assert.rejects(
    consumeSSE(new Response('data: {"type":"RUN_STARTED"}\n\n'), () => {}),
    /before the run completed/,
  );
});
test("patches are immutable and reject prototype pollution", () => {
  const original = { elements: {} };
  const changed = applyPatch(original, {
    op: "add",
    path: "/elements/root",
    value: { type: "Panel" },
  });
  assert.deepEqual(original, { elements: {} });
  assert.equal(changed.elements.root.type, "Panel");
  assert.throws(() =>
    applyPatch({}, { op: "add", path: "/__proto__/polluted", value: true }),
  );
  assert.throws(() =>
    applyPatch({}, { op: "replace", path: "/missing", value: 1 }),
  );
});
test("host limits tool capabilities and sandbox begins with CSP", () => {
  const msg = {
    jsonrpc: "2.0",
    method: "tools/call",
    params: { name: "campus_venues", arguments: { attendees: 80 } },
  };
  assert.equal(isAllowedToolMessage(msg), true);
  msg.params.name = "run_shell";
  assert.equal(isAllowedToolMessage(msg), false);
  assert.ok(
    sandboxDocument("<script>test()</script>").startsWith(
      '<meta http-equiv="Content-Security-Policy"',
    ),
  );
});
