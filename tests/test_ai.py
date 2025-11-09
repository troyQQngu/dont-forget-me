import json
from datetime import date
from pathlib import Path

import pytest

from npo_assistant.ai import generate_daily_todo, plan_meeting
from npo_assistant.data_loader import load_donors, load_schedule


class StubLLM:
    """Deterministic substitute for the real language model in tests."""

    def __init__(self) -> None:
        self.last_payload: dict | None = None
        self.calls: list[dict] = []

    def complete(self, messages, response_format=None):  # pragma: no cover - exercised via public APIs
        assert response_format == "json_object"
        payload = json.loads(messages[-1]["content"])
        self.last_payload = payload
        self.calls.append(payload)
        if payload["request"] == "daily_todo":
            return json.dumps(
                {
                    "tasks": [
                        {
                            "task": "Prep: Lunch with Alicia Gomez",
                            "time": "12:00",
                            "reason": "Coordinate agenda that highlights STEM programs Alicia cares about.",
                        },
                        {
                            "task": "Call Cara Lee",
                            "time": "15:00",
                            "reason": "No recent touchpoint; confirm interest in mentorship initiative.",
                        },
                    ]
                }
            )
        return json.dumps(
            {
                "meeting_format": "coffee meeting at Alicia's favorite café",
                "discussion_topics": [
                    "Celebrate the robotics showcase she sponsored",
                    "Preview upcoming STEM scholarship",
                    "Ask about new volunteering interests",
                ],
                "gift_ideas": ["Bring a STEM-themed thank-you card"],
                "pre_meeting_preparation": [
                    "Review Alicia's interaction notes",
                    "Gather impact metrics on STEM labs",
                ],
                "follow_up_plan": "Send a thank-you email within 24 hours with event photos.",
            }
        )


@pytest.fixture(scope="session")
def sample_data():
    root = Path(__file__).resolve().parents[1] / "data"
    donors = load_donors(root / "donors.json")
    schedule = load_schedule(root / "schedule.json")
    return donors, schedule


def test_generate_daily_todo_includes_schedule_tasks(sample_data):
    donors, schedule = sample_data
    stub = StubLLM()
    tasks = generate_daily_todo(donors, schedule, today=date(2024, 3, 25), llm=stub)
    assert tasks[0]["task"] == "Prep: Lunch with Alicia Gomez"
    assert tasks[1]["task"] == "Call Cara Lee"
    assert stub.last_payload["schedule"]  # prompt contains schedule context


def test_plan_meeting_contains_expected_sections(sample_data):
    donors, _ = sample_data
    donor = next(item for item in donors if item.name == "Alicia Gomez")
    stub = StubLLM()
    plan = plan_meeting(donor, meeting_date=date(2024, 3, 25), llm=stub)
    assert plan["meeting_format"].startswith("coffee meeting")
    assert any("STEM" in topic for topic in plan["discussion_topics"])
    assert plan["follow_up_plan"].startswith("Send a thank-you email")
