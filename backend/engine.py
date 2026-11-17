"""Shared original pipeline, with per-lesson protocol demonstrations."""
import json
from uuid import uuid4
from pydantic import BaseModel, Field
from typing import Literal
from ag_ui.core import (RunStartedEvent, RunFinishedEvent, RunErrorEvent, CustomEvent,
                       TextMessageStartEvent, TextMessageContentEvent, TextMessageEndEvent,
                       StateSnapshotEvent, StateDeltaEvent, ToolCallStartEvent, ToolCallArgsEvent,
                       ToolCallEndEvent, ToolCallResultEvent)
from .curriculum import LESSONS
from .domain import EventPlan, sample_plan
from .representations import make_spec, validate_spec, calculator_html, openui_program, a2ui_messages, spec_to_a2ui, patches_for, terminal_view
from .gemini import generate_document
from .harness import run_tools


class RunRequest(BaseModel):
    lesson: str = "01.1"
    mode: Literal["static", "declarative", "open", "mixed"] = "static"
    source: Literal["fixture", "gemini"] = "fixture"
    prompt: str = Field(default="Plan a campus makers fair.", min_length=1, max_length=2000)
    attendees: int = Field(default=80, ge=1, le=500)


async def build_payload(body: RunRequest):
    lesson = LESSONS[body.lesson]
    trace, usage = [], {}
    if lesson["theme"] == "harness" or body.lesson == "02.3":
        trace = await run_tools(body.prompt, body.attendees, body.source == "gemini")
    if body.source == "gemini":
        prompt = body.prompt + ("\nVerified tool results: " + json.dumps(trace) if trace else "")
        document, usage = await generate_document(prompt, lesson["theme"], body.mode, body.attendees)
        plan = EventPlan.model_validate(document.get("plan"))
        if plan.attendees != body.attendees:
            raise ValueError("Generated attendance did not match the requested attendance.")
        html = document.get("html", "")
        if not isinstance(html, str) or len(html) > 30000:
            raise ValueError("Generated HTML is invalid or too large.")
        # Some models put the custom document only in the Sandbox props.
        # Accept that generated value after validating its graph; never use a fixture here.
        if body.mode in ("open", "mixed") and not html.strip():
            generated_spec = validate_spec(document.get("spec"))
            regions = [el["props"]["html"] for el in generated_spec["elements"].values()
                       if el["type"] == "Sandbox"]
            if len(regions) == 1:
                html = regions[0]
        if body.mode in ("open", "mixed") and not html.strip():
            raise ValueError("The model did not generate the requested custom region.")
        spec = make_spec(plan, body.mode, html) if body.mode in ("static", "open") else validate_spec(document.get("spec"))
        program = document.get("program", "") if lesson["theme"] == "openui" and body.mode != "static" else openui_program(spec)
        if not isinstance(program, str) or len(program) > 60000 or not program.strip():
            raise ValueError("Missing or oversized OpenUI program.")
    else:
        plan = sample_plan(body.attendees)
        html = calculator_html(body.attendees) if body.mode in ("open", "mixed") else ""
        spec = make_spec(plan, body.mode, html)
        program = openui_program(spec)
    a2ui = a2ui_messages(plan)
    if lesson["theme"] == "a2ui" and body.mode != "static" and body.lesson != "03.2":
        a2ui = spec_to_a2ui(spec)
    if body.lesson == "03.2":
        # Demonstrate a separate data-only update, not a second component declaration.
        a2ui[-1]["updateDataModel"]["value"]["attendance"] = "Attendance is loading…"
        a2ui.append({"version": "v0.9", "updateDataModel": {"surfaceId": "campus", "path": "/attendance", "value": f"{plan.attendees} attendees"}})
    return {"lesson": body.lesson, "theme": lesson["theme"], "mode": body.mode, "source": body.source,
            "plan": plan.model_dump(), "spec": spec, "html": html, "program": program, "a2ui": a2ui,
            "trace": trace, "usage": usage, "terminal": terminal_view(spec),
            "comparison": {"json_utf8_bytes": len(json.dumps(spec, ensure_ascii=False).encode()),
                           "openui_utf8_bytes": len(program.encode()), "measure": "UTF-8 bytes, not tokens or latency"}}


async def events(body):
    thread_id, run_id, message_id = "campus-session", str(uuid4()), str(uuid4())
    yield RunStartedEvent(thread_id=thread_id, run_id=run_id)
    try:
        payload = await build_payload(body)
        yield StateSnapshotEvent(snapshot={"attendees": body.attendees, "source": body.source})
        yield TextMessageStartEvent(message_id=message_id, role="assistant")
        # UI delivery stream: Gemini's generateContent finishes before these events start.
        for word in payload["plan"]["summary"].split():
            yield TextMessageContentEvent(message_id=message_id, delta=word + " ")
        yield TextMessageEndEvent(message_id=message_id)
        for tool in payload["trace"]:
            ident = str(uuid4())
            yield ToolCallStartEvent(tool_call_id=ident, tool_call_name=tool["name"], parent_message_id=message_id)
            yield ToolCallArgsEvent(tool_call_id=ident, delta=json.dumps(tool["arguments"]))
            yield ToolCallEndEvent(tool_call_id=ident)
            yield ToolCallResultEvent(message_id=str(uuid4()), tool_call_id=ident, content=json.dumps(tool["result"]), role="tool")
        if payload["theme"] == "a2ui":
            for message in payload["a2ui"]:
                yield CustomEvent(name="a2ui", value=message)
        if body.lesson == "04.2":
            for line in payload["program"].splitlines():
                yield CustomEvent(name="openui.line", value=line + "\n")
        if body.lesson == "05.2":
            for patch in patches_for(payload["spec"]):
                yield CustomEvent(name="spec.patch", value=patch)
        yield CustomEvent(name="campus.result", value=payload)
        yield RunFinishedEvent(thread_id=thread_id, run_id=run_id)
    except Exception as exc:
        # Provider errors are already sanitized; don't expose tracebacks or local configuration.
        from .gemini import ProviderError
        reason = str(exc) if isinstance(exc, ProviderError) else "Output validation failed. Inspect server tests or try a simpler prompt."
        yield RunErrorEvent(message=reason)
