"""Utilities to load donor and schedule data from JSON files."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable, List

from .models import Donor, ScheduleEntry


def _read_json(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if "items" in payload:
        return payload["items"]
    raise ValueError(f"Unsupported JSON schema in {path}")


def load_donors(path: str | Path) -> List[Donor]:
    """Load donors from a JSON file."""

    path = Path(path)
    donors: List[Donor] = []
    for entry in _read_json(path):
        donors.append(Donor.from_dict(entry))
    return donors


def load_schedule(path: str | Path, *, week_of: date | None = None) -> List[ScheduleEntry]:
    """Load a schedule from JSON."""

    path = Path(path)
    schedule: List[ScheduleEntry] = []
    for entry in _read_json(path):
        schedule.append(ScheduleEntry.from_dict(entry))
    if week_of:
        return [item for item in schedule if item.start.date().isocalendar()[:2] == week_of.isocalendar()[:2]]
    return schedule


def find_donor(donors: Iterable[Donor], name: str) -> Donor | None:
    """Find a donor by name, case insensitive."""

    name = name.strip().lower()
    for donor in donors:
        if donor.name.lower() == name:
            return donor
    return None


__all__ = ["load_donors", "load_schedule", "find_donor"]
