"""Original UI representations for the same event, with an explicit catalog."""
import json
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal
from .domain import EventPlan


class StrictProps(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PanelProps(StrictProps):
    title: str = Field(max_length=150)


class StatProps(StrictProps):
    label: str = Field(max_length=80)
    value: str = Field(max_length=100)


class NoteProps(StrictProps):
    text: str = Field(max_length=1000)


class AgendaProps(StrictProps):
    items: list[str] = Field(max_length=8)


class ActionProps(StrictProps):
    label: str = Field(max_length=80)
    action: Literal["add_attendees"]


class SandboxProps(StrictProps):
    html: str = Field(max_length=30000)


PROPS = {"Panel": PanelProps, "Stat": StatProps, "Note": NoteProps,
         "Agenda": AgendaProps, "Action": ActionProps, "Sandbox": SandboxProps}


def validate_spec(spec):
    if not isinstance(spec, dict) or set(spec) != {"root", "elements"}:
        raise ValueError("A UI spec must contain exactly root and elements.")
    elements = spec["elements"]
    if not isinstance(elements, dict) or not 1 <= len(elements) <= 40:
        raise ValueError("Expected 1–40 elements.")
    if spec["root"] not in elements:
        raise ValueError("Root does not exist.")
    for ident, el in elements.items():
        if not isinstance(ident, str) or not ident.isidentifier() or ident in {"__proto__", "constructor", "prototype"}:
            raise ValueError("Element IDs must be simple identifiers.")
        if not isinstance(el, dict) or set(el) - {"type", "props", "children"}:
            raise ValueError("Invalid element fields.")
        name = el.get("type")
        if name not in PROPS:
            raise ValueError(f"Unknown component: {name}")
        PROPS[name].model_validate(el.get("props", {}))
        children = el.get("children", [])
        if not isinstance(children, list) or any(not isinstance(c, str) or c not in elements for c in children):
            raise ValueError("Children must reference existing elements.")
        if name != "Panel" and children:
            raise ValueError("Only Panel may contain children.")
    seen, stack = set(), set()

    def walk(ident, depth=0):
        if ident in stack or depth > 12:
            raise ValueError("Cyclic or overly deep UI graph.")
        stack.add(ident)
        seen.add(ident)
        for child in elements[ident].get("children", []):
            walk(child, depth + 1)
        stack.remove(ident)

    walk(spec["root"])
    if seen != set(elements):
        raise ValueError("Every element must be reachable from root.")
    return spec


def calculator_html(attendees=80):
    # This fixture is deliberately independent of the reference course's examples.
    return f"""<!doctype html><html><head><style>body{{font:16px system-ui;padding:20px;color:#173c36;background:#edf6ee}}input{{width:100%}}output{{font-size:32px;font-weight:700}}</style></head><body><h2>Ticket lab</h2><p>{attendees} attendees. Explore the ticket income.</p><label>Ticket price: <span id='price'>12</span> dollars<input id='slider' aria-label='Ticket price' type='range' min='0' max='30' value='12'></label><output id='income'>${attendees * 12}</output><script>document.getElementById('slider').addEventListener('input',e=>{{document.getElementById('price').textContent=e.target.value;document.getElementById('income').textContent='$'+(Number(e.target.value)*{attendees});parent.postMessage({{kind:'campus-preview',price:Number(e.target.value)}},'*')}})</script></body></html>"""


def make_spec(plan: EventPlan, mode="declarative", html=""):
    elements = {
        "event": {"type": "Panel", "props": {"title": plan.title}, "children": ["people", "money", "place", "agenda", "note", "add"]},
        "people": {"type": "Stat", "props": {"label": "Attendees", "value": str(plan.attendees)}},
        "money": {"type": "Stat", "props": {"label": "Budget", "value": f"${plan.budget:,.0f}"}},
        "place": {"type": "Stat", "props": {"label": "Venue", "value": plan.venue}},
        "agenda": {"type": "Agenda", "props": {"items": plan.agenda}},
        "note": {"type": "Note", "props": {"text": plan.summary}},
        "add": {"type": "Action", "props": {"label": "Add 10 attendees", "action": "add_attendees"}},
    }
    if mode in ("open", "mixed"):
        elements["custom"] = {"type": "Sandbox", "props": {"html": html or calculator_html(plan.attendees)}}
        elements["event"]["children"].append("custom")
    if mode == "open":
        elements = {"event": {"type": "Panel", "props": {"title": "Custom interface"}, "children": ["custom"]}, "custom": elements["custom"]}
    return validate_spec({"root": "event", "elements": elements})


def openui_program(spec):
    names = {spec["root"]: "root"}
    names.update({key: key for key in spec["elements"] if key != spec["root"]})
    order = [spec["root"]] + [key for key in spec["elements"] if key != spec["root"]]
    lines = []
    for key in order:
        el = spec["elements"][key]
        # JSON property order is arbitrary; OpenUI positional arguments are not.
        values = [json.dumps(el["props"][field], ensure_ascii=False) for field in PROPS[el["type"]].model_fields]
        if el["type"] == "Panel":
            values.append("[" + ", ".join(names[c] for c in el.get("children", [])) + "]")
        lines.append(f"{names[key]} = {el['type']}({', '.join(values)})")
    return "\n".join(lines)


def a2ui_messages(plan, surface_id="campus"):
    # v0.9, with structure and data delivered separately to the official Lit renderer.
    def envelope(name, body):
        return {"version": "v0.9", name: {"surfaceId": surface_id, **body}}
    components = [
        {"id": "root", "component": "Column", "children": ["heading", "venue", "attendance", "budget"]},
        {"id": "heading", "component": "Text", "text": {"path": "/title"}, "variant": "h2"},
        {"id": "venue", "component": "Text", "text": {"path": "/venue"}},
        {"id": "attendance", "component": "Text", "text": {"path": "/attendance"}},
        {"id": "budget", "component": "Text", "text": {"path": "/budget"}},
    ]
    return [
        envelope("createSurface", {"catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"}),
        envelope("updateComponents", {"components": components}),
        envelope("updateDataModel", {"path": "/", "value": {"title": plan.title, "venue": plan.venue,
                "attendance": f"{plan.attendees} attendees", "budget": f"Budget: ${plan.budget:,.0f}"}}),
    ]


def spec_to_a2ui(spec):
    """Translate our validated graph into native A2UI text/column components.

    HTML stays in a separate companion sandbox, never in the A2UI basic catalog.
    """
    validate_spec(spec)
    mapping = {key: ("root" if key == spec["root"] else "node_" + key) for key in spec["elements"]}
    components, values = [], {}
    for key, element in spec["elements"].items():
        ident = mapping[key]
        props = element["props"]
        if element["type"] == "Panel":
            heading = ident + "_heading"
            components.append({"id": ident, "component": "Column", "children": [heading] + [mapping[c] for c in element.get("children", [])]})
            components.append({"id": heading, "component": "Text", "text": {"path": "/" + heading}, "variant": "h2"})
            values[heading] = props["title"]
        else:
            if element["type"] == "Sandbox":
                text = "Custom interface appears in the companion sandbox below."
            elif element["type"] == "Agenda":
                text = " · ".join(props["items"])
            elif element["type"] == "Action":
                text = "Use the host's attendance action below this surface."
            else:
                text = " — ".join(str(v) for v in props.values())
            components.append({"id": ident, "component": "Text", "text": {"path": "/" + ident}})
            values[ident] = text
    return [
        {"version": "v0.9", "createSurface": {"surfaceId": "campus", "catalogId": "https://a2ui.org/specification/v0_9/catalogs/basic/catalog.json"}},
        {"version": "v0.9", "updateComponents": {"surfaceId": "campus", "components": components}},
        {"version": "v0.9", "updateDataModel": {"surfaceId": "campus", "path": "/", "value": values}},
    ]


def patches_for(spec):
    # Parent-before-child updates; incomplete maps are displayed only once references resolve.
    yield {"op": "add", "path": "/root", "value": spec["root"]}
    yield {"op": "add", "path": "/elements", "value": {}}
    for key, value in spec["elements"].items():
        yield {"op": "add", "path": f"/elements/{key}", "value": value}


def terminal_view(spec):
    validate_spec(spec)
    lines = []
    def draw(ident, level=0):
        el = spec["elements"][ident]
        props = el["props"]
        label = "[isolated HTML region]" if el["type"] == "Sandbox" else " | ".join(str(v) for v in props.values())
        lines.append("  " * level + el["type"] + ": " + label)
        for child in el.get("children", []):
            draw(child, level + 1)
    draw(spec["root"])
    return "\n".join(lines)
