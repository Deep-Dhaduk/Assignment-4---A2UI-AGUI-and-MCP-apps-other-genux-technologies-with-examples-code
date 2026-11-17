# Verification record

Status is based on local execution, not the screenshots or claims in the reference repository.

- Frontend bundle: built with the pinned npm dependencies.
- Python suite: **104 tests passed**, including 92 checkpoint/mode combinations and provider-boundary tests using injected responses.
- JavaScript transport/security suite: **4 tests passed**.
- Browser: **51 lesson/mode checks passed** (23 defaults plus four modes across seven sections), using installed Chrome. The MCP capacity-filter round trip, attendance action, and mobile overflow check also passed. Desktop and mobile screenshots were inspected.
- Live Gemini: **verified on November 8, 2026** with `gemini-2.5-flash`. Representative static, declarative, open-ended, and mixed outputs passed the application contract. The live harness called `find_venues`, `estimate_event`, and `render_event`. This is representative coverage, not 92 separate live generations.
- Saved live-output browser checks: **4 passed**, one per mode. The generated open-ended calculator responded to its slider. These browser checks replayed the actual saved model responses without additional provider calls; they were not fresh live browser requests.
- External MCP hosts: not verified. The included teaching host uses the real MCP SDK server.
- Videos: pending user recording and upload.
- Public app deployment: not performed. Source publication is recorded in the repository's Git history.

Reproduce with `python run.py test`, `npm test`, and (with the local server running) `.venv/Scripts/python.exe scripts/check_browser.py`.

The browser report and screenshots are local artifacts under `evidence/browser/`; they are not committed automatically. Offline tests do not prove that a Gemini account has quota, that every live prompt will generate a valid UI, or that a third-party MCP host supports this app.

## Failure found and fixed

The first full browser pass found that the MCP app's Filter venues form could not submit inside its sandbox, which intentionally does not permit forms. The control was changed to a button that explicitly calls the allowed host tool. The final browser pass verified that changing capacity from 80 to 150 returns only Campus Auditorium. The sandbox permissions were not expanded.

## Live generation findings

| Check | Result |
|---|---|
| 01.1 static | Gemini generated a Student Astronomy Evening plan; validated successfully. |
| 04.2 declarative | Gemini generated a component map and OpenUI program; the official OpenUI renderer displayed it. |
| 01.3 open-ended | Initially rejected because top-level `html` was empty. The actual generated HTML was present in a single Sandbox component. After the adapter fix, the saved response validated and the browser calculator worked. No new request was needed to revalidate that response. |
| 07.3 mixed / harness | Live tool calls and final mixed-mode output passed. The saved result rendered successfully in the browser. |

The adapter now accepts custom HTML from a single validated generated Sandbox when the duplicate top-level field is empty. It does not substitute fixture HTML. A regression test covers that distinction. The generation prompt also makes the top-level field requirement explicit.

Local live evidence is stored in ignored `artifacts/live/`. `scripts/check_live.py` is an opt-in provider test; `scripts/check_live_browser.py` renders those saved outputs without consuming more quota. Model output can vary between runs. Billing status cannot be verified by this application; the user must keep the project on Free Tier.
