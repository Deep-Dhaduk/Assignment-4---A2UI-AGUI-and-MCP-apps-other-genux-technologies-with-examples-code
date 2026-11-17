"""One local server for the original labs. Credentials never reach the browser."""
import asyncio
import json
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4
from typing import Literal
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from ag_ui.encoder import EventEncoder
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from .curriculum import lessons, LESSONS
from .engine import RunRequest, events
from .domain import EventPlan, venues_for
from .representations import make_spec, openui_program, a2ui_messages, calculator_html, terminal_view
from .gemini import settings
from .mcp_app import mcp, RESOURCE

ROOT = Path(__file__).resolve().parents[1]
SESSIONS = {}


@asynccontextmanager
async def lifespan(app):
    async with mcp.session_manager.run():
        yield


app = FastAPI(title="Campus GenUI Lab", lifespan=lifespan)
app.mount("/tools", mcp.streamable_http_app())
app.mount("/assets", StaticFiles(directory=ROOT / "dist", check_dir=False), name="assets")


@app.get("/")
def index():
    return FileResponse(ROOT / "web" / "index.html")


@app.get("/api/health")
def health():
    key, model = settings()
    return {"ok": True, "gemini_configured": bool(key), "model": model, "lessons": len(LESSONS)}


@app.get("/api/lessons")
def curriculum():
    return lessons()


@app.post("/api/run")
async def run(body: RunRequest):
    if body.lesson not in LESSONS:
        raise HTTPException(404, "Unknown lesson")
    encoder = EventEncoder()
    async def stream():
        async for event in events(body):
            if getattr(event, "name", None) == "campus.result":
                session = str(uuid4())
                event.value["session"] = session
                if len(SESSIONS) >= 100:
                    SESSIONS.pop(next(iter(SESSIONS)))
                SESSIONS[session] = event.value
            yield encoder.encode(event)
            await asyncio.sleep(0.025)  # teaching pace, explicitly not model-token latency
    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-store"})


class Action(BaseModel):
    session: str
    action: Literal["add_attendees"]


@app.post("/api/action")
def action(body: Action):
    previous = SESSIONS.get(body.session)
    if previous is None:
        raise HTTPException(404, "Session expired. Run the lesson again.")
    plan = EventPlan.model_validate(previous["plan"])
    if plan.attendees + 10 > 500:
        raise HTTPException(400, "Maximum attendance is 500.")
    plan.attendees += 10
    eligible = venues_for(plan.attendees)
    plan.venue = eligible[0]["name"] if eligible else "No campus venue has enough capacity"
    html = calculator_html(plan.attendees) if previous["mode"] in ("open", "mixed") else ""
    # Action is deterministic; no hidden model call. Generated layout is replaced with a known valid layout.
    spec = make_spec(plan, previous["mode"], html)
    updated = {**previous, "plan": plan.model_dump(), "html": html, "spec": spec,
               "program": openui_program(spec), "a2ui": a2ui_messages(plan), "terminal": terminal_view(spec),
               "action_note": "Attendance updated locally; layout rebuilt from the trusted catalog. No Gemini call."}
    SESSIONS[body.session] = updated
    return {"payload": updated, "events": [
        {"type": "STATE_DELTA", "delta": [{"op": "replace", "path": "/attendees", "value": plan.attendees}]},
        {"type": "CUSTOM", "name": "a2ui", "value": {"version": "v0.9", "updateDataModel": {
            "surfaceId": "campus", "path": "/attendance", "value": f"{plan.attendees} attendees"}}},
    ]}


@asynccontextmanager
async def mcp_session():
    # Fixed local endpoint: browser input cannot choose an arbitrary server.
    port = int(os.getenv("PORT", "8000"))
    async with streamable_http_client(f"http://127.0.0.1:{port}/tools/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


@app.get("/api/mcp/discover")
async def discover():
    async with mcp_session() as session:
        tools = await session.list_tools()
        resource = await session.read_resource(RESOURCE)
        return {"tools": tools.model_dump(by_alias=True), "resource": resource.model_dump(by_alias=True)}


class ToolRequest(BaseModel):
    name: Literal["campus_venues"] = "campus_venues"
    attendees: int = Field(default=80, ge=1, le=500)
    mode: Literal["static", "declarative", "open", "mixed"] = "static"
    custom_html: str = Field(default="", max_length=30000)


@app.post("/api/mcp/call")
async def call_tool(body: ToolRequest):
    async with mcp_session() as session:
        result = await session.call_tool(body.name, arguments=body.model_dump(exclude={"name"}))
        return result.model_dump(by_alias=True)
