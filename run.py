"""Windows-friendly entry point: python run.py [serve|test|doctor|terminal]."""
import argparse
import asyncio
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if VENV.exists() and Path(sys.executable).resolve() != VENV.resolve():
    raise SystemExit(subprocess.call([str(VENV), str(Path(__file__).resolve()), *sys.argv[1:]]))

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("command", nargs="?", default="serve", choices=["serve", "test", "doctor", "terminal"])
parser.add_argument("--port", type=int, default=8000)
args = parser.parse_args()
if args.command == "serve":
    import uvicorn
    if not (ROOT / "dist" / "app.js").exists():
        raise SystemExit("Run npm install and npm run build first.")
    os.environ["PORT"] = str(args.port)
    print(f"Campus GenUI Lab: http://127.0.0.1:{args.port} (offline fixtures selected by default)", flush=True)
    uvicorn.run("backend.main:app", host="127.0.0.1", port=args.port, log_level="warning")
elif args.command == "test":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "tests", "-q"], cwd=ROOT))
elif args.command == "doctor":
    from backend.gemini import settings
    key, model = settings()
    print("Python:", sys.version.split()[0])
    print("Gemini key:", "configured (hidden)" if key else "not configured")
    print("Model:", model)
    print("Browser bundle:", "ready" if (ROOT / "dist/app.js").exists() else "run npm run build")
    print("Billing status cannot be checked here. Keep the project on Free Tier in AI Studio.")
else:
    from backend.engine import RunRequest, build_payload
    result = asyncio.run(build_payload(RunRequest(lesson="05.3", mode="mixed")))
    print("OFFLINE FIXTURE — same spec as the browser\n")
    print(result["terminal"])
