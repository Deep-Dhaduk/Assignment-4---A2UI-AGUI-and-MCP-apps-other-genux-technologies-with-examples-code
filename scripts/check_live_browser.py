"""Render saved live Gemini responses without spending additional API quota.

The intercepted /api/run response is explicitly a playback, not a fresh live run.
MCP discovery/tool calls still execute against the local MCP server.
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "live"
BASE = "http://127.0.0.1:8000"
CASES = [("01.1", "static"), ("04.2", "declarative"), ("01.3", "open"), ("07.3", "mixed")]
results = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(BASE)
    page.get_by_role("button", name="Run checkpoint").wait_for()
    for lesson, mode in CASES:
        payload = json.loads((OUT / f"{lesson}-{mode}-payload.json").read_text(encoding="utf-8"))
        payload["session"] = f"saved-live-{lesson}"

        def playback(route):
            frames = [{"type": "RUN_STARTED", "threadId": "saved-live", "runId": lesson},
                      {"type": "CUSTOM", "name": "campus.result", "value": payload},
                      {"type": "RUN_FINISHED", "threadId": "saved-live", "runId": lesson}]
            route.fulfill(status=200, content_type="text/event-stream", body="".join("data: " + json.dumps(e) + "\n\n" for e in frames))

        page.route("**/api/run", playback)
        page.locator(".nav-item").filter(has_text=lesson).click()
        page.locator(f'input[name="mode"][value="{mode}"]').check()
        page.get_by_role("button", name="Run checkpoint").click()
        page.wait_for_function("document.querySelector('.result-state').textContent.includes('Gemini output')")
        page.wait_for_timeout(300)
        assert not errors, errors
        assert not page.get_by_role("alert").count(), page.get_by_role("alert").all_text_contents()
        if mode == "open":
            frame = page.frame_locator('iframe[title="Generated ticket calculator"]')
            slider = frame.locator('input[type="range"]')
            slider.wait_for()
            before = frame.locator("body").inner_text()
            slider.fill("17")
            slider.dispatch_event("input")
            assert frame.locator("body").inner_text() != before, "Generated calculator did not respond"
        page.evaluate("window.scrollTo(0,0)")
        page.screenshot(path=str(OUT / f"{lesson}-{mode}-browser.png"), full_page=True)
        page.unroute("**/api/run", playback)
        results.append({"lesson": lesson, "mode": mode, "status": "passed", "source": "saved live response playback"})
        print(f"{lesson} {mode}: saved live output rendered", flush=True)
    browser.close()
(OUT / "browser-report.json").write_text(json.dumps({"cases": results, "browser_errors": errors}, indent=2), encoding="utf-8")
