"""Run the planning helpers offline using a stubbed language model."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from npo_assistant.ai import generate_daily_todo, plan_meeting, reflect_on_meeting
from npo_assistant.data_loader import load_donors, load_schedule


class StubLLM:
    """Simple stand-in that mimics the OpenAI client interface."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def complete(self, messages, response_format=None):
        assert response_format == "json_object"
        payload = json.loads(messages[-1]["content"])
        self.calls.append(payload)
        if payload["request"] == "daily_todo":
            directives = payload.get("directives", [])
            reason_suffix = f" Focus: {directives[0]}" if directives else ""
            return json.dumps(
                {
                    "tasks": [
                        {
                            "task": "Prep slides for lunch with Alicia Gomez",
                            "time": "09:00",
                            "reason": "Tailor the deck to Alicia's interest in STEM labs and mentorship." + reason_suffix,
                            "related_donors": ["Alicia Gomez"],
                        },
                        {
                            "task": "Send recap email to Cara Lee",
                            "time": "16:00",
                            "reason": "She prefers email follow-ups and hasn't heard from us this month.",
                            "related_donors": ["Cara Lee"],
                        },
                    ]
                }
            )
        if payload["request"] == "meeting_reflection":
            return json.dumps(
                {
                    "missed_opportunities": [
                        "Alicia asked for wine program updates tied to her pledge conditions.",
                    ],
                    "follow_up_actions": [
                        "Deliver the mentorship milestone checklist (items A, B, C) before next Wednesday.",
                        "Send curated wine education article as a thoughtful touchpoint.",
                    ],
                    "suggested_questions": payload.get("missed_questions", [])
                    + ["Confirm if Alicia will join the LA alumni mixer."],
                    "updated_timeline": "Block 30 minutes tomorrow to draft the follow-up email and checklist.",
                }
            )
        donor_name = payload["donor"]["name"]
        return json.dumps(
            {
                "meeting_format": "coffee meeting with {name} at their preferred café".format(name=donor_name),
                "discussion_topics": [
                    "Share impact metrics from the recent robotics showcase",
                    "Discuss upcoming mentorship kickoff",
                    "Ask about new focus areas for their philanthropy",
                ],
                "gift_ideas": ["Bring a handwritten thank-you card"],
                "pre_meeting_preparation": [
                    "Review past interactions and notes",
                    "Summarize last year's donation outcomes",
                ],
                "follow_up_plan": "Send meeting notes and volunteer sign-up links within 24 hours.",
            }
        )


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    donors = load_donors(data_dir / "donors.json")
    schedule = load_schedule(data_dir / "schedule.json")

    llm = StubLLM()
    tasks = generate_daily_todo(
        donors,
        schedule,
        today=date(2024, 3, 25),
        directives=["Prioritize donors currently in Los Angeles"],
        llm=llm,
    )
    donor = next(d for d in donors if d.name == "Alicia Gomez")
    meeting_plan = plan_meeting(
        donor,
        meeting_date=date(2024, 3, 25),
        objectives=[
            "Reconfirm $100k pledge once A/B/C milestones are shared",
            "Identify best venue for next stewardship touchpoint in LA",
        ],
        llm=llm,
    )
    reflection = reflect_on_meeting(
        donor,
        meeting_notes=(
            "Met after the robotics showcase. Covered mentorship expansion but forgot to ask about "
            "her daughter's alumni connections. Need to deliver the A/B/C action plan she tied to "
            "the $100k commitment."
        ),
        follow_up_horizon_days=4,
        missed_questions=["Confirm Alicia's preferred follow-up format for the action checklist"],
        llm=llm,
    )

    print("Daily to-do list:\n", json.dumps(tasks, indent=2))
    print("\nMeeting plan:\n", json.dumps(meeting_plan, indent=2))
    print("\nFollow-up summary:\n", json.dumps(reflection, indent=2))


if __name__ == "__main__":
    main()
