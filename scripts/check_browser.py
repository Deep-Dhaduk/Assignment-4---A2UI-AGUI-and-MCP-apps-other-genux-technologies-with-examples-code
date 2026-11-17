"""Integration checks against a running local server; all requests use offline fixtures."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "browser"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.getenv("LAB_URL", "http://127.0.0.1:8000")
errors, results = [], []

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(BASE)
    page.get_by_role("button", name="Run checkpoint").wait_for()
    lessons = page.request.get(BASE + "/api/lessons").json()
    for lesson in lessons:
        page.locator('.nav-item').filter(has_text=lesson['id']).click()
        page.get_by_role('button', name='Run checkpoint').click()
        page.get_by_role('button', name='Run checkpoint').wait_for(timeout=30000)
        page.wait_for_function("document.querySelector('.result-state').textContent.includes('Offline fixture')", timeout=30000)
        if lesson['theme']=='mcp':
            frame=page.frame_locator('iframe[title="MCP campus venue app"]')
            frame.locator('#status').filter(has_text='matching venues').wait_for(timeout=20000)
        if lesson['theme']=='a2ui':
            page.locator('.a2ui-surface').get_by_text('Campus Makers Fair', exact=True).wait_for(timeout=15000)
        if lesson['theme']=='openui':
            page.locator('.event-panel h2').get_by_text('Campus Makers Fair', exact=True).wait_for(timeout=15000)
        alerts=page.get_by_role('alert').all_text_contents()
        if alerts: raise AssertionError(f"{lesson['id']}: {alerts}")
        if errors: raise AssertionError(f"{lesson['id']}: browser errors {errors}")
        results.append({"lesson":lesson['id'],"mode":lesson['mode'],"status":"passed"})
        print(f"{lesson['id']} {lesson['theme']}: passed",flush=True)
    # Exercise every mode across each technology, beyond each lesson's default mode.
    for ident in ['01.1','02.2','03.3','04.4','05.3','06.3','07.3']:
        page.locator('.nav-item').filter(has_text=ident).click()
        for mode in ['static','declarative','open','mixed']:
            page.locator(f'input[name="mode"][value="{mode}"]').check()
            page.get_by_role('button',name='Run checkpoint').click()
            page.get_by_role('button',name='Run checkpoint').wait_for(timeout=30000)
            page.wait_for_function("document.querySelector('.result-state').textContent.includes('Offline fixture')")
            if ident=='06.3':
                frame=page.frame_locator('iframe[title="MCP campus venue app"]')
                frame.locator('#status').filter(has_text='matching venues').wait_for(timeout=20000)
            else:
                page.locator('.output-body').wait_for()
            if page.get_by_role('alert').count(): raise AssertionError(page.get_by_role('alert').all_text_contents())
            if errors: raise AssertionError(errors)
            results.append({"lesson":ident,"mode":mode,"status":"passed"})
        print(f"{ident}: all four modes passed",flush=True)
    # Real app-to-host-to-MCP tool round trip.
    page.locator('.nav-item').filter(has_text='06.2').click()
    page.get_by_role('button',name='Run checkpoint').click()
    frame=page.frame_locator('iframe[title="MCP campus venue app"]')
    frame.locator('#status').filter(has_text='matching venues').wait_for()
    frame.locator('#people').fill('150')
    frame.get_by_role('button',name='Filter venues').click()
    frame.locator('#status').filter(has_text='1 matching venues').wait_for()
    assert frame.locator('#venues').inner_text().find('Campus Auditorium')>=0
    # Stateful UI action.
    page.locator('.nav-item').filter(has_text='02.2').click()
    page.get_by_role('button',name='Run checkpoint').click()
    page.get_by_role('button',name='Add 10 attendees').wait_for()
    page.get_by_role('button',name='Add 10 attendees').click()
    page.wait_for_function("document.querySelector('.stat strong').textContent==='90'")
    page.screenshot(path=str(OUT/'desktop.png'),full_page=True)
    page.set_viewport_size({"width":390,"height":844})
    page.screenshot(path=str(OUT/'mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
    browser.close()
report={"source":"offline fixtures", "checks":results,"browser_errors":errors,
        "mcp_capacity_filter":"passed", "state_action":"passed", "mobile_overflow":"passed"}
(OUT/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(f"PASS: {len(results)} lesson/mode checks, MCP interaction, state action, mobile layout.")
