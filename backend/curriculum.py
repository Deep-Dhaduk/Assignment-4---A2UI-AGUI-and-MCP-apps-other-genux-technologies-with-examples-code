"""The original exercises: each checkpoint adds an observable capability."""

THEMES = [
    ("foundations", "01", "Foundations", [
        ("Fixed event cards", "static", "Select a predefined card and populate its values.", "Show two campus workshops within a $1,200 budget."),
        ("A layout from data", "declarative", "Inspect the component map, then change the order of its children.", "Arrange attendance and budget metrics above an event agenda."),
        ("An interactive calculator", "open", "Generate a self-contained ticket calculator inside an isolated frame.", "Build a ticket calculator for 80 students at $12 per ticket."),
        ("Combine both approaches", "mixed", "Keep the plan in trusted components and add a custom calculator.", "Plan a makers fair and add a ticket calculator."),
    ]),
    ("agui", "02", "AG-UI", [
        ("Observe the run lifecycle", "static", "Find RUN_STARTED, message deltas, and RUN_FINISHED in the event trace.", "Summarize a campus sustainability fair."),
        ("Synchronize attendance", "declarative", "Apply a STATE_SNAPSHOT followed by a STATE_DELTA when attendance changes.", "Plan a sustainability fair for 80 students."),
        ("Tool calls become UI", "mixed", "Trace a tool call through its arguments, result, and rendered output.", "Choose a venue for 80 students and calculate the remaining budget."),
    ]),
    ("a2ui", "03", "A2UI", [
        ("A surface by hand", "static", "Read createSurface and updateComponents in the protocol panel.", "Show the campus event summary."),
        ("Bind data to components", "declarative", "Update attendance through updateDataModel without rebuilding the component graph.", "Create a compact event summary with attendance and budget."),
        ("A2UI carried by AG-UI", "mixed", "Find each A2UI envelope inside an AG-UI CUSTOM event.", "Build an event summary with an interactive ticket calculator."),
    ]),
    ("openui", "04", "OpenUI", [
        ("Read a UI program", "static", "Follow named statements and references in the OpenUI program.", "Show a simple event brief."),
        ("Stream a component library", "declarative", "Watch forward references resolve in the official React renderer.", "Create a compact dashboard for a student makers fair."),
        ("Compare representations", "declarative", "Measure UTF-8 bytes for the same facts in JSON and OpenUI; do not call these token counts.", "Compare the same event summary in two UI formats."),
        ("A custom OpenUI component", "mixed", "Inspect the custom Sandbox component in the library and its isolated content.", "Add a ticket-price calculator beside the event brief."),
    ]),
    ("jsonrender", "05", "json-render", [
        ("Validate a component catalog", "declarative", "Match the generated element types to the Zod catalog and React registry.", "Create an event budget dashboard."),
        ("Build with patches", "declarative", "Reconstruct the element map using incremental RFC 6902 add operations.", "Build the event dashboard progressively."),
        ("Actions and a second target", "mixed", "Update attendance, then render the same validated spec in a terminal.", "Show the event dashboard with an attendance action and calculator."),
    ]),
    ("mcp", "06", "MCP Apps", [
        ("Discover an app resource", "static", "List tools, follow _meta.ui.resourceUri, and read the UI resource over MCP.", "Open the campus venue explorer."),
        ("Interact through a host", "declarative", "Use the embedded app to call the capacity filter through the host bridge.", "Find campus venues for 80 attendees."),
        ("An app with a custom region", "mixed", "Combine the MCP tool result with a nested calculator frame.", "Show venues and an interactive event cost calculator."),
    ]),
    ("harness", "07", "Harness integration", [
        ("Search, estimate, render", "static", "Observe the bounded tool loop: venue lookup, budget estimate, and final UI.", "Find a venue for 80 students with a $1,200 budget."),
        ("Choose a representation", "declarative", "Connect a local agent tool loop to a validated UI spec.", "Plan a campus makers fair and show a dashboard."),
        ("Keep a human in the loop", "mixed", "Change attendance and rerun the planner; no venue is actually booked.", "Plan the fair, then include an interactive ticket calculator."),
    ]),
]


def lessons():
    result = []
    for theme, number, title, steps in THEMES:
        for index, (name, mode, objective, prompt) in enumerate(steps, 1):
            result.append(dict(id=f"{number}.{index}", theme=theme, section=title,
                               title=name, mode=mode, objective=objective, prompt=prompt))
    return result


LESSONS = {item["id"]: item for item in lessons()}
