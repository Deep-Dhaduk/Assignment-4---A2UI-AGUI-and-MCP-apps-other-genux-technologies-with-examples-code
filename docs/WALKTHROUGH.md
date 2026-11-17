# Original codelabs: code and recording walkthrough

These 23 checkpoints are new campus-event examples. They follow the reference course's progression but use our own implementation and scenario. Shared server and renderer modules are reused deliberately; a checkpoint is a guided execution path, not a copied standalone project.

## Before recording

1. Follow the root README to install dependencies and build the browser bundle.
2. Run `python run.py doctor`, then `python run.py test` and `npm test`.
3. Start `python run.py`, open http://127.0.0.1:8000, and keep the terminal visible for the setup explanation.
4. Select **Offline fixture** for reproducible rehearsals. Say explicitly that this is scripted sample content.
5. After configuring Gemini, use **Live Gemini** for AI execution. Only live mode uses the prompt. Record any quota or validation failure honestly.
6. Open the source files named for each chapter. Show the input, transformation, validation, and final rendering; reading every line aloud is unnecessary.

The **Interface**, **Protocol**, and **Walkthrough** tabs provide the three views needed during recording. Use the Protocol tab to expand individual events instead of showing a wall of JSON at once.

## Part 1 — Foundations

### 01.1 — Fixed event cards

- **Run:** select 01.1 and Static, then Run checkpoint.
- **Source:** `backend/domain.py:sample_plan`, `web/components.jsx:FixedView`, `backend/gemini.py:generate_document`.
- **Trace:** the plan contains event data. `FixedView` always places the same cards, agenda, note, and attendance button in the same layout. In live mode Gemini supplies values, not the surrounding UI code.
- **Show:** attendance, budget, venue, and agenda. Change the attendance input to 120 and rerun. The offline venue becomes Campus Auditorium because the garden is too small.
- **Explain:** static generation means the application fixes the interface structure. It does not mean the values must be hard-coded in a live run.

### 01.2 — A layout from data

- **Run:** select 01.2 and Declarative.
- **Source:** `backend/representations.py:make_spec`, `validate_spec`; `web/components.jsx:OwnRenderer`.
- **Trace:** `{root, elements}` references components by ID. The validator checks component props, child references, reachability, and cycles before the recursive renderer runs.
- **Show:** expand the `campus.result` event and compare its `spec` with the visible layout. For a local exercise, change the `event.children` order in `make_spec`, restart the server, rerun, then restore the order.
- **Explain:** the application controls the component catalog while the declarative document controls composition.

### 01.3 — An interactive calculator

- **Run:** select 01.3 and Open-ended. Move the ticket-price slider.
- **Source:** `backend/representations.py:calculator_html`; `web/components.jsx:Sandbox`; `web/protocol.mjs:sandboxDocument`.
- **Trace:** an HTML string becomes `iframe.srcDoc`, never HTML injected into the main application's DOM. The iframe has an opaque origin and inline-only script/style policy.
- **Show:** ticket income changes without a server call. The small parent label updates only after the source window and message shape are checked.
- **Explain:** the offline HTML is an original fixture; the live HTML comes from Gemini. Isolation limits capabilities but is not a production security guarantee.

### 01.4 — Combine both approaches

- **Run:** select 01.4 and Mixed.
- **Source:** `make_spec` adds a `Sandbox` element; `OwnRenderer` maps it to the isolated custom region.
- **Show:** standard attendance/budget cards and the calculator coexist. Switch to Open-ended to show that the standard surrounding plan disappears.
- **Explain:** mixed mode adds freedom in one region while keeping the rest of the interface consistent.

## Part 2 — AG-UI

### 02.1 — Observe the run lifecycle

- **Run:** select 02.1. After execution open Protocol.
- **Source:** `backend/engine.py:events`, `backend/main.py:run`, `web/protocol.mjs:consumeSSE`.
- **Trace:** official `ag_ui.core` objects become SSE frames through `EventEncoder`. The browser decodes complete frames even when network chunks split the JSON.
- **Show:** `RUN_STARTED`, `TEXT_MESSAGE_START`, several `TEXT_MESSAGE_CONTENT` events, `TEXT_MESSAGE_END`, and `RUN_FINISHED`.
- **Explain:** AG-UI carries lifecycle and interaction events. This implementation paces delivery after generation; it is not raw model-token streaming.

### 02.2 — Synchronize attendance

- **Run:** select 02.2, then click Add 10 attendees.
- **Source:** `backend/main.py:action`; `backend/engine.py:events`; `web/app.jsx:act`.
- **Trace:** the initial run publishes a `STATE_SNAPSHOT`. The authorized action produces an RFC 6902 replacement in `STATE_DELTA`, updates the server session, and returns the refreshed interface.
- **Show:** 80 becomes 90. Repeat until capacity changes; explain the venue change. Inspect the delta's `/attendees` path.
- **Explain:** this action is deterministic and does not call Gemini. Unknown actions are rejected, and a UI action is not permission to book a room.

### 02.3 — Tool calls become UI

- **Run:** select 02.3. Open the tool execution details and Protocol.
- **Source:** `backend/harness.py:run_tools`, `execute`; `backend/engine.py:events`.
- **Trace:** a tool name and arguments are checked, the Python domain function runs, and the result becomes `TOOL_CALL_RESULT`. Every result references its matching tool-call ID.
- **Show:** `find_venues`, `estimate_event`, and `render_event` arguments/results. The fixture chooses a known sequence; live Gemini chooses tool calls.
- **Explain:** a tool request, a completed tool result, and a rendered interface are three different steps.

## Part 3 — A2UI

### 03.1 — A surface by hand

- **Run:** select 03.1 and Static.
- **Source:** `backend/representations.py:a2ui_messages`; `web/renderers.jsx:A2uiView`.
- **Trace:** create a named surface using the basic catalog, declare Text/Column components, then send the data model. The official `MessageProcessor` and `A2uiSurface` handle rendering.
- **Show:** `createSurface`, `updateComponents`, and `updateDataModel` in the protocol trace. Point to the root component and child IDs.
- **Explain:** this example targets A2UI v0.9 explicitly. A catalog ID identifies the component vocabulary, not an API key or transport endpoint.

### 03.2 — Bind data to components

- **Run:** select 03.2. Inspect the two `updateDataModel` messages.
- **Source:** `backend/engine.py:build_payload` and `a2ui_messages`.
- **Trace:** the Text component references `/attendance`. The initial model says attendance is loading, and a later data-only message replaces that path with the number of attendees. The component graph stays the same.
- **Show:** there is only one `updateComponents` message. The final official renderer resolves the last value. The final UI is mounted after the delivered messages are collected, so do not claim that a loading animation was shown live on screen.
- **Explain:** structure and data are separate contracts. This is useful even when the structure is hand-authored.

### 03.3 — A2UI carried by AG-UI

- **Run:** select 03.3 and Mixed; compare with Declarative and Open-ended.
- **Source:** `spec_to_a2ui`, `backend/engine.py:events`, `web/renderers.jsx:A2uiView`.
- **Trace:** our validated graph is translated to native A2UI Column/Text components; each envelope travels in an AG-UI `CUSTOM` event named `a2ui`.
- **Show:** expand a `CUSTOM` event. Explain its outer event wrapper and inner UI message separately.
- **Explain:** the HTML calculator is a companion host iframe, not an arbitrary-HTML feature of the A2UI basic catalog. No A2UI protocol support is invented to make the modes appear uniform.

## Part 4 — OpenUI

### 04.1 — Read a UI program

- **Run:** select 04.1 and Static.
- **Source:** `backend/representations.py:openui_program`; `web/renderers.jsx:library`.
- **Trace:** named statements such as `root = Panel(...)` refer to leaf statements. Positional argument order comes from the component's Zod property order.
- **Show:** compare the program in the generated-representation panel with the rendered event card.
- **Explain:** this is OpenUI Lang rendered by `@openuidev/react-lang`, not a JSON object relabelled as OpenUI.

### 04.2 — Stream a component library

- **Run:** select 04.2 and Declarative. Watch the interface as statements arrive.
- **Source:** `web/renderers.jsx:defineComponent`, `createLibrary`, `OpenView`; `backend/engine.py:events`.
- **Trace:** `openui.line` events accumulate into a program. The official renderer receives the partial program with `isStreaming` and resolves references as statements arrive.
- **Show:** the root arrives before its leaves. Expand the corresponding line events.
- **Explain:** these lines are delivered incrementally after generation completes; the lesson demonstrates renderer behavior, not a measured provider streaming advantage.

### 04.3 — Compare representations

- **Run:** select 04.3. Read the two byte counts below the result.
- **Source:** `build_payload` calculates `len(text.encode())` for JSON and OpenUI representing the same event.
- **Show:** the JSON map and named OpenUI statements encode the same facts. Explain the measurement unit and serialization choices.
- **Explain:** byte size is not token count. There is no claim that a smaller string necessarily makes a model faster, cheaper, or more accurate.

### 04.4 — A custom OpenUI component

- **Run:** select 04.4 and Mixed. Move the calculator slider.
- **Source:** `web/renderers.jsx` registers the Sandbox component alongside Stat, Note, Agenda, and Action.
- **Trace:** OpenUI composes an allowed custom component whose implementation supplies the iframe boundary.
- **Show:** the `Sandbox(html)` statement and its rendered iframe. Compare with the same component in json-render.
- **Explain:** the library author controls what that component does. The language does not grant arbitrary host-page execution.

## Part 5 — json-render

### 05.1 — Validate a component catalog

- **Run:** select 05.1 and Declarative.
- **Source:** `web/renderers.jsx:propSchemas`, `catalog`, `registry`, `JsonView`; `backend/representations.py:validate_spec`.
- **Trace:** the official library maps the spec's element types to registered React implementations. The backend validates props and graph topology before the browser sees the result.
- **Show:** compare a Stat's `{label,value}` props in the spec with its Zod definition and visible card.
- **Explain:** valid JSON alone is insufficient; unknown components, missing references, and cycles must also be rejected. Show the corresponding Python test rather than breaking a recording run.

### 05.2 — Build with patches

- **Run:** select 05.2. Inspect `spec.patch` events.
- **Source:** `backend/representations.py:patches_for`; `web/protocol.mjs:applyPatch`.
- **Trace:** `add /root`, `add /elements`, then one `add /elements/<id>` per component build the map. The patch function rejects dangerous property paths and missing parents.
- **Show:** the assembling map, then the completed official renderer output.
- **Explain:** this implementation waits for a complete validated graph before rendering the final card. It demonstrates incremental delivery and reconstruction, not partial component rendering or arbitrary RFC 6902 operations.

### 05.3 — Actions and a second target

- **Run:** select 05.3. Click Add 10 attendees. In a terminal run `python run.py terminal`.
- **Source:** `web/components.jsx:Action`; `backend/main.py:action`; `backend/representations.py:terminal_view`.
- **Trace:** the React Action uses the host's explicit action handler. A server response rebuilds the known layout without a hidden model call. The terminal walker consumes the same spec shape as the web renderer.
- **Show:** the web card and indented terminal view. The terminal prints an HTML-region placeholder because it does not execute HTML.
- **Explain:** shared representation does not imply identical capabilities across targets.

## Part 6 — MCP Apps

### 06.1 — Discover an app resource

- **Run:** select 06.1 and Static.
- **Source:** `backend/mcp_app.py`; `backend/main.py:mcp_session`, `discover`.
- **Trace:** the real MCP client initializes over Streamable HTTP, lists tools, follows `_meta.ui.resourceUri`, and reads `ui://campus/venue-explorer.html`.
- **Show:** the `MCP_DISCOVERY` entry and its resource URI. Explain `text/html;profile=mcp-app`.
- **Explain:** a normal MCP text tool is not automatically an MCP App. The UI resource and host bridge make the interface possible.

### 06.2 — Interact through a host

- **Run:** select 06.2. Set minimum capacity to 150 inside the embedded app and click Filter venues.
- **Source:** `web/mcp-app.html`; `web/mcp-host.jsx`; `backend/mcp_app.py:campus_venues`.
- **Trace:** app `tools/call` → host validates the source frame and allowed tool → backend MCP client calls the server → tool result returns to the app.
- **Show:** only Campus Auditorium remains. The declarative layout references venue IDs separately from their data.
- **Explain:** the teaching host supports initialization, tool-result notification, and one allowed tool. It is not a full implementation of every host capability. The app uses a button rather than form submission because its sandbox does not allow forms.

### 06.3 — An app with a custom region

- **Run:** select 06.3 and Mixed. Move the slider in the embedded calculator, then filter venues.
- **Source:** `campus_venues`; `app_resource`; the nested iframe in `web/mcp-app.html`.
- **Trace:** the outer host isolates the app resource, and the app separately isolates its custom HTML region.
- **Show:** the fixed/declarative venue area and generated region. Explain that a filter refresh recomputes a local fixture calculator and does not secretly call Gemini.
- **Explain:** tool data, host capabilities, and generated markup cross different boundaries. No reservation is performed.

## Part 7 — Harness integration

### 07.1 — Search, estimate, render

- **Run:** select 07.1, then expand Agent tool execution.
- **Source:** `backend/harness.py:TOOLS`, `execute`, `run_tools`.
- **Trace:** venue search checks capacity, budget estimation applies a $6-per-attendee materials cost, and `render_event` validates a plan into a component graph.
- **Show:** 80 attendees at Learning Garden cost $320 + $480 = $800, leaving $400 of the $1,200 budget.
- **Explain:** fixture mode scripts the tool choices but runs the real domain functions. Live mode receives actual function calls from Gemini and executes only allowed tools.

### 07.2 — Choose a representation

- **Run:** select 07.2 and Declarative, then compare Static and Open-ended.
- **Source:** `run_tools`; `backend/gemini.py:generate_document`; `backend/engine.py:build_payload`.
- **Trace:** tool results become evidence for the final generation request, whose validated output is routed to the selected renderer.
- **Show:** the same checked venue data can be presented as a fixed card, a component graph, or custom HTML.
- **Explain:** this is an original local harness. It deliberately replaces the reference's hosted TrueForge example and does not claim compatibility with that service.

### 07.3 — Keep a human in the loop

- **Run:** select 07.3 and Mixed. Change attendance from 80 to 120 and run again.
- **Source:** `RunRequest` validates the input; `venues_for` filters capacity; `run_tools` has a three-round ceiling; `make_spec` adds the custom region.
- **Show:** the garden is no longer viable, so the auditorium is used. With materials, $650 + $720 = $1,370, exceeding the original budget by $170.
- **Explain:** the system displays the tradeoff for the user. It cannot book, pay, send messages, or execute arbitrary model-named tools. A UI action does not authorize those operations.

## Finish your recording

Summarize the division of responsibility: the model proposes content, the app validates it, a protocol carries it, a renderer displays it, and the server authorizes actions. Show the test commands and identify any live integrations you could not execute. Add your video URLs to `docs/VIDEOS.md` before submitting.
