"""Heuristics that emulate AI-powered reasoning for the NPO assistant."""
from __future__ import annotations

from datetime import date
from typing import Iterable, List

from .models import Donor, ScheduleEntry


CONTACT_PRIORITY = {
    "in_person": 1,
    "phone": 2,
    "video": 3,
    "email": 4,
}


def _recent_interaction_age(donor: Donor, reference: date) -> int | None:
    if not donor.interactions:
        return None
    most_recent = max(interaction.date for interaction in donor.interactions)
    return (reference - most_recent).days


def generate_daily_todo(
    donors: Iterable[Donor],
    schedule: Iterable[ScheduleEntry],
    *,
    today: date | None = None,
) -> List[dict]:
    """Generate a list of priority tasks for the day."""

    today = today or date.today()

    schedule_today = [item for item in schedule if item.start.date() == today]
    tasks: List[dict] = []

    for entry in sorted(schedule_today, key=lambda item: item.start):
        donor = None
        if entry.donor:
            donor = next((d for d in donors if d.name == entry.donor), None)
        reason_parts = [f"Prepare for {entry.title}"]
        if donor:
            reason_parts.append(f"Donor {donor.name} prefers {donor.preferred_contact}")
            if donor.interests:
                reason_parts.append(f"Align talking points with interests: {', '.join(donor.interests[:3])}")
        if entry.location:
            reason_parts.append(f"Confirm location: {entry.location}")
        tasks.append(
            {
                "task": f"Prep: {entry.title}",
                "time": entry.start.strftime("%H:%M"),
                "reason": "; ".join(reason_parts),
            }
        )

    donors_without_recent_contact = [
        donor
        for donor in donors
        if _recent_interaction_age(donor, today) is None or _recent_interaction_age(donor, today) > 45
    ]

    donors_without_recent_contact.sort(
        key=lambda donor: (
            CONTACT_PRIORITY.get(donor.preferred_contact, 99),
            -len(donor.interests),
        )
    )

    for donor in donors_without_recent_contact[:3]:
        reason_parts = [
            "No interaction in the last 45 days"
            if _recent_interaction_age(donor, today)
            else "No recorded interactions yet",
            f"High interest areas: {', '.join(donor.interests[:3])}" if donor.interests else "",
            f"Preferred contact method: {donor.preferred_contact}",
        ]
        reason = "; ".join(part for part in reason_parts if part)
        tasks.append(
            {
                "task": f"Reach out to {donor.name}",
                "time": "flex",
                "reason": reason,
            }
        )

    if not tasks:
        tasks.append(
            {
                "task": "Review donor pipeline",
                "time": "flex",
                "reason": "No scheduled meetings today; review prospects and prepare outreach list.",
            }
        )

    return tasks


def plan_meeting(donor: Donor, *, meeting_date: date | None = None) -> dict:
    """Return a meeting strategy for the given donor."""

    meeting_date = meeting_date or date.today()
    interaction_age = _recent_interaction_age(donor, meeting_date)

    if donor.preferred_contact in {"coffee", "in_person"}:
        setting = "coffee meeting at a location they enjoy"
    elif donor.preferred_contact in {"video", "phone"}:
        setting = f"{donor.preferred_contact} call with a clear agenda"
    else:
        setting = "personalized email followed by a scheduling link"

    topics = list(donor.interests)
    if donor.notes:
        topics.append(donor.notes)
    if interaction_age and interaction_age > 180:
        topics.append("Re-engage by sharing organizational impact updates")
    elif interaction_age is None:
        topics.append("Introduce mission and learn about philanthropic interests")

    gift_ideas = []
    if donor.interests:
        gift_ideas.append(f"Bring a small token related to {donor.interests[0]}")
    if donor.last_gift_amount and donor.last_gift_amount > 5000:
        gift_ideas.append("Prepare a handwritten thank-you card highlighting recent impact")
    if not gift_ideas:
        gift_ideas.append("Bring branded stationery as a gratitude gesture")

    prep_steps = [
        "Review past interaction notes",
        "Outline 2-3 stories that show program impact",
    ]
    if donor.last_gift_date:
        prep_steps.append(
            f"Acknowledge their last gift on {donor.last_gift_date.strftime('%B %d, %Y')}"
        )
    if donor.preferred_contact == "email":
        prep_steps.append("Draft concise follow-up email template")

    follow_up = "Send a thank-you note within 24 hours"
    if donor.preferred_contact == "phone":
        follow_up += " and schedule a recap call"

    return {
        "meeting_format": setting,
        "discussion_topics": topics,
        "gift_ideas": gift_ideas,
        "pre_meeting_preparation": prep_steps,
        "follow_up_plan": follow_up,
    }


__all__ = ["generate_daily_todo", "plan_meeting"]
