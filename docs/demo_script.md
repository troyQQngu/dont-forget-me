# Demo script and run of show

This guide walks you through a polished demo of the donor assistant. It includes
narration tips, the exact commands to run, and branches for both an
internet-connected showcase and the fully offline interactive rehearsal powered
by the stub LLM.

---

## 1. Set the stage (2 minutes)

1. **Frame the story** – Explain that the assistant keeps a non-profit
   fundraiser on track by grounding LLM suggestions in rich donor notes and the
   weekly schedule.
2. **Highlight the assets** – Point to:
   * `data/donors.json` for long-form relationship history (open it in your
     editor to show Alicia Gomez's mentorship commitments and wine expertise).
   * `data/schedule.json` for the upcoming week of meetings.
   * `examples/offline_manual_demo.py` as the interactive rehearsal tool.
3. **Mention configuration** – Note that a live demo only needs an
   `OPENAI_API_KEY`, but the offline script mirrors every feature without
   network access.

---

## 2. Walkthrough with a live LLM (8–10 minutes)

> Skip this section if you are rehearsing offline; jump to
> [Section 3](#3-interactive-offline-rehearsal-8-10-minutes).

### 2.1 Daily to-do list driven by directives (3 minutes)

1. Run the CLI with location and relationship directives:

   ```bash
   PYTHONPATH=src python -m npo_assistant.cli data todo --date 2024-03-25 \
     --directive "I am in LA right now, prioritize donors I can meet there" \
     --directive "Find someone I haven't talked to for a while but should" \
     --directive "Find someone I have been talking to for too long and might not be interested in donating, so I can disqualify them"
   ```

2. Narrate the JSON output:
   * Show that Alicia Gomez is highlighted because her notes mention an LA
     meetup and a $100K pledge contingent on finishing three deliverables
     (mentor background checks, matching roster, impact dashboard).
   * Call out that the "catch up" directive surfaces dormant donors, while the
     "disqualify" directive flags relationships that are stalling.
   * Emphasize the "reason" fields that quote directly from the donor notes.

### 2.2 Meeting strategy for a key donor (3 minutes)

1. Generate a plan for Alicia with targeted objectives:

   ```bash
   PYTHONPATH=src python -m npo_assistant.cli data plan "Alicia Gomez" --date 2024-03-25 \
     --objective "Confirm mentor background checks, roster, and dashboard before Friday" \
     --objective "Suggest a refined wine-themed gift that isn't a bottle" \
     --objective "Ask about her daughter's robotics team to build rapport"
   ```

2. Narrate how each recommendation ties back to the notes (wine expertise, LA
   availability, mentorship commitments, family details).

### 2.3 Interactive reflection after a meeting (2–4 minutes)

1. Pretend you just met Alicia and forgot to cover a few items. Feed that into
   the reflection command:

   ```bash
   PYTHONPATH=src python -m npo_assistant.cli data reflect "Alicia Gomez" \
     --notes "Met today. Promised to send the mentorship onboarding checklist, but we didn't confirm the volunteer background checks timeline or whether she wants a site visit. She also mentioned her daughter's robotics competition next month." \
     --missed-question "Clarify if she prefers a virtual or in-person site tour" \
     --horizon 7
   ```

2. Highlight how the assistant:
   * Reminds you to deliver the three mentorship commitments immediately.
   * Flags the missed site-visit question and any other critical follow-ups (e.g.,
     aligning on the robotics team sponsorship angle).

---

## 3. Interactive offline rehearsal (8–10 minutes)

1. Start the scripted experience:

   ```bash
   PYTHONPATH=src python examples/offline_manual_demo.py
   ```

2. Follow the prompts. The script walks through four acts—each mirrors the live
   demo but with deterministic stubbed responses. Narration tips for each act:

   | Act | What to type | What to emphasize |
   | --- | --- | --- |
   | 1. **Directive primer** | Accept the default date (2024-03-25) and enter the same three directives you would use live. | Show how the stub echoes LA prioritization, dormant donors to re-engage, and prospects to pause, all with grounded reasoning. |
   | 2. **Note update & re-run** | When prompted, append the pledge reminder by entering:<br>`She said if we finalize the mentor background checks, deliver the matching roster, and publish the progress dashboard by next Friday, she'll wire $100,000.` | Immediately request the updated to-do list to demonstrate that the assistant now pushes those three tasks to the top with clear deadlines. |
   | 3. **Meeting planning** | Provide Alicia's name and accept the suggested objectives. | Note how the stub references wine expertise, LA availability, and the mentorship commitments. |
   | 4. **Post-meeting reflection** | Enter a recap where you forgot to confirm the site visit and volunteer paperwork. | Observe how the script produces reminders to send the checklist, lock the background check schedule, and follow up on the robotics question you missed. |

3. Close by pointing out that the offline experience logs every prompt/response
   to the console, so presenters can practice answers to likely stakeholder
   questions.

---

## 4. Optional variations and audience Q&A (3 minutes)

* **Switch donors** – Update `data/donors.json` with another long-form note (e.g.
  Ben Ito's interest in LA site visits) and rerun the same commands to show how
  quickly the narrative changes.
* **Adjust the schedule** – Move a meeting into `schedule.json` to influence the
  daily planner. Mention that the assistant cross-references the schedule to
  avoid conflicts.
* **Demonstrate extensibility** – Briefly mention that the CLI accepts any
  number of `--directive`, `--objective`, or `--missed-question` flags, so you
  can respond to on-the-fly requests from the audience.

---

## 5. Pre-demo checklist

- [ ] Ensure Python 3.10+ is available.
- [ ] Export `OPENAI_API_KEY` if you plan to hit the live LLM.
- [ ] Run `PYTHONPATH=src pytest` to confirm the environment is healthy.
- [ ] Open the donor JSON file in your editor for quick reference during the
      narration.
- [ ] Keep this script handy to stay on pace.

With this run of show you can confidently demonstrate how the assistant grounds
its guidance in donor notes, adapts to new information instantly, and supports a
full lifecycle of planning, meeting, and follow-up.
