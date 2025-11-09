# dont-forget-me

This project provides an AI-assisted workflow that helps a non-profit employee manage donor relationships. The assistant currently supports two workflows:

1. Generate a prioritized to-do list for the current day based on a weekly schedule and donor information.
2. Produce a meeting strategy for a specific donor, including talking points, gift ideas, and follow-up suggestions.

## Project layout

```
src/npo_assistant/
├── ai.py              # Prompt engineering and orchestration for LLM calls
├── cli.py             # Command-line entry point for running the assistant
├── data_loader.py     # Helpers to load donor and schedule data
├── llm.py             # OpenAI chat client abstraction
└── models.py          # Data classes representing donors and schedule entries
data/
├── donors.json        # Sample donor database
└── schedule.json      # Sample weekly schedule
```

## Usage

Create or update the `data/donors.json` and `data/schedule.json` files to match your organization. Set the `OPENAI_API_KEY` environment variable (or pass `--api-key` to the CLI), then run:

```
PYTHONPATH=src python -m npo_assistant.cli data todo --date 2024-03-25
PYTHONPATH=src python -m npo_assistant.cli data plan "Alicia Gomez" --date 2024-03-25
```

Use `--model` to select a different OpenAI chat model if desired. The commands output JSON describing the suggested to-do list or meeting plan. You can pipe the results to other tools or transform them into a UI of your choice.

## Development

The project targets Python 3.10 or newer. The runtime requires the [`openai`](https://pypi.org/project/openai/) package and a valid API key when you want to reach the hosted model. During development it can be helpful to create a virtual environment and point `PYTHONPATH` at the `src` directory. To run the automated checks locally:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt  # installs pytest (openai is optional for tests)
PYTHONPATH=src pytest
```

The test suite uses stubbed responses that mimic the LLM output, so it does not require network access or API usage. When running the CLI or using the package in production, the assistant will call the OpenAI Chat Completions API to produce its strategies.

## Extending the assistant

Customize the prompts or supply an alternate `LLMClient` implementation to integrate with a different provider. The `generate_daily_todo` and `plan_meeting` functions both accept an optional `llm` argument so you can inject custom behavior or mocks.
