"""Command-line interface for the NPO assistant."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .ai import generate_daily_todo, plan_meeting, reflect_on_meeting
from .data_loader import find_donor, load_donors, load_schedule
from .llm import OpenAIChatClient


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI assistant for NPO relationship managers")
    parser.add_argument("data_root", help="Directory containing donors.json and schedule.json")
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Chat model to use for OpenAI completions (default: %(default)s)",
    )
    parser.add_argument(
        "--api-key",
        help="OpenAI API key. If omitted, the OPENAI_API_KEY environment variable is used.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    todo_parser = subparsers.add_parser("todo", help="Generate today's to-do list")
    todo_parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Target date")
    todo_parser.add_argument(
        "--directive",
        action="append",
        default=[],
        help="Optional custom focus instructions for the AI (repeatable).",
    )

    plan_parser = subparsers.add_parser("plan", help="Create a meeting plan for a donor")
    plan_parser.add_argument("name", help="Donor name")
    plan_parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Meeting date")
    plan_parser.add_argument(
        "--objective",
        action="append",
        default=[],
        help="Specific outcomes you want to achieve in the meeting (repeatable).",
    )

    reflect_parser = subparsers.add_parser(
        "reflect", help="Summarize follow-up needs after meeting with a donor"
    )
    reflect_parser.add_argument("name", help="Donor name")
    reflect_parser.add_argument(
        "--notes",
        required=True,
        help="Fresh meeting notes or recap to analyze for missed opportunities.",
    )
    reflect_parser.add_argument(
        "--missed-question",
        action="append",
        default=[],
        help="Important question you forgot to ask (repeatable).",
    )
    reflect_parser.add_argument(
        "--horizon",
        type=int,
        default=7,
        help="Number of days to look ahead when scheduling follow-up (default: %(default)s)",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data_root = Path(args.data_root)
    donors = load_donors(data_root / "donors.json")
    schedule = load_schedule(data_root / "schedule.json")

    llm = OpenAIChatClient(model=args.model, api_key=args.api_key)

    if args.command == "todo":
        tasks = generate_daily_todo(
            donors,
            schedule,
            today=args.date,
            directives=args.directive,
            llm=llm,
        )
        print(json.dumps(tasks, indent=2))
    elif args.command == "plan":
        donor = find_donor(donors, args.name)
        if donor is None:
            parser.error(f"Donor '{args.name}' not found")
        plan = plan_meeting(
            donor,
            meeting_date=args.date,
            objectives=args.objective,
            llm=llm,
        )
        print(json.dumps(plan, indent=2))
    elif args.command == "reflect":
        donor = find_donor(donors, args.name)
        if donor is None:
            parser.error(f"Donor '{args.name}' not found")
        reflection = reflect_on_meeting(
            donor,
            meeting_notes=args.notes,
            follow_up_horizon_days=args.horizon,
            missed_questions=args.missed_question,
            llm=llm,
        )
        print(json.dumps(reflection, indent=2))
    else:
        parser.error("Unknown command")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
