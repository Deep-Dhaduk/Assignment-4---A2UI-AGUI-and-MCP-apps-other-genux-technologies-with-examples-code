"""Small native Gemini client. No OpenAI key, paid fallback, or automatic retries."""
import json
import os
from pathlib import Path
import httpx
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


class ProviderError(RuntimeError):
    pass


def settings():
    local = dotenv_values(ROOT / ".env")
    key = os.getenv("GEMINI_API_KEY") or local.get("GEMINI_API_KEY", "")
    model = os.getenv("MODEL") or local.get("MODEL") or "gemini-2.5-flash"
    if not model.replace("-", "").replace(".", "").isalnum():
        raise ProviderError("MODEL must be a Gemini model ID, not a URL.")
    return key, model


async def request(contents, system, *, tools=None, json_output=False):
    key, model = settings()
    if not key:
        raise ProviderError("Configure GEMINI_API_KEY in the local .env file first.")
    body = {"contents": contents, "systemInstruction": {"parts": [{"text": system}]},
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8192}}
    if tools:
        body["tools"] = [{"functionDeclarations": tools}]
    if json_output:
        body["generationConfig"]["responseMimeType"] = "application/json"
    async with httpx.AsyncClient(timeout=90) as client:
        try:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={"x-goog-api-key": key}, json=body,
            )
        except httpx.HTTPError:
            raise ProviderError("Could not reach Gemini. Check your connection and retry manually.") from None
    if response.status_code != 200:
        messages = {400: "Gemini rejected the request or model settings.",
                    403: "Gemini denied access. Check the key, region, and project permissions.",
                    404: "That model is unavailable. Choose a model with free quota in AI Studio.",
                    429: "Free-tier quota or rate limit reached. Wait and retry; no paid fallback was used."}
        raise ProviderError(messages.get(response.status_code, f"Gemini returned HTTP {response.status_code}."))
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates or candidates[0].get("finishReason") not in (None, "STOP"):
        raise ProviderError("Gemini returned an incomplete or blocked response. Try a smaller request.")
    return candidates[0]["content"], data.get("usageMetadata", {})


async def generate_document(prompt, theme, mode, attendees):
    from .domain import sample_plan
    from .representations import make_spec, openui_program
    example = sample_plan(attendees)
    spec = make_spec(example, mode)
    system = (
        "You design campus event interfaces. Return one JSON object, no fences. "
        "Include plan, spec, html, program. plan has title:string, attendees:integer (1..500), "
        "budget:number, venue:string, agenda:array of 1..6 strings, summary:string. "
        "Use only the supplied campus venues: Design Studio (40 seats), Learning Garden (100), "
        "Campus Auditorium (250). Avoid claiming any reservation. "
        "The spec must follow the example's {root,elements} structure. Allowed components and props: "
        "Panel(title:string, children at element level), Stat(label:string,value:string), "
        "Note(text:string), Agenda(items:string[]), Action(label:string,action:'add_attendees'), "
        "Sandbox(html:string). IDs are simple identifiers; all references must exist, no cycles. "
        "For static mode keep the example layout. For declarative mode compose the layout yourself. "
        "For open or mixed mode write a custom working ticket calculator in html, with inline CSS/JS, "
        "no network, no external assets, no forms navigating away. Put it in Sandbox as needed. "
        "For open/mixed, top-level html must contain that same complete HTML document, not an empty string. "
        "For other modes html is empty. program is OpenUI Lang using the same components; "
        "Panel takes (title, array of leaf component references); do not nest Panel inside Panel. "
        "Other positional arguments follow the order above. "
        "Use root = Panel(...) first. Write one statement per line. "
        f"\nExample plan: {example.model_dump_json()}\nExample spec: {json.dumps(spec)}"
        f"\nExample program: {openui_program(spec)}\nSelected theme: {theme}; mode: {mode}. "
        f"Attendance must be {attendees}."
    )
    content, usage = await request([{"role": "user", "parts": [{"text": prompt}]}], system, json_output=True)
    text = "".join(p.get("text", "") for p in content.get("parts", []) if not p.get("thought"))
    try:
        result = json.loads(text)
        if not isinstance(result, dict):
            raise ValueError()
    except ValueError:
        raise ProviderError("Gemini returned invalid JSON. No generated interface was executed.") from None
    return result, usage
