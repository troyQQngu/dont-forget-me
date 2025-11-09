# dont-forget-me

This project provides a lightweight AI-inspired assistant that helps a non-profit employee manage donor relationships. The assistant currently supports two workflows:

1. Generate a prioritized to-do list for the current day based on a weekly schedule and donor information.
2. Produce a meeting strategy for a specific donor, including talking points, gift ideas, and follow-up suggestions.

## Project layout

```
src/npo_assistant/
├── ai.py              # Heuristic "AI" logic for tasks and meeting plans
├── cli.py             # Command-line entry point for running the assistant
├── data_loader.py     # Helpers to load donor and schedule data
└── models.py          # Data classes representing donors and schedule entries
data/
├── donors.json        # Sample donor database
└── schedule.json      # Sample weekly schedule
```

## Usage

Create or update the `data/donors.json` and `data/schedule.json` files to match your organization. Then run:

```
PYTHONPATH=src python -m npo_assistant.cli data todo --date 2024-03-25
PYTHONPATH=src python -m npo_assistant.cli data plan "Alicia Gomez" --date 2024-03-25
```

The commands output JSON describing the suggested to-do list or meeting plan. You can pipe the results to other tools or transform them into a UI of your choice.

## Extending the assistant

The heuristics in `ai.py` are designed to be easy to replace with a real large language model call. The module exposes two functions—`generate_daily_todo` and `plan_meeting`—that can be swapped to use an API client instead of the built-in rules.
