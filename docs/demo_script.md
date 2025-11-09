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

1. Launch the scripted experience:

   ```bash
   PYTHONPATH=src python examples/offline_manual_demo.py
   ```

2. **Baseline to-do list** – Choose option **[1] Reset & show baseline to-do
   list**. Narrate that this uses the unmodified dataset (Alicia’s pledge note is
   intentionally absent) and the default directives, so the output reflects the
   "out-of-the-box" priorities.

3. **Append the pledge reminder** – Select **[2] Append Alicia's $100k pledge
   note**. Immediately regenerate the plan with **[6] Generate to-do list** and
   point out how three new tasks appear: finalizing mentor background checks,
   polishing the matching roster, and publishing the progress dashboard—each
   explicitly tied to unlocking the $100K gift.

4. **Layer location context** – Add the LA directive with **[3]** and re-run the
   to-do list via **[6]**. Emphasize the new "Schedule Los Angeles touchpoint"
   items that reference donor primary cities and travel notes.

5. **Surface dormant relationships** – Activate **[4]** to request donors you
   haven’t spoken with recently, then hit **[6]** again. Narrate how the stub
   reports the number of days since the last interaction and recommends specific
   catch-up actions.

6. **Identify prospects to pause** – Use **[5]** to add the disqualification
   directive and regenerate with **[6]**. Highlight the "Assess fit" entries that
   reference notes about waning interest.

7. **Plan an event-specific meeting** – Choose **[7] Plan meeting by event
   description** and type `Meet Alicia at Gala 2025`. Show the JSON plan that now
   includes event-specific tips in addition to the usual objectives and gift
   suggestions.

8. **Capture a post-meeting reflection** – Trigger **[8] Reflect on meeting
   notes**. Provide Alicia’s name, summarize a meeting where you forgot to
   confirm logistics or deliverables, and optionally list missed questions.
   Review how the assistant flags the unasked questions (e.g., site visit,
   robotics interest) and restates the high-stakes follow-ups tied to the
   $100K pledge.

9. Remind the audience that options **[9]–[12]** let you inspect donor notes,
   review active directives, clear the context, or append custom notes—handy for
   ad-hoc audience requests during rehearsal.

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
