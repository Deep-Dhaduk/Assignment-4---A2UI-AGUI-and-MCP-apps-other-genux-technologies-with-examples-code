import asyncio
import copy
import json
import pytest
from backend.curriculum import LESSONS
from backend.engine import RunRequest, build_payload, events
from backend.representations import validate_spec, make_spec, spec_to_a2ui
from backend.domain import sample_plan, venues_for, estimate
from backend.harness import execute


@pytest.mark.parametrize("lesson", list(LESSONS))
@pytest.mark.parametrize("mode", ["static", "declarative", "open", "mixed"])
def test_every_checkpoint_has_a_valid_offline_result(lesson, mode, monkeypatch):
    async def forbidden(*args, **kwargs):
        raise AssertionError("Offline fixtures must not call Gemini")
    monkeypatch.setattr("backend.gemini.request", forbidden)
    result = asyncio.run(build_payload(RunRequest(lesson=lesson, mode=mode)))
    assert result["source"] == "fixture"
    assert validate_spec(result["spec"])
    assert result["plan"]["attendees"] == 80
    assert result["program"].startswith("root = Panel(")
    assert bool(result["html"]) == (mode in ("open", "mixed"))
    assert result["a2ui"][0]["createSurface"]["surfaceId"] == "campus"
    assert "Panel:" in result["terminal"]


def test_event_lifecycle_and_real_tool_result():
    async def collect():
        return [e.model_dump(mode="json", by_alias=True) async for e in events(RunRequest(lesson="07.1"))]
    rows = asyncio.run(collect())
    assert rows[0]["type"] == "RUN_STARTED"
    assert rows[-1]["type"] == "RUN_FINISHED"
    starts = [e for e in rows if e["type"] == "TOOL_CALL_START"]
    results = [e for e in rows if e["type"] == "TOOL_CALL_RESULT"]
    assert {e["toolCallId"] for e in starts} == {e["toolCallId"] for e in results}
    assert json.loads(results[1]["content"])["remaining"] == 400


def test_unknown_component_missing_child_and_cycle_rejected():
    for defect in ("type", "child", "cycle"):
        spec = copy.deepcopy(make_spec(sample_plan()))
        if defect == "type": spec["elements"]["people"]["type"] = "script"
        if defect == "child": spec["elements"]["event"]["children"].append("missing")
        if defect == "cycle": spec["elements"]["event"]["children"].append("event")
        with pytest.raises(ValueError): validate_spec(spec)


def test_native_a2ui_graph_uses_declared_ids():
    messages = spec_to_a2ui(make_spec(sample_plan(), "mixed"))
    components = messages[1]["updateComponents"]["components"]
    ids = {c["id"] for c in components}
    assert "root" in ids
    assert all(child in ids for c in components for child in c.get("children", []))
    assert all(c["component"] in ("Column", "Text") for c in components)


def test_capacity_and_tool_allowlist():
    assert [v["id"] for v in venues_for(101)] == ["auditorium"]
    assert venues_for(300) == []
    with pytest.raises(ValueError): estimate(80, "studio")
    with pytest.raises(ValueError): execute("book_venue", {"attendees": 80})
    with pytest.raises(ValueError): execute("find_venues", {"attendees": 80, "command": "anything"})


def test_failure_is_terminal_and_redacted(monkeypatch):
    async def fail(*args, **kwargs): raise RuntimeError("SECRET_TOKEN")
    monkeypatch.setattr("backend.engine.build_payload", fail)
    async def collect(): return [e.model_dump(mode="json", by_alias=True) async for e in events(RunRequest())]
    rows = asyncio.run(collect())
    assert rows[-1]["type"] == "RUN_ERROR"
    assert "SECRET_TOKEN" not in json.dumps(rows)
    assert not any(r["type"] == "RUN_FINISHED" for r in rows)
