"""Provider boundaries are tested with injected replies; no account or quota is used."""
import asyncio
import json
import pytest
from backend import gemini
from backend.engine import RunRequest, build_payload
from backend.domain import sample_plan
from backend.representations import make_spec, openui_program, validate_spec


def test_live_generation_uses_prompt_and_validates_output(monkeypatch):
    seen = []
    async def reply(contents, system, **options):
        seen.append(contents)
        plan = sample_plan()
        plan.title = "Student Astronomy Night"
        spec = make_spec(plan)
        document = {"plan": plan.model_dump(), "spec": spec, "html": "", "program": openui_program(spec)}
        return {"parts": [{"text": json.dumps(document)}]}, {"totalTokenCount": 42}
    monkeypatch.setattr(gemini, "request", reply)
    result = asyncio.run(build_payload(RunRequest(source="gemini", mode="declarative", prompt="Organize an astronomy night.")))
    assert "astronomy" in seen[0][0]["parts"][0]["text"]
    assert result["plan"]["title"] == "Student Astronomy Night"
    assert result["source"] == "gemini"
    assert result["usage"]["totalTokenCount"] == 42


def test_invalid_model_json_is_not_silently_replaced(monkeypatch):
    async def bad_reply(*args, **kwargs):
        return {"parts": [{"text": "not json"}]}, {}
    monkeypatch.setattr(gemini, "request", bad_reply)
    with pytest.raises(gemini.ProviderError, match="invalid JSON"):
        asyncio.run(build_payload(RunRequest(source="gemini")))


def test_openui_property_order_is_canonical():
    spec = make_spec(sample_plan())
    spec["elements"]["people"]["props"] = {"value": "80", "label": "Attendees"}
    assert 'people = Stat("Attendees", "80")' in openui_program(spec)


def test_unsafe_element_identifier_is_rejected():
    spec = make_spec(sample_plan())
    spec["elements"]["__proto__"] = spec["elements"].pop("people")
    spec["elements"]["event"]["children"][0] = "__proto__"
    with pytest.raises(ValueError, match="identifiers"):
        validate_spec(spec)


def test_custom_html_can_be_read_from_valid_generated_sandbox(monkeypatch):
    from backend.representations import calculator_html
    generated_html = "<!doctype html><h1>Model-authored test document</h1>"
    plan = sample_plan()
    spec = make_spec(plan, "open", generated_html)
    async def reply(*args, **kwargs):
        document = {"plan": plan.model_dump(), "spec": spec, "html": "", "program": openui_program(spec)}
        return {"parts": [{"text": json.dumps(document)}]}, {}
    monkeypatch.setattr(gemini, "request", reply)
    result = asyncio.run(build_payload(RunRequest(source="gemini", mode="open")))
    assert result["html"] == generated_html
    assert result["html"] != calculator_html()
