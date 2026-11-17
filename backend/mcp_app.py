"""Original MCP Apps server: resource discovery and a real capacity-filter tool."""
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from .domain import venues_for
from .representations import calculator_html

RESOURCE = "ui://campus/venue-explorer.html"
mcp = FastMCP("Campus Venue Explorer", stateless_http=True, json_response=True)


@mcp.resource(RESOURCE, mime_type="text/html;profile=mcp-app",
              meta={"ui": {"csp": {"connectDomains": [], "resourceDomains": []}}})
def app_resource() -> str:
    return (Path(__file__).resolve().parents[1] / "web" / "mcp-app.html").read_text(encoding="utf-8")


@mcp.tool(meta={"ui": {"resourceUri": RESOURCE, "visibility": ["model", "app"]}})
def campus_venues(attendees: int = 80, mode: str = "static", custom_html: str = "") -> dict:
    """Find campus venues by capacity and show the interactive venue app. Does not book venues."""
    if mode not in ("static", "declarative", "open", "mixed"):
        raise ValueError("Unknown UI mode.")
    if len(custom_html) > 30000:
        raise ValueError("Custom region is too large.")
    venues = venues_for(attendees)
    # The declarative mode returns a small layout description, separate from data.
    layout = {"component": "VenueList", "children": [{"component": "VenueCard", "venueId": venue["id"]} for venue in venues]}
    return {"attendees": attendees, "venues": venues, "layout": layout, "mode": mode,
            "html": (custom_html or calculator_html(attendees)) if mode in ("open", "mixed") else ""}
