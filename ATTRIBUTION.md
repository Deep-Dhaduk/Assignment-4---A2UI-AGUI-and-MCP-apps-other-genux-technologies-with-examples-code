# References and authorship

This project contains new campus-event examples written for this assignment with AI coding assistance. The professor's [simple-coding-harness GenUI course](https://github.com/dlmastery/simple-coding-harness/tree/main/genui) informed the seven-theme learning sequence and the 23 checkpoints. Its demo implementations are not part of this submission.

An earlier, unused import is retained only in ignored local folders (`reference-harness/` and `.local/reference-import/`). Neither is needed to install, run, or test this project. No application imports those folders.

The original scenario, backend, UI, adapters, teaching materials, and tests are in `backend/`, `web/`, `docs/`, and `tests/`. Third-party SDKs are installed as dependencies and retain their own licenses.

Primary technical references:

- [AG-UI events](https://docs.ag-ui.com/concepts/events)
- [A2UI](https://a2ui.org/): this project deliberately targets the v0.9 message format supported by its pinned Lit renderer.
- [json-render](https://json-render.dev/docs/quick-start)
- [OpenUI component libraries](https://www.openui.com/docs/openui-lang/defining-components)
- [MCP Apps](https://modelcontextprotocol.io/extensions/apps/overview)
- [Gemini API](https://ai.google.dev/gemini-api/docs)

The final harness lessons use our own local tool loop with Gemini instead of the reference's TrueForge service. They demonstrate harness integration, not a claimed TrueForge integration.
