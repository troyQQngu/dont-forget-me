from datetime import date
from pathlib import Path

import pytest

from npo_assistant.ai import generate_daily_todo, plan_meeting
from npo_assistant.data_loader import load_donors, load_schedule


@pytest.fixture(scope="session")
def sample_data():
    root = Path(__file__).resolve().parents[1] / "data"
    donors = load_donors(root / "donors.json")
    schedule = load_schedule(root / "schedule.json")
    return donors, schedule


def test_generate_daily_todo_includes_schedule_tasks(sample_data):
    donors, schedule = sample_data
    tasks = generate_daily_todo(donors, schedule, today=date(2024, 3, 25))
    titles = [task["task"] for task in tasks]
    assert "Prep: Lunch with Alicia Gomez" in titles
    assert "Prep: Call with Cara Lee" in titles


def test_plan_meeting_contains_expected_sections(sample_data):
    donors, _ = sample_data
    donor = next(item for item in donors if item.name == "Alicia Gomez")
    plan = plan_meeting(donor, meeting_date=date(2024, 3, 25))
    assert plan["meeting_format"].startswith("coffee meeting")
    assert any("STEM" in topic for topic in plan["discussion_topics"])
    assert plan["follow_up_plan"].startswith("Send a thank-you note")
