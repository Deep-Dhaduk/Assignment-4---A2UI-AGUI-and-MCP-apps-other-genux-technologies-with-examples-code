"""A new bounded agent loop; tools can inspect campus data but cannot book anything."""
import json
from . import gemini
from .domain import venues_for, estimate, sample_plan, EventPlan
from .representations import make_spec

TOOLS = [
    {"name": "find_venues", "description": "List campus venues with enough seats.",
     "parameters": {"type": "object", "properties": {"attendees": {"type": "integer"}}, "required": ["attendees"]}},
    {"name": "estimate_event", "description": "Calculate venue and materials cost; does not make a booking.",
     "parameters": {"type": "object", "properties": {"attendees": {"type": "integer"}, "venue_id": {"type": "string"}, "budget": {"type": "number"}}, "required": ["attendees", "venue_id", "budget"]}},
    {"name": "render_event", "description": "Validate an event plan and produce its UI component graph.",
     "parameters": {"type": "object", "properties": {
         "title": {"type": "string"}, "attendees": {"type": "integer"}, "budget": {"type": "number"},
         "venue": {"type": "string"}, "agenda": {"type": "array", "items": {"type": "string"}}, "summary": {"type": "string"}},
         "required": ["title", "attendees", "budget", "venue", "agenda", "summary"]}},
]


def execute(name, arguments):
    if name == "render_event":
        return make_spec(EventPlan.model_validate(arguments))
    if name == "find_venues" and set(arguments) == {"attendees"}:
        return venues_for(int(arguments["attendees"]))
    if name == "estimate_event" and set(arguments) == {"attendees", "venue_id", "budget"}:
        return estimate(int(arguments["attendees"]), arguments["venue_id"], float(arguments["budget"]))
    raise ValueError("Tool or argument set is not allowed.")


async def run_tools(prompt, attendees, live=False):
    trace = []
    if not live:
        calls = [("find_venues", {"attendees": attendees})]
        venues = venues_for(attendees)
        if venues:
            calls.append(("estimate_event", {"attendees": attendees, "venue_id": venues[0]["id"], "budget": 1200}))
        calls.append(("render_event", sample_plan(attendees).model_dump()))
        for name, args in calls:
            trace.append({"name": name, "arguments": args, "result": execute(name, args), "source": "scripted fixture"})
        return trace
    contents = [{"role": "user", "parts": [{"text": f"{prompt}\nAttendance: {attendees}. Use tools to check capacity and budget."}]}]
    for _ in range(3):
        content, usage = await gemini.request(contents,
            "You are a campus event planner. Find venues, estimate a viable venue's cost, call render_event, then summarize. "
            "You cannot book or purchase anything. Use only the declared tools.", tools=TOOLS)
        calls = [p["functionCall"] for p in content.get("parts", []) if "functionCall" in p]
        if not calls:
            return trace
        if len(calls) > 4:
            raise ValueError("Too many tools requested in one turn.")
        contents.append(content)  # Preserve provider signatures on multi-turn tool requests.
        responses = []
        for call in calls:
            name, args = call["name"], call.get("args", {})
            try:
                result = execute(name, args)
            except (ValueError, TypeError, KeyError) as exc:
                result = {"error": str(exc)}
            trace.append({"name": name, "arguments": args, "result": result, "source": "Gemini tool call"})
            responses.append({"functionResponse": {"name": name, "response": {"result": result}}})
        contents.append({"role": "user", "parts": responses})
    return trace
