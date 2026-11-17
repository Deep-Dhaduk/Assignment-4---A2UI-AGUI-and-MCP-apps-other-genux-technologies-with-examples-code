"""Campus-only sample data and deterministic calculations, independent of AI."""
from pydantic import BaseModel, ConfigDict, Field


class EventPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=100)
    attendees: int = Field(ge=1, le=500)
    budget: float = Field(ge=0, le=100000)
    venue: str = Field(min_length=1, max_length=100)
    agenda: list[str] = Field(min_length=1, max_length=6)
    summary: str = Field(max_length=500)


VENUES = [
    {"id": "studio", "name": "Design Studio", "capacity": 40, "cost": 150},
    {"id": "garden", "name": "Learning Garden", "capacity": 100, "cost": 320},
    {"id": "auditorium", "name": "Campus Auditorium", "capacity": 250, "cost": 650},
]


def venues_for(attendees: int):
    if not 1 <= attendees <= 500:
        raise ValueError("Attendance must be between 1 and 500.")
    return [venue.copy() for venue in VENUES if venue["capacity"] >= attendees]


def estimate(attendees: int, venue_id: str, budget: float = 1200):
    venue = next((v for v in VENUES if v["id"] == venue_id), None)
    if venue is None or not 1 <= attendees <= venue["capacity"]:
        raise ValueError("Unknown venue or insufficient capacity.")
    cost = venue["cost"] + attendees * 6
    return {"venue": venue["name"], "cost": cost, "remaining": round(budget - cost, 2)}


def sample_plan(attendees=80):
    venues = venues_for(attendees)
    return EventPlan(title="Campus Makers Fair", attendees=attendees, budget=1200,
                     venue=venues[0]["name"] if venues else "Venue search required",
                     agenda=["Welcome & project pitches", "Build together", "Student showcase"],
                     summary="An afternoon for students to share ideas and build something useful.")
