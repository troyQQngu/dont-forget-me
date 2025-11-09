"""AI-powered routines for the NPO assistant."""
from __future__ import annotations

import json
from datetime import date
from typing import Iterable, List, Optional, Sequence

from .llm import LLMClient, OpenAIChatClient
from .models import Donor, ScheduleEntry


TODO_SYSTEM_PROMPT = (
    "You are an assistant helping a nonprofit relationship manager prioritize outreach. "
    "Always answer with valid JSON matching the schema: {\"tasks\": [{\"task\": string, "
    "\"time\": string, \"reason\": string, \"related_donors\": [string]}]}. "
    "Use the information provided—especially donor notes, strategic objectives, and the "
    "user's directives—to explain why each task matters."
)

MEETING_SYSTEM_PROMPT = (
    "You advise nonprofit fundraisers on donor meetings. Always respond with valid "
    "JSON matching the schema: {\"meeting_format\": string, \"discussion_topics\": "
    "[string], \"gift_ideas\": [string], \"pre_meeting_preparation\": [string], "
    "\"follow_up_plan\": string}. If an event description is provided, ground the plan "
    "in that context and offer event-specific strategies."
)

REFLECTION_SYSTEM_PROMPT = (
    "You review donor meeting recaps for a nonprofit fundraiser and recommend follow-up. "
    "Always answer with valid JSON matching the schema: {\"missed_opportunities\": "
    "[string], \"follow_up_actions\": [string], \"suggested_questions\": [string], "
    "\"updated_timeline\": string}. Ground every suggestion in the donor notes, the "
    "meeting summary, and any explicit next-step requests."
)


def _default_llm(llm: Optional[LLMClient]) -> LLMClient:
    if llm is not None:
        return llm
    return OpenAIChatClient()


def _serialize_donor(donor: Donor) -> dict:
    return {
        "name": donor.name,
        "giving_capacity": donor.giving_capacity,
        "interests": donor.interests,
        "preferred_contact": donor.preferred_contact,
        "last_gift_date": donor.last_gift_date.isoformat() if donor.last_gift_date else None,
        "last_gift_amount": donor.last_gift_amount,
        "notes": donor.notes,
        "primary_city": donor.primary_city,
        "time_zone": donor.time_zone,
        "engagement_stage": donor.engagement_stage,
        "status": donor.status,
        "strategic_objectives": donor.strategic_objectives,
        "open_questions": donor.open_questions,
        "interactions": [
            {
                "date": interaction.date.isoformat(),
                "type": interaction.type,
                "notes": interaction.notes,
            }
            for interaction in donor.interactions
        ],
    }


def _serialize_schedule(entry: ScheduleEntry) -> dict:
    return {
        "start": entry.start.isoformat(),
        "end": entry.end.isoformat(),
        "title": entry.title,
        "donor": entry.donor,
        "location": entry.location,
        "notes": entry.notes,
    }


def _complete_json(llm: LLMClient, *, system: str, payload: dict) -> dict:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, indent=2)},
    ]
    response_text = llm.complete(messages, response_format="json_object")
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as exc:
        raise ValueError("LLM response was not valid JSON") from exc


def generate_daily_todo(
    donors: Iterable[Donor],
    schedule: Iterable[ScheduleEntry],
    *,
    today: date | None = None,
    directives: Optional[Sequence[str]] = None,
    llm: Optional[LLMClient] = None,
) -> List[dict]:
    """Generate a prioritized to-do list for the specified day using an LLM."""

    today = today or date.today()
    llm_client = _default_llm(llm)

    schedule_today = [
        _serialize_schedule(item)
        for item in schedule
        if item.start.date() == today
    ]
    serialized_donors = [_serialize_donor(donor) for donor in donors]
    directive_list = list(directives or [])

    payload = {
        "request": "daily_todo",
        "date": today.isoformat(),
        "schedule": schedule_today,
        "donors": serialized_donors,
        "guidelines": [
            "Highlight why the task matters for relationship building.",
            "Respect each donor's preferred contact method when suggesting outreach.",
            "Call out preparation steps for meetings scheduled today.",
            "Prioritize any promises, deadlines, or follow-ups captured in the donor notes.",
            "Match donors to the fundraiser's directives (location focus, reconnecting, or "
            "disqualifying).",
        ],
        "directives": directive_list,
    }

    response = _complete_json(llm_client, system=TODO_SYSTEM_PROMPT, payload=payload)
    tasks = response.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("LLM response missing 'tasks' list")
    return tasks


def plan_meeting(
    donor: Donor,
    *,
    meeting_date: date | None = None,
    objectives: Optional[Sequence[str]] = None,
    event: str | None = None,
    llm: Optional[LLMClient] = None,
) -> dict:
    """Create a meeting strategy for ``donor`` with the help of an LLM."""

    meeting_date = meeting_date or date.today()
    llm_client = _default_llm(llm)

    payload = {
        "request": "meeting_plan",
        "meeting_date": meeting_date.isoformat(),
        "donor": _serialize_donor(donor),
        "expectations": [
            "Tailor the meeting format to the donor's preferred contact style.",
            "Suggest specific talking points grounded in the donor profile.",
            "Recommend thoughtful but realistic stewardship gestures.",
            "Address any open questions or strategic objectives referenced in the notes.",
        ],
    }
    if objectives:
        payload["fundraiser_objectives"] = list(objectives)
    if event:
        payload["event"] = event

    response = _complete_json(llm_client, system=MEETING_SYSTEM_PROMPT, payload=payload)
    required_keys = {
        "meeting_format",
        "discussion_topics",
        "gift_ideas",
        "pre_meeting_preparation",
        "follow_up_plan",
    }
    missing = [key for key in required_keys if key not in response]
    if missing:
        raise ValueError(f"LLM response missing keys: {', '.join(missing)}")
    return response


def reflect_on_meeting(
    donor: Donor,
    *,
    meeting_notes: str,
    follow_up_horizon_days: int = 7,
    missed_questions: Optional[Sequence[str]] = None,
    llm: Optional[LLMClient] = None,
) -> dict:
    """Summarize next steps after a meeting and surface any missed questions."""

    llm_client = _default_llm(llm)
    payload = {
        "request": "meeting_reflection",
        "donor": _serialize_donor(donor),
        "meeting_notes": meeting_notes,
        "follow_up_horizon_days": follow_up_horizon_days,
        "missed_questions": list(missed_questions or []),
        "expectations": [
            "Highlight commitments or requests mentioned during the meeting or in donor notes.",
            "Propose concrete follow-up actions to keep momentum.",
            "Remind the fundraiser to address unanswered questions or gaps.",
        ],
    }

    response = _complete_json(
        llm_client,
        system=REFLECTION_SYSTEM_PROMPT,
        payload=payload,
    )
    required = {"missed_opportunities", "follow_up_actions", "suggested_questions", "updated_timeline"}
    missing = [key for key in required if key not in response]
    if missing:
        raise ValueError(f"LLM response missing keys: {', '.join(missing)}")
    return response


__all__ = ["generate_daily_todo", "plan_meeting", "reflect_on_meeting"]
