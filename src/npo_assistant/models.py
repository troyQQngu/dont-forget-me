"""Data models for the NPO assistant domain."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional


@dataclass
class Interaction:
    """Represents a past interaction with a donor."""

    date: date
    type: str
    notes: str

    @classmethod
    def from_dict(cls, payload: dict) -> "Interaction":
        return cls(
            date=datetime.strptime(payload["date"], "%Y-%m-%d").date(),
            type=payload.get("type", "meeting"),
            notes=payload.get("notes", ""),
        )


@dataclass
class Donor:
    """Represents a donor or prospect."""

    name: str
    giving_capacity: str
    interests: List[str] = field(default_factory=list)
    preferred_contact: str = "email"
    last_gift_date: Optional[date] = None
    last_gift_amount: Optional[float] = None
    interactions: List[Interaction] = field(default_factory=list)
    notes: str = ""
    primary_city: Optional[str] = None
    time_zone: Optional[str] = None
    engagement_stage: Optional[str] = None
    strategic_objectives: List[str] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict) -> "Donor":
        interactions = [Interaction.from_dict(item) for item in payload.get("interactions", [])]
        last_gift_date = None
        if payload.get("last_gift_date"):
            last_gift_date = datetime.strptime(payload["last_gift_date"], "%Y-%m-%d").date()
        return cls(
            name=payload["name"],
            giving_capacity=payload.get("giving_capacity", "unknown"),
            interests=payload.get("interests", []),
            preferred_contact=payload.get("preferred_contact", "email"),
            last_gift_date=last_gift_date,
            last_gift_amount=payload.get("last_gift_amount"),
            interactions=interactions,
            notes=payload.get("notes", ""),
            primary_city=payload.get("primary_city"),
            time_zone=payload.get("time_zone"),
            engagement_stage=payload.get("engagement_stage"),
            strategic_objectives=payload.get("strategic_objectives", []),
            open_questions=payload.get("open_questions", []),
        )


@dataclass
class ScheduleEntry:
    """Represents a scheduled event for the staff member."""

    start: datetime
    end: datetime
    title: str
    donor: Optional[str] = None
    location: Optional[str] = None
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: dict) -> "ScheduleEntry":
        return cls(
            start=datetime.fromisoformat(payload["start"]),
            end=datetime.fromisoformat(payload["end"]),
            title=payload.get("title", "Meeting"),
            donor=payload.get("donor"),
            location=payload.get("location"),
            notes=payload.get("notes", ""),
        )


__all__ = ["Donor", "Interaction", "ScheduleEntry"]
