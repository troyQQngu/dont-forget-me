"""Interactive offline demo that exercises the assistant workflows with a stubbed LLM."""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from textwrap import dedent

from npo_assistant.ai import generate_daily_todo, plan_meeting, reflect_on_meeting
from npo_assistant.data_loader import find_donor, load_donors, load_schedule


class DemoStubLLM:
    """Deterministic stand-in for the OpenAI client used by the offline demo."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    # pylint: disable=too-many-branches
    def complete(self, messages, response_format=None):  # pragma: no cover - exercised via script
        assert response_format == "json_object"
        payload = json.loads(messages[-1]["content"])
        self.calls.append(payload)
        request = payload.get("request")
        if request == "daily_todo":
            return json.dumps(self._daily_todo(payload))
        if request == "meeting_plan":
            return json.dumps(self._meeting_plan(payload))
        if request == "meeting_reflection":
            return json.dumps(self._meeting_reflection(payload))
        raise ValueError(f"Unsupported request type: {request}")

    # pylint: disable=too-many-locals, too-many-branches
    def _daily_todo(self, payload: dict) -> dict:
        donors = payload["donors"]
        schedule = payload.get("schedule", [])
        directives = [item.lower() for item in payload.get("directives", [])]
        today = datetime.fromisoformat(payload["date"]).date()

        slot_order = ["08:00", "09:30", "10:45", "12:15", "14:00", "15:30", "16:45", "17:30"]
        tasks: list[dict] = []
        added_tasks: set[str] = set()

        def add_task(task: str, reason: str, related: list[str]) -> None:
            if task in added_tasks:
                return
            index = min(len(tasks), len(slot_order) - 1)
            tasks.append(
                {
                    "task": task,
                    "time": slot_order[index],
                    "reason": reason,
                    "related_donors": related,
                }
            )
            added_tasks.add(task)

        donors_by_name = {donor["name"]: donor for donor in donors}
        la_focus = any("los angeles" in d or " la" in d for d in directives)
        reconnect_focus = any("haven't talked" in d or "catch up" in d for d in directives)
        disqualify_focus = any("disqualify" in d or "stop engaging" in d or "too long" in d for d in directives)

        # Always elevate Alicia's pledged deliverables when present in the notes.
        alicia = donors_by_name.get("Alicia Gomez")
        if alicia and "mentor background checks" in alicia.get("notes", "").lower():
            add_task(
                "Complete mentor background checks for the mentorship pilot",
                (
                    "Alicia tied her $100k commitment to seeing these background checks completed before next week. "
                    "Finish the clearance paperwork and confirm every mentor is approved."
                ),
                ["Alicia Gomez"],
            )
            add_task(
                "Finalize the mentor-mentee matching roster",
                (
                    "Alicia wants the matching roster to review pairings before she signs the $100k gift. "
                    "Tighten the roster and flag any gaps in STEM representation."
                ),
                ["Alicia Gomez"],
            )
            add_task(
                "Publish the mentorship progress dashboard",
                (
                    "Without the updated dashboard Alicia can't verify impact. Ship the metrics summary so the pledge can clear "
                    "by next week."
                ),
                ["Alicia Gomez"],
            )

        # Tie in scheduled meetings for the day.
        for entry in schedule:
            start = datetime.fromisoformat(entry["start"]).date()
            if start != today:
                continue
            donor_name = entry.get("donor")
            if donor_name:
                reason = (
                    f"Prep for {entry['title']} at {entry.get('location', 'the scheduled venue')}. "
                    f"Use the agenda notes: {entry.get('notes', 'Review donor priorities.')}"
                )
                add_task(f"Prep briefing for {donor_name}", reason, [donor_name])
            else:
                add_task(
                    f"Prepare for {entry['title']}",
                    "Gather the required program updates so every donor follow-up stays accurate.",
                    [],
                )

        def last_interaction_days(donor: dict) -> int | None:
            latest = None
            for interaction in donor.get("interactions", []):
                try:
                    dt = datetime.fromisoformat(interaction["date"]).date()
                except ValueError:
                    continue
                latest = dt if latest is None or dt > latest else latest
            if latest is None:
                return None
            return (today - latest).days

        if la_focus:
            la_donors = [
                donor
                for donor in donors
                if donor.get("primary_city")
                and any(city in donor["primary_city"].lower() for city in ("los angeles", "pasadena"))
            ]
            for donor in la_donors:
                add_task(
                    f"Schedule Los Angeles touchpoint with {donor['name']}",
                    (
                        f"Directive: prioritize LA meetings. {donor['name']} can meet locally, so coordinate a coffee or site "
                        "visit while you're in town."
                    ),
                    [donor["name"]],
                )

        if reconnect_focus:
            for donor in donors:
                gap = last_interaction_days(donor)
                if gap is not None and gap > 60:
                    add_task(
                        f"Reconnect with {donor['name']}",
                        (
                            f"Directive: revive dormant relationships. It's been {gap} days since the last touchpoint with "
                            f"{donor['name']}; send a tailored update to restart the conversation."
                        ),
                        [donor["name"]],
                    )
                if gap is None:
                    add_task(
                        f"Introduce yourself to {donor['name']}",
                        (
                            "Directive: find contacts you haven't spoken with yet. There's no prior interaction logged, so send "
                            f"a welcome message to {donor['name']}."
                        ),
                        [donor["name"]],
                    )

        if disqualify_focus:
            for donor in donors:
                notes = donor.get("notes", "").lower()
                stalled = "prefers fewer" in notes or "not ready" in notes or donor.get("engagement_stage") == "qualification"
                if stalled:
                    add_task(
                        f"Assess fit of {donor['name']}",
                        (
                            f"Directive: identify prospects to pause. {donor['name']} has signaled limited interest recently—"
                            "review whether continued outreach adds value or if you should disqualify for now."
                        ),
                        [donor["name"]],
                    )

        if not tasks:
            add_task(
                "Review donor database",
                "No directives matched specific actions today—scan the database for emerging opportunities.",
                [],
            )
        return {"tasks": tasks}

    def _meeting_plan(self, payload: dict) -> dict:
        donor = payload["donor"]
        objectives = payload.get("fundraiser_objectives", [])
        event = payload.get("event")
        name = donor["name"]
        plan = {
            "meeting_format": f"Coffee meeting with {name} at their preferred venue in Los Angeles",
            "discussion_topics": [
                "Share impact metrics from the latest mentorship milestone",
                "Review commitments captured in the donor's strategic objectives",
                "Offer an interactive update aligned to their interests",
            ],
            "gift_ideas": [
                "Bring a hand-written thank-you card referencing their recent support",
                "Curate a wine-education podcast playlist tied to their preferences",
            ],
            "pre_meeting_preparation": [
                "Revisit detailed notes and open questions",
                "Draft answers for any objectives the donor asked about",
            ],
            "follow_up_plan": (
                "Send a recap within 24 hours summarizing agreed actions, attach relevant materials, and confirm next checkpoints."
            ),
        }
        if "wine" in donor.get("notes", "").lower():
            plan["discussion_topics"].append("Explore wine education experiences that fit her sommelier expertise")
        if objectives:
            plan["discussion_topics"].extend(objectives)
        if event:
            plan["event"] = event
            plan["event_specific_tips"] = [
                (
                    "Personalize the agenda with one high-impact story tied directly to the event theme so the conversation feels anchored."
                ),
                (
                    "Confirm logistics like guest list, dress code, and any moments where Alicia can speak or be recognized."
                ),
                (
                    "Bring a small keepsake—such as a robotics showcase photo card—that ties Alicia's passions to the gala experience."
                ),
            ]
            plan["pre_meeting_preparation"].append(
                "Draft talking points specific to the event so you can seamlessly transition from celebration to commitment."
            )
        return plan

    def _meeting_reflection(self, payload: dict) -> dict:
        donor = payload["donor"]
        meeting_notes = payload.get("meeting_notes", "")
        notes_lower = meeting_notes.lower()
        horizon = payload.get("follow_up_horizon_days", 7)

        follow_ups: list[str] = []
        missed_opportunities: list[str] = []
        suggested_questions = list(payload.get("missed_questions", []))

        deliverables = [
            (
                "mentor background checks",
                "Finalize and send the cleared mentor background checks so Alicia knows the program is ready."
            ),
            (
                "matching roster",
                "Share the complete mentor-mentee roster and highlight STEM pairings to honor her pledge conditions."
            ),
            (
                "progress dashboard",
                "Publish the mentorship progress dashboard and include it in your follow-up email."
            ),
        ]

        for keyword, action in deliverables:
            if keyword not in notes_lower:
                follow_ups.append(action)
                missed_opportunities.append(
                    f"Missed the chance to confirm the {keyword}; her $100k gift depends on seeing this handled."
                )

        for question in donor.get("open_questions", []):
            if "site visit" in question.lower() and "site visit" not in notes_lower:
                suggested_questions.append(question)
            if "daughter" in question.lower() and "daughter" not in notes_lower:
                suggested_questions.append(question)
            if "wine" in question.lower() and "wine" not in notes_lower:
                suggested_questions.append(question)

        if "forgot" in notes_lower or "didn't ask" in notes_lower:
            follow_ups.append("Send a rapid follow-up covering the topics you noted forgetting during the meeting.")
            suggested_questions.extend(donor.get("open_questions", []))

        follow_ups = list(dict.fromkeys(follow_ups))
        suggested_questions = list(dict.fromkeys(suggested_questions))
        missed_opportunities = list(dict.fromkeys(missed_opportunities))

        return {
            "missed_opportunities": missed_opportunities or [
                "No major gaps detected, but reinforce commitments in your recap."
            ],
            "follow_up_actions": follow_ups or [
                "Send a thank-you email reiterating next steps within 24 hours."
            ],
            "suggested_questions": suggested_questions,
            "updated_timeline": (
                f"Complete the follow-ups within the next {horizon} days to keep Alicia's pledge on track; "
                "block calendar time immediately so nothing slips."
            ),
        }


class DemoState:
    """Mutable state for the interactive walkthrough."""

    PLEDGE_SNIPPET = (
        "She said if I can deliver the mentorship pilot checklist—complete mentor background checks, "
        "finalize the mentor-mentee matching roster, and publish the progress dashboard—by next Wednesday, "
        "she will donate 100,000 dollars by the following week."
    )

    PLEDGE_REMINDER = (
        "She said if I can finalize the mentor background checks, confirm the mentor-mentee matching roster, and send "
        "her the updated mentorship progress dashboard by next week, then she will donate 100,000 dollars."
    )

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.llm = DemoStubLLM()
        self.directives: list[str] = []
        self.donors = []
        self.schedule = []
        self.reset()

    def reset(self) -> None:
        """Reload data and remove Alicia's pledge snippet to show the baseline state."""

        self.donors = load_donors(self.data_dir / "donors.json")
        self.schedule = load_schedule(self.data_dir / "schedule.json")
        self.llm = DemoStubLLM()
        self.directives = []
        self._strip_alicia_pledge()
        print("Reset demo state to the baseline dataset.")

    def _strip_alicia_pledge(self) -> None:
        alicia = find_donor(self.donors, "Alicia Gomez")
        if not alicia:
            return
        if self.PLEDGE_SNIPPET in alicia.notes:
            alicia.notes = alicia.notes.replace(
                self.PLEDGE_SNIPPET,
                (
                    "She is considering a major spring pledge and wants proof the mentorship pilot is truly launch-ready."
                ),
            )

    def add_directive(self, directive: str) -> None:
        if directive:
            if directive in self.directives:
                print(f"Directive already active: {directive}")
                return
            self.directives.append(directive)
            print(f"Added directive: {directive}")

    def clear_directives(self) -> None:
        self.directives.clear()
        print("Cleared all directives.")

    def append_note(self, donor_name: str, note: str) -> None:
        donor = find_donor(self.donors, donor_name)
        if not donor:
            print(f"Could not find donor named '{donor_name}'.")
            return
        if donor.notes and not donor.notes.endswith(" "):
            donor.notes += " "
        donor.notes += note.strip()
        print(f"Updated notes for {donor.name}.")

    def add_alicia_pledge(self) -> None:
        self.append_note("Alicia Gomez", self.PLEDGE_REMINDER)

    def generate_todo(self) -> None:
        tasks = generate_daily_todo(
            self.donors,
            self.schedule,
            today=date(2024, 3, 25),
            directives=self.directives,
            llm=self.llm,
        )
        print("\nSuggested to-do list:\n")
        for idx, task in enumerate(tasks, start=1):
            donors = ", ".join(task.get("related_donors", [])) or "general"
            print(f"{idx}. [{task['time']}] {task['task']} ({donors})")
            print(f"   → {task['reason']}\n")

    def plan_meeting(self, donor_name: str, event: str | None = None) -> None:
        donor = find_donor(self.donors, donor_name)
        if not donor:
            print(f"Could not find donor named '{donor_name}'.")
            return
        plan = plan_meeting(
            donor,
            meeting_date=date(2024, 3, 25),
            objectives=["Confirm mentorship deliverables are ready", "Discuss LA alumni mixer logistics"],
            event=event,
            llm=self.llm,
        )
        print("\nMeeting plan:\n")
        print(json.dumps(plan, indent=2))

    def plan_by_event(self, description: str) -> None:
        if not description:
            print("Please provide an event description (e.g., 'Meet Alicia at Gala 2025').")
            return
        lowered = description.lower()
        donor = next((d for d in self.donors if d.name.lower() in lowered), None)
        if not donor:
            print("Could not infer a donor from that event description. Try including their full name.")
            return
        self.plan_meeting(donor.name, event=description)

    def reflect_on_meeting(self, donor_name: str, meeting_notes: str, missed: list[str]) -> None:
        donor = find_donor(self.donors, donor_name)
        if not donor:
            print(f"Could not find donor named '{donor_name}'.")
            return
        summary = reflect_on_meeting(
            donor,
            meeting_notes=meeting_notes,
            follow_up_horizon_days=5,
            missed_questions=missed,
            llm=self.llm,
        )
        print("\nFollow-up guidance:\n")
        print(json.dumps(summary, indent=2))

    def show_donors(self) -> None:
        print("\nCurrent donor snapshots:\n")
        for donor in self.donors:
            latest_interaction = donor.interactions[-1].date.isoformat() if donor.interactions else "No interactions yet"
            print(f"- {donor.name} ({donor.primary_city or 'Unknown city'})")
            print(f"  Last interaction: {latest_interaction}")
            print(f"  Notes: {donor.notes}\n")

    def show_directives(self) -> None:
        if not self.directives:
            print("No active directives.")
            return
        print("Active directives:")
        for directive in self.directives:
            print(f"- {directive}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    state = DemoState(root / "data")

    print(
        dedent(
            """
            Welcome to the offline interactive demo! This walkthrough uses a deterministic stub instead of a live LLM so you
            can still showcase how the assistant grounds recommendations in donor notes, directives, and meeting recaps.

            The menu is organized to mirror the final presentation:
              • Option [1] resets to the baseline dataset (with Alicia's pledge note removed) and immediately shows the default
                to-do list.
              • Option [2] appends the $100k pledge reminder to Alicia's notes, enabling the assistant to surface the new
                deliverables on the next to-do run.
              • Options [3], [4], and [5] add the LA, catch-up, and disqualify directives one by one so you can regenerate the
                list after each change.
              • Option [7] lets you plan a donor interaction by typing an event description such as "Meet Alicia at Gala 2025".
              • Option [8] records meeting notes so the assistant can flag missed questions and urgent follow-ups.

            Type the menu number (or keyword) to trigger an action. Enter "quit" to exit.
            """
        )
    )

    while True:
        print(
            "\nMenu:\n"
            "  [1] Reset & show baseline to-do list\n"
            "  [2] Append Alicia's $100k pledge note\n"
            "  [3] Add directive: 'I am in LA right now...'\n"
            "  [4] Add directive: 'Find someone I haven't talked to for a while...'\n"
            "  [5] Add directive: 'Find someone I have been talking to for too long...'\n"
            "  [6] Generate to-do list with current context\n"
            "  [7] Plan meeting by event description\n"
            "  [8] Reflect on meeting notes\n"
            "  [9] Show donor snapshots\n"
            "  [10] Show active directives\n"
            "  [11] Clear directives\n"
            "  [12] Append custom note to donor\n"
            "  [quit] Exit\n"
        )
        choice = input("Select an option: ").strip().lower()
        if choice in {"quit", "q", "exit"}:
            print("Goodbye!")
            break
        if choice in {"1", "reset"}:
            state.reset()
            state.generate_todo()
            continue
        if choice in {"2", "pledge"}:
            state.add_alicia_pledge()
            continue
        if choice in {"3", "la"}:
            state.add_directive("I am in LA right now, find some clients that might be in LA too so I can catch up with them")
            continue
        if choice in {"4", "catchup"}:
            state.add_directive("Find someone that I haven't talked to for a while but I should")
            continue
        if choice in {"5", "disqualify"}:
            state.add_directive(
                "Find someone I have been talking to for too long and might not be interested in donating, so I can disqualify them"
            )
            continue
        if choice in {"6", "todo"}:
            state.generate_todo()
            continue
        if choice in {"7", "event"}:
            event_description = input("Describe the event (include the donor's name): ").strip()
            state.plan_by_event(event_description)
            continue
        if choice in {"8", "reflect"}:
            donor_name = input("Donor name: ").strip()
            meeting_notes = input("Meeting recap / notes: ").strip()
            missed_raw = input("Missed questions (comma-separated, optional): ").strip()
            missed = [item.strip() for item in missed_raw.split(",") if item.strip()]
            state.reflect_on_meeting(donor_name, meeting_notes, missed)
            continue
        if choice in {"9", "show"}:
            state.show_donors()
            continue
        if choice in {"10", "directives"}:
            state.show_directives()
            continue
        if choice in {"11", "clear"}:
            state.clear_directives()
            continue
        if choice in {"12", "note"}:
            donor_name = input("Donor name: ").strip()
            note = input("Additional note to append: ").strip()
            state.append_note(donor_name, note)
            continue
        print("Unknown option. Please try again.")


if __name__ == "__main__":
    main()
