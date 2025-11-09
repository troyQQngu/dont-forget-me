import json
from datetime import date
from pathlib import Path

import pytest

from npo_assistant.ai import generate_daily_todo, plan_meeting, reflect_on_meeting
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
            directive_note = " " + payload["directives"][0] if payload.get("directives") else ""
            return json.dumps(
                {
                    "tasks": [
                        {
                            "task": "Prep: Lunch with Alicia Gomez",
                            "time": "12:00",
                            "reason": "Coordinate agenda that highlights STEM programs Alicia cares about." + directive_note,
                            "related_donors": ["Alicia Gomez"],
                        },
                        {
                            "task": "Call Cara Lee",
                            "time": "15:00",
                            "reason": "No recent touchpoint; confirm interest in mentorship initiative.",
                            "related_donors": ["Cara Lee"],
                        },
                    ]
                }
            )
        if payload["request"] == "meeting_reflection":
            missed = payload.get("missed_questions", [])
            return json.dumps(
                {
                    "missed_opportunities": [
                        "You promised to share the mentorship pilot deck before Friday.",
                    ],
                    "follow_up_actions": [
                        "Email Alicia the mentorship deck with volunteer sign-up links.",
                        "Schedule a follow-up call next week to cover impact metrics.",
                    ],
                    "suggested_questions": missed
                    + [
                        "Ask whether her daughter would like to attend the summer robotics camp.",
                    ],
                    "updated_timeline": "Complete all follow-ups within 5 days to honor the pledge timeline.",
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
    tasks = generate_daily_todo(
        donors,
        schedule,
        today=date(2024, 3, 25),
        directives=["Focus on donors in Los Angeles"],
        llm=stub,
    )
    assert tasks[0]["task"] == "Prep: Lunch with Alicia Gomez"
    assert tasks[1]["task"] == "Call Cara Lee"
    assert tasks[0]["related_donors"] == ["Alicia Gomez"]
    assert "Los Angeles" in tasks[0]["reason"]
    assert stub.last_payload["schedule"]  # prompt contains schedule context
    assert stub.last_payload["directives"] == ["Focus on donors in Los Angeles"]


def test_plan_meeting_contains_expected_sections(sample_data):
    donors, _ = sample_data
    donor = next(item for item in donors if item.name == "Alicia Gomez")
    stub = StubLLM()
    plan = plan_meeting(
        donor,
        meeting_date=date(2024, 3, 25),
        objectives=["Confirm pledge timeline"],
        llm=stub,
    )
    assert plan["meeting_format"].startswith("coffee meeting")
    assert any("STEM" in topic for topic in plan["discussion_topics"])
    assert plan["follow_up_plan"].startswith("Send a thank-you email")
    assert stub.last_payload["fundraiser_objectives"] == ["Confirm pledge timeline"]


def test_reflect_on_meeting_highlights_missed_questions(sample_data):
    donors, _ = sample_data
    donor = next(item for item in donors if item.name == "Alicia Gomez")
    stub = StubLLM()
    summary = reflect_on_meeting(
        donor,
        meeting_notes="Discussed pledge milestones but forgot to ask about the gala attendance.",
        follow_up_horizon_days=5,
        missed_questions=["Clarify if Alicia prefers a site visit or virtual tour"],
        llm=stub,
    )
    assert "Email Alicia" in summary["follow_up_actions"][0]
    assert "Clarify" in summary["suggested_questions"][0]
    assert summary["updated_timeline"].startswith("Complete all follow-ups")
    assert stub.last_payload["follow_up_horizon_days"] == 5
