"""Command-line interface for the NPO assistant."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from .ai import generate_daily_todo, plan_meeting
from .data_loader import find_donor, load_donors, load_schedule


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI assistant for NPO relationship managers")
    parser.add_argument("data_root", help="Directory containing donors.json and schedule.json")
    subparsers = parser.add_subparsers(dest="command", required=True)

    todo_parser = subparsers.add_parser("todo", help="Generate today's to-do list")
    todo_parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Target date")

    plan_parser = subparsers.add_parser("plan", help="Create a meeting plan for a donor")
    plan_parser.add_argument("name", help="Donor name")
    plan_parser.add_argument("--date", type=date.fromisoformat, default=date.today(), help="Meeting date")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    data_root = Path(args.data_root)
    donors = load_donors(data_root / "donors.json")
    schedule = load_schedule(data_root / "schedule.json")

    if args.command == "todo":
        tasks = generate_daily_todo(donors, schedule, today=args.date)
        print(json.dumps(tasks, indent=2))
    elif args.command == "plan":
        donor = find_donor(donors, args.name)
        if donor is None:
            parser.error(f"Donor '{args.name}' not found")
        plan = plan_meeting(donor, meeting_date=args.date)
        print(json.dumps(plan, indent=2))
    else:
        parser.error("Unknown command")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
