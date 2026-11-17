"""Opt-in live Gemini check. Saves generated output locally; never prints the key."""
import argparse
import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.engine import RunRequest, build_payload
from backend import engine
from backend.gemini import ProviderError, settings

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--lesson", default="01.1")
parser.add_argument("--mode", choices=["static", "declarative", "open", "mixed"], default="static")
parser.add_argument("--replay-document", type=Path, help="Revalidate a saved Gemini response without a new API call")
args = parser.parse_args()
destination = ROOT / "artifacts" / "live"
destination.mkdir(parents=True, exist_ok=True)
_, model = settings()
original_generate = engine.generate_document


async def capture_document(*args, **kwargs):
    if parser_args.replay_document:
        document = json.loads(parser_args.replay_document.read_text(encoding="utf-8"))
        usage = {}
    else:
        document, usage = await original_generate(*args, **kwargs)
    (destination / f"{parser_args.lesson}-{parser_args.mode}-document.json").write_text(
        json.dumps(document, indent=2), encoding="utf-8")
    return document, usage


parser_args = args
engine.generate_document = capture_document
report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(), "model": model,
          "lesson": args.lesson, "mode": args.mode, "source": "live Gemini"}
if args.replay_document:
    if args.lesson.startswith("07.") or args.lesson == "02.3":
        raise SystemExit("Replay is limited to lessons without a live tool loop.")
    report["source"] = "saved live Gemini response (no new API call)"
try:
    result = asyncio.run(build_payload(RunRequest(
        lesson=args.lesson, mode=args.mode, source="gemini", attendees=80,
        prompt="Plan a student astronomy evening for 80 attendees with a $1200 budget. "
               "Include a ticket-income calculator only if the selected mode needs custom HTML.")))
    report.update(status="passed", title=result["plan"]["title"], usage=result["usage"],
                  tool_calls=[t["name"] for t in result["trace"]])
    (destination / f"{args.lesson}-{args.mode}-payload.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
except ProviderError as error:
    report.update(status="provider_error", message=str(error))
except Exception as error:
    # The generated response is retained locally for diagnosis; credentials are never logged.
    key, _ = settings()
    detail = str(error).replace(key, "[redacted]") if key else str(error)
    report.update(status="validation_error", message=f"{type(error).__name__}: {detail[:400]}")
(destination / f"{args.lesson}-{args.mode}-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2), flush=True)
sys.exit(0 if report["status"] == "passed" else 1)
