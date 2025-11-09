# dont-forget-me

This project provides an AI-assisted workflow that helps a non-profit employee manage donor relationships. The assistant currently supports three complementary workflows:

1. Generate a prioritized to-do list for the current day based on a weekly schedule, rich donor notes, and any custom directives you provide.
2. Produce a meeting strategy for a specific donor, including talking points, gift ideas, preparation steps, and follow-up suggestions aligned to your objectives.
3. Reflect on a meeting recap to surface missed opportunities, follow-up actions, and questions you still need to ask.

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

Create or update the `data/donors.json` and `data/schedule.json` files to match your organization. The sample data illustrates long-form relationship notes that contain commitments ("complete mentor background checks, finalize the matching roster, and publish the progress dashboard"), personal context, location hints, and open questions. The model leans on this context when generating suggestions.

Set the `OPENAI_API_KEY` environment variable (or pass `--api-key` to the CLI), then run:

```
PYTHONPATH=src python -m npo_assistant.cli data todo --date 2024-03-25 \
  --directive "I am in LA right now, prioritize donors I can meet there" \
  --directive "Flag anyone I should pause because conversations are stalling"

PYTHONPATH=src python -m npo_assistant.cli data plan "Alicia Gomez" --date 2024-03-25 \
  --objective "Confirm that the mentorship deliverables (background checks, roster, dashboard) are ready" \
  --objective "Identify a thoughtful wine-related touch that isn't a bottle"

PYTHONPATH=src python -m npo_assistant.cli data reflect "Alicia Gomez" \
  --notes "Met today, promised to send checklist and forgot to ask about daughter's robotics interest." \
  --missed-question "Confirm if Alicia prefers a site visit or virtual tour" \
  --horizon 5
```

Use `--model` to select a different OpenAI chat model if desired. Each command outputs JSON that you can pipe into downstream tooling or a prototype UI.

### Offline manual experiment

If you want to experiment without API access, run the bundled example script that injects a stubbed LLM response:

```
PYTHONPATH=src python examples/offline_manual_demo.py
```

The script restores `data/donors.json` to a baseline state (with Alicia's $100k pledge note removed), prints the default to-do list, and then waits for free-form commands. Edit the JSON just as you would for the live system—append notes in your editor, save, return to the prompt, and run `todo` to see how the recommendations change. A few highlights:

* After you add Alicia's pledge reminder manually, the next `todo` run surfaces the mentorship deliverables (background checks, matching roster, progress dashboard) with grounded reasoning.
* Use `directives add …` to layer location filters, catch-up requests, or disqualification criteria before regenerating the plan—each recommendation cites the donor data that triggered it.
* `event Meet Alicia at Gala 2025` produces an event-specific meeting plan, while `reflect Alicia Gomez` analyzes your recap for missed questions and urgent follow-ups.
* Because the script reloads from disk for every command, any manual edit to `data/` is reflected immediately, making the rehearsal feel identical to a live LLM session.


## Detailed demo process

If you are preparing a stakeholder walkthrough, follow the scripted flow in
[`docs/demo_script.md`](docs/demo_script.md). It covers both an online demo with a
live LLM and a fully offline rehearsal, including when to switch datasets,
which CLI invocations to run, and how to narrate the assistant's reasoning at
each step.


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

Customize the prompts or supply an alternate `LLMClient` implementation to integrate with a different provider. The `generate_daily_todo`, `plan_meeting`, and `reflect_on_meeting` functions accept optional `llm` arguments so you can inject custom behavior or mocks. You can also supply extra directives/objectives programmatically when orchestrating multi-step fundraising workflows.
