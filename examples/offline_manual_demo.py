"""Interactive offline demo that exercises the assistant workflows with a stubbed LLM."""
from __future__ import annotations

import json
import shlex
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

    # pylint: disable=too-many-locals, too-many-branches, too-many-statements
    def _daily_todo(self, payload: dict) -> dict:
        donors = payload["donors"]
        schedule = payload.get("schedule", [])
        directives = [item.lower() for item in payload.get("directives", [])]
        today = datetime.fromisoformat(payload["date"]).date()

        slot_order = [
            "08:00",
            "08:45",
            "09:30",
            "10:45",
            "12:15",
            "13:00",
            "14:30",
            "16:00",
        ]
        max_tasks = 6
        tasks: list[dict] = []
        added_tasks: set[str] = set()
        order = 0

        def add_task(
            task: str,
            reason: str,
            related: list[str],
            *,
            priority: int,
            default_time: str | None = None,
        ) -> None:
            nonlocal order
            if task in added_tasks:
                return
            tasks.append(
                {
                    "task": task,
                    "time": default_time,
                    "reason": reason,
                    "related_donors": related,
                    "_priority": priority,
                    "_order": order,
                }
            )
            added_tasks.add(task)
            order += 1

        donors_by_name = {donor["name"]: donor for donor in donors}

        def has_phrase(phrases: tuple[str, ...]) -> bool:
            return any(any(phrase in directive for phrase in phrases) for directive in directives)

        la_focus = any("los angeles" in d or " in la" in d for d in directives)
        reconnect_focus = has_phrase(
            (
                "haven't talked",
                "havent talked",
                "revive dormant",
                "reconnect",
                "dormant relationship",
                "re-engage",
            )
        )
        disqualify_focus = has_phrase(
            (
                "disqualify",
                "stop engaging",
                "too long",
                "disengage",
                "pause outreach",
            )
        )

        alicia = donors_by_name.get("Alicia Gomez")
        if alicia and "mentor background checks" in alicia.get("notes", "").lower():
            add_task(
                "Complete mentor background checks for the mentorship pilot",
                (
                    "Alicia tied her $100k commitment to seeing these background checks completed before next week. "
                    "Finish the clearance paperwork and confirm every mentor is approved."
                ),
                ["Alicia Gomez"],
                priority=0,
            )
            add_task(
                "Finalize the mentor-mentee matching roster",
                (
                    "Alicia wants the matching roster to review pairings before she signs the $100k gift. "
                    "Tighten the roster and flag any gaps in STEM representation."
                ),
                ["Alicia Gomez"],
                priority=0,
            )
            add_task(
                "Publish the mentorship progress dashboard",
                (
                    "Without the updated dashboard Alicia can't verify impact. Ship the metrics summary so the pledge can "
                    "clear by next week."
                ),
                ["Alicia Gomez"],
                priority=0,
            )

        directive_active = bool(directives)

        for entry in schedule:
            start = datetime.fromisoformat(entry["start"]).date()
            if start != today:
                continue
            donor_name = entry.get("donor")
            if donor_name:
                donor = donors_by_name.get(donor_name)
                if donor and donor.get("status") in {"paused", "disqualified", "inactive"}:
                    continue
                reason = (
                    f"Prep for {entry['title']} at {entry.get('location', 'the scheduled venue')}. "
                    f"Use the agenda notes: {entry.get('notes', 'Review donor priorities.')}"
                )
                add_task(
                    f"Prep briefing for {donor_name}",
                    reason,
                    [donor_name],
                    priority=1,
                    default_time=datetime.fromisoformat(entry["start"]).strftime("%H:%M"),
                )
            else:
                lower_notes = entry.get("notes", "").lower()
                optional = any(
                    phrase in lower_notes
                    for phrase in ("optional", "can move", "low priority", "deferred")
                )
                if directive_active:
                    base_priority = 7 if optional else 5
                else:
                    base_priority = 4 if optional else 2
                add_task(
                    f"Prepare for {entry['title']}",
                    "Gather the required program updates so every donor follow-up stays accurate.",
                    [],
                    priority=base_priority,
                    default_time=datetime.fromisoformat(entry["start"]).strftime("%H:%M"),
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
            original_directive = next(
                (
                    text
                    for text in payload.get("directives", [])
                    if "los angeles" in text.lower() or " in la" in text.lower()
                ),
                "Prioritize time in Los Angeles",
            )
            la_donors = [
                donor
                for donor in donors
                if donor.get("primary_city")
                and any(city in donor["primary_city"].lower() for city in ("los angeles", "pasadena"))
                and donor.get("status") not in {"paused", "disqualified", "inactive"}
            ]
            for donor in la_donors:
                add_task(
                    f"Schedule Los Angeles touchpoint with {donor['name']}",
                    (
                        f"Directive: {original_directive}. {donor['name']} can meet locally, so coordinate a coffee or site "
                        "visit while you're in town."
                    ),
                    [donor["name"]],
                    priority=2,
                )

        if reconnect_focus:
            reconnect_directive = next(
                (
                    text
                    for text in payload.get("directives", [])
                    if any(
                        phrase in text.lower()
                        for phrase in ("haven't talked", "havent talked", "revive", "reconnect")
                    )
                ),
                "Re-engage dormant supporters",
            )
            for donor in donors:
                gap = last_interaction_days(donor)
                if gap is not None and gap > 60:
                    add_task(
                        f"Reconnect with {donor['name']}",
                        (
                            f"Directive: {reconnect_directive}. It's been {gap} days since the last touchpoint with {donor['name']}. "
                            "Send a tailored update to restart the conversation."
                        ),
                        [donor["name"]],
                        priority=2,
                    )
                if gap is None:
                    add_task(
                        f"Introduce yourself to {donor['name']}",
                        (
                            f"Directive: {reconnect_directive}. You haven't logged a first conversation yet. Send a warm "
                            f"introduction so {donor['name']} knows you're the point of contact."
                        ),
                        [donor["name"]],
                        priority=2,
                    )

        if disqualify_focus:
            for donor in donors:
                notes = donor.get("notes", "").lower()
                stalled = (
                    donor.get("status") in {"paused", "disqualified"}
                    or "prefers fewer" in notes
                    or "not ready" in notes
                    or donor.get("engagement_stage") == "qualification"
                )
                if not stalled:
                    continue
                if donor.get("status") in {"paused", "disqualified"}:
                    reason = (
                        f"{donor['name']} is already marked as {donor.get('status')}. Confirm the CRM reflects this pause and "
                        "document any final notes."
                    )
                elif "prefers fewer" in notes:
                    reason = (
                        f"{donor['name']} asked for fewer check-ins. Reassess whether continued outreach aligns with their "
                        "interest level before the next touchpoint."
                    )
                else:
                    reason = (
                        f"{donor['name']} remains in qualification without momentum. Decide if they should be paused so you can"
                        " refocus on stronger prospects."
                    )
                add_task(
                    f"Pause outreach to {donor['name']}",
                    reason,
                    [donor["name"]],
                    priority=3,
                )

        if not tasks:
            add_task(
                "Review donor database",
                "No directives matched specific actions today—scan the database for emerging opportunities.",
                [],
                priority=5,
            )

        sorted_tasks = sorted(tasks, key=lambda item: (item["_priority"], item["_order"]))[:max_tasks]

        if directive_active:
            filtered: list[dict] = []
            general_allowed = 1
            general_used = 0
            for item in sorted_tasks:
                if item.get("related_donors"):
                    filtered.append(item)
                    continue
                if general_used < general_allowed:
                    filtered.append(item)
                    general_used += 1
            sorted_tasks = filtered
        used_times = {item["time"] for item in sorted_tasks if item.get("time")}
        slot_iter = (slot for slot in slot_order if slot not in used_times)
        for item in sorted_tasks:
            if not item.get("time"):
                item["time"] = next(slot_iter, slot_order[-1])
            item.pop("_priority", None)
            item.pop("_order", None)
        return {"tasks": sorted_tasks}

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
        raw_missed = [item for item in payload.get("missed_questions", []) if item]
        filtered_missed = [
            item
            for item in raw_missed
            if item.strip().lower() not in {"any suggestions", "any suggestions?"}
        ]
        suggested_questions = list(filtered_missed)

        deliverables = [
            (
                "mentor background checks",
                "Send Alicia the cleared mentor background check summary."
            ),
            (
                "matching roster",
                "Share the final mentor-mentee roster highlighting the STEM pairings."
            ),
            (
                "progress dashboard",
                "Deliver the mentorship progress dashboard update in your follow-up email."
            ),
        ]

        for keyword, action in deliverables:
            if keyword not in notes_lower:
                follow_ups.append(action)
                missed_opportunities.append(
                    f"Confirm the {keyword} Alicia tied to her $100k pledge."
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
            "missed_opportunities": missed_opportunities
            or ["No major gaps detected—reinforce commitments in your recap."],
            "follow_up_actions": follow_ups
            or ["Send a thank-you note that reiterates agreed next steps."],
            "suggested_questions": suggested_questions,
            "updated_timeline": (
                f"Complete these follow-ups within {horizon} days so Alicia's pledge stays on track."
            ),
        }


class DemoState:
    """Mutable state for the interactive walkthrough."""

    PLEDGE_SNIPPET = (
        "She said if I can deliver the mentorship pilot checklist—complete mentor background checks, "
        "finalize the mentor-mentee matching roster, and publish the progress dashboard—by next Wednesday, "
        "she will donate 100,000 dollars by the following week."
    )

    PLEDGE_REPLACEMENT = (
        "She is considering a major spring pledge and wants proof the mentorship pilot is truly launch-ready."
    )

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.donors_path = self.data_dir / "donors.json"
        self.schedule_path = self.data_dir / "schedule.json"
        self.llm = DemoStubLLM()
        self.directives: list[str] = []
        self._baseline_donors_payload = self._load_baseline_donors()
        self._baseline_schedule_payload = self._load_json(self.schedule_path)

    def _load_json(self, path: Path):
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _write_json(self, path: Path, payload) -> None:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")

    def _load_baseline_donors(self):
        payload = self._load_json(self.donors_path)
        for entry in payload:
            notes = entry.get("notes", "")
            if self.PLEDGE_SNIPPET in notes:
                entry["notes"] = notes.replace(self.PLEDGE_SNIPPET, self.PLEDGE_REPLACEMENT)
        return payload

    def reset(self) -> None:
        """Restore the sample data to the baseline state without Alicia's pledge reminder."""

        self._write_json(self.donors_path, self._baseline_donors_payload)
        self._write_json(self.schedule_path, self._baseline_schedule_payload)
        self.directives.clear()
        self.llm = DemoStubLLM()
        print(
            "Reset donors.json and schedule.json to their baseline versions. "
            "Alicia's pledge reminder has been removed so you can add it manually during the demo."
        )

    def _load_current_donors(self):
        return load_donors(self.donors_path)

    def _load_current_schedule(self):
        return load_schedule(self.schedule_path)

    def add_directive(self, directive: str) -> None:
        directive = directive.strip()
        if not directive:
            print("Cannot add an empty directive.")
            return
        if directive in self.directives:
            print(f"Directive already active: {directive}")
            return
        self.directives.append(directive)
        print(f"Added directive: {directive}")

    def remove_directive(self, directive: str) -> None:
        try:
            self.directives.remove(directive)
            print(f"Removed directive: {directive}")
        except ValueError:
            print(f"Directive not found: {directive}")

    def list_directives(self) -> None:
        if not self.directives:
            print("No active directives.")
            return
        print("Active directives:")
        for directive in self.directives:
            print(f"- {directive}")

    def clear_directives(self) -> None:
        self.directives.clear()
        print("Cleared all directives.")

    def generate_todo(self) -> None:
        donors = self._load_current_donors()
        schedule = self._load_current_schedule()
        tasks = generate_daily_todo(
            donors,
            schedule,
            today=date(2024, 3, 25),
            directives=self.directives,
            llm=self.llm,
        )
        if self.directives:
            print("\nCurrent directives driving this list:")
            for directive in self.directives:
                print(f"- {directive}")
        print("\nSuggested to-do list:\n")
        for idx, task in enumerate(tasks, start=1):
            donors_text = ", ".join(task.get("related_donors", [])) or "general"
            print(f"{idx}. [{task['time']}] {task['task']} ({donors_text})")
            print(f"   → {task['reason']}\n")

    def plan_meeting_for_donor(self, donor_name: str, event: str | None = None) -> None:
        donors = self._load_current_donors()
        donor = find_donor(donors, donor_name)
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
        description = description.strip()
        if not description:
            print(
                "Please provide an event description (for example, copy the exact title from the to-do list)."
            )
            return
        donors = self._load_current_donors()
        lowered = description.lower()
        full_matches = [d for d in donors if d.name.lower() in lowered]
        if full_matches:
            self.plan_meeting_for_donor(full_matches[0].name, event=description)
            return

        first_name_matches = [
            d for d in donors if d.name.split()[0].lower() in lowered
        ]
        first_name_matches = list({d.name: d for d in first_name_matches}.values())
        if len(first_name_matches) == 1:
            self.plan_meeting_for_donor(first_name_matches[0].name, event=description)
            return

        last_name_matches = [
            d for d in donors if d.name.split()[-1].lower() in lowered
        ]
        last_name_matches = list({d.name: d for d in last_name_matches}.values())
        if len(last_name_matches) == 1:
            self.plan_meeting_for_donor(last_name_matches[0].name, event=description)
            return

        print(
            "Could not confidently infer a donor from that event description. Try pasting the full task name from "
            "today's to-do list so the donor is unambiguous."
        )

    def reflect_on_meeting(self, donor_name: str, meeting_notes: str, missed: list[str]) -> None:
        donors = self._load_current_donors()
        donor = find_donor(donors, donor_name)
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
        missed_items = summary.get("missed_opportunities", [])
        if missed_items:
            print("Missed commitments to revisit:")
            for item in missed_items:
                print(f"- {item}")
            print()
        actions = summary.get("follow_up_actions", [])
        if actions:
            print("Immediate next steps:")
            for action in actions:
                print(f"- {action}")
            print()
        questions = summary.get("suggested_questions", [])
        if questions:
            print("Questions to cover next time:")
            for question in questions:
                print(f"- {question}")
            print()
        timeline = summary.get("updated_timeline")
        if timeline:
            print(f"Timing reminder: {timeline}")

    def show_donors(self) -> None:
        donors = self._load_current_donors()
        print("\nCurrent donor snapshots:\n")
        for donor in donors:
            latest_interaction = donor.interactions[-1].date.isoformat() if donor.interactions else "No interactions yet"
            print(f"- {donor.name} ({donor.primary_city or 'Unknown city'})")
            print(f"  Last interaction: {latest_interaction}")
            print(f"  Notes: {donor.notes}\n")


def _print_help() -> None:
    print(
        dedent(
            """
            Commands:
              reset                       → Restore donors.json to the baseline state (removes Alicia's pledge note).
              todo                        → Reload data from disk and generate the current to-do list.
              directives add <text>       → Add a directive that will influence the next to-do list.
              directives remove <text>    → Remove a previously added directive.
              directives list             → Show the active directives.
              directives clear            → Remove all directives.
              donors                      → Print the current donor notes to verify edits.
              plan <donor name>           → Generate a meeting strategy for the donor.
              event <description>         → Generate a meeting strategy inferred from an event description.
              reflect <donor name>        → Summarize follow-ups after a meeting (you'll be prompted for notes).
              help                        → Show this help message.
              quit                        → Exit the demo.
            """
        )
    )


def _prompt_multiline(prompt: str) -> str:
    print(prompt)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line)
    return "\n".join(lines)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    state = DemoState(root / "data")

    print(
        dedent(
            """
            Welcome to the offline interactive demo! This walkthrough uses a deterministic stub instead of a live LLM so you
            can still showcase how the assistant grounds recommendations in donor notes, directives, and meeting recaps.

            The script mirrors the real workflow: edit the JSON data just as you would in production, then regenerate
            suggestions. Launching the demo restores the baseline dataset so Alicia's $100k pledge reminder is absent—you'll
            add it manually in step two of the walkthrough.

            Tip: keep your editor open on data/donors.json so you can paste new notes between commands.
            Type "help" at any time to see the available commands.
            """
        )
    )

    state.reset()
    print("\nBaseline to-do list (before making any edits):")
    state.generate_todo()

    while True:
        try:
            raw = input("\nassistant> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not raw:
            continue
        lowered = raw.lower()
        if lowered in {"quit", "exit"}:
            print("Goodbye!")
            break
        if lowered in {"help", "?"}:
            _print_help()
            continue
        tokens = shlex.split(raw)
        if not tokens:
            continue
        command = tokens[0].lower()
        args = tokens[1:]

        if command == "reset":
            state.reset()
            continue
        if command == "todo":
            state.generate_todo()
            continue
        if command == "directives":
            if not args:
                print("Usage: directives <add|remove|list|clear> [text]")
                continue
            subcommand = args[0].lower()
            remainder = " ".join(args[1:])
            if subcommand == "add":
                state.add_directive(remainder)
            elif subcommand == "remove":
                state.remove_directive(remainder)
            elif subcommand in {"list", "show"}:
                state.list_directives()
            elif subcommand == "clear":
                state.clear_directives()
            else:
                print("Usage: directives <add|remove|list|clear> [text]")
            continue
        if command == "donors":
            state.show_donors()
            continue
        if command == "plan":
            if not args:
                print("Usage: plan <donor name>")
                continue
            donor_name = " ".join(args)
            state.plan_meeting_for_donor(donor_name)
            continue
        if command == "event":
            description = " ".join(args)
            state.plan_by_event(description)
            continue
        if command == "reflect":
            if not args:
                print("Usage: reflect <donor name>")
                continue
            donor_name = " ".join(args)
            notes = _prompt_multiline(
                "Paste your meeting recap (end with a blank line):"
            )
            missed_raw = input("Missed questions (comma-separated, optional): ").strip()
            missed = [item.strip() for item in missed_raw.split(",") if item.strip()]
            state.reflect_on_meeting(donor_name, notes, missed)
            continue
        print("Unknown command. Type 'help' to see the available options.")


if __name__ == "__main__":
    main()
