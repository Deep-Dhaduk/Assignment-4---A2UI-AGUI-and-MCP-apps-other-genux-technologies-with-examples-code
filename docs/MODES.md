# Four UI modes, six technologies

The generation mode describes what an agent can decide. The protocol or library describes how the result is carried or rendered. These are independent choices.

| Technology | Static | Declarative | Open-ended | Mixed |
|---|---|---|---|---|
| Foundations | Fixed event card layout | Validated component map | HTML calculator in an iframe | Trusted event panel plus calculator |
| AG-UI | Events deliver values for fixed cards | Events deliver a component graph | A custom event carries HTML to the sandbox | One run carries the graph and its custom region |
| A2UI | Hand-authored Text/Column surface | Data binding and graph-to-A2UI adapter | Host companion iframe; not native A2UI | Official A2UI surface beside the companion iframe |
| OpenUI | Predefined UI program | Agent-created program through the official renderer | Custom Sandbox component holds HTML | Panel contains standard leaves and Sandbox |
| json-render | Predetermined element map | Validated generated element map | Our Sandbox registry component | Standard registry entries plus Sandbox |
| MCP Apps | Fixed venue app with tool data | Resource renders a declarative venue layout | Custom region inside the app's sandbox | Venue UI and nested calculator |
| Harness | Tools populate a fixed result | Tool evidence feeds generated spec | Tool evidence feeds an HTML calculator | Catalog view and custom region after the tool loop |

Every checkpoint has all four mode controls. The 23 default checkpoints emphasize a particular new idea; the mode controls allow comparisons without duplicating the transport and server code.

## Explain these distinctions on video

1. **Static does not mean no AI.** The layout is predetermined; a live model can still choose its values.
2. **Declarative is not arbitrary code.** The app accepts a bounded set of component names and properties and rejects invalid graphs.
3. **Open-ended needs a different boundary.** HTML can contain JavaScript, so it stays in an iframe with `sandbox="allow-scripts"` and a restrictive Content Security Policy.
4. **Mixed keeps a stable surrounding application.** Only the custom region gets the extra freedom.
5. **AG-UI is an event protocol.** Its events can carry any of these representations; it does not itself render the interface.
6. **A2UI is a UI description protocol.** This project uses its official basic renderer for Text/Column. The companion HTML example is a host integration, not a claim that arbitrary HTML is in the standard catalog.
7. **MCP Apps adds a host boundary.** A tool declares a `ui://` resource, and the host controls the app's capabilities. Our browser host only permits `campus_venues`.

## What the source labels mean

- **Offline fixture:** the event data, UI graph, and custom HTML are deterministic original samples. The prompt text is ignored. Domain calculations and real MCP tool/resource requests still execute.
- **Live Gemini:** the server asks Gemini for a plan, spec, program, and (where appropriate) HTML. API responses are validated; there is no silent replacement with a successful-looking fixture on failure.
- **Attendance action:** the server recalculates from trusted data and rebuilds the layout deterministically. This is explicitly labelled as an action without a new Gemini call.
- **Delivery streaming:** the server emits already-produced data in ordered events. These demos do not currently stream Gemini token deltas directly to the page.
