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

   The tool restores `data/donors.json` to the baseline dataset (with Alicia's
   pledge reminder removed) and immediately prints the current to-do list. Use
   this first output to describe the "default" priorities before any fresh
   context is added—it's a packed schedule that includes lower-impact admin
   items (newsletter draft, finance reconciliation). Mention that those tasks
   will fall away once directives introduce higher-priority outreach.

2. **Append the pledge reminder manually** – Open `data/donors.json` in your
   editor, find Alicia Gomez’s `notes`, and paste the following sentence at the
   end of the paragraph (or adapt the language to suit your narrative):

   > She said if I can deliver the mentorship pilot checklist—complete mentor
   > background checks, finalize the mentor-mentee matching roster, and publish
   > the progress dashboard—by next Wednesday, she will donate 100,000 dollars by
   > the following week.

   Save the file, return to the terminal, and run `todo`. Point out how the
   refreshed list now includes three mission-critical deliverables tied directly
   to that freshly recorded pledge commitment.

3. **Layer location context** – Type the following and hit enter:

   ```
   assistant> directives add "I am in LA right now, find some clients that might be in LA too so I can catch up with them"
   assistant> todo
   ```

   Narrate the new "Schedule Los Angeles touchpoint" entries and tie each back to
   donor primary cities or travel notes. Point out how one of the low-priority
   admin blocks disappears to make space for the location-focused outreach.

4. **Surface dormant relationships** – Add another directive and refresh the
   list:

   ```
   assistant> directives add "Find someone that I haven't talked to for a while but I should"
   assistant> todo
   ```

   Call out how the assistant cites the number of days since each donor’s last
   interaction to justify the catch-up suggestions, and note that another
   optional admin task was dropped so the reconnection can take precedence.

5. **Identify prospects to pause** – Layer the disqualification directive and
   regenerate:

   ```
   assistant> directives add "Find someone I have been talking to for too long and might not be interested in donating, so I can disqualify them"
   assistant> todo
   ```

   Highlight the "Pause outreach" actions that explain why each donor is a poor
   near-term fit.

6. **Plan an event-specific meeting** – Copy the exact task title from the
   latest to-do list (for example, `Coffee briefing with Alicia Gomez`) and run:

   ```
   assistant> event Coffee briefing with Alicia Gomez
   ```

   Explain that using the precise task title helps the assistant infer the donor
   immediately. Walk through how the JSON plan blends Alicia's standing
   objectives with fresh tips tied to that meeting.

7. **Capture a post-meeting reflection** – Trigger a follow-up summary by
   entering:

   ```
   assistant> reflect Alicia Gomez
   ```

   When prompted, paste notes that admit you forgot to confirm the mentorship
   deliverables and skipped a question about her daughter's robotics team. After
   submitting optional "missed questions," walk through the bulleted guidance
   that now summarizes missed commitments, next steps, and follow-up questions in
   plain language.

8. Mention that additional helpers are available:
   * `directives list` shows the active context filters.
   * `directives clear` wipes them if you want to restart a section.
   * `plan Alicia Gomez` generates a strategy without referencing an event.
   * `donors` prints the current notes so you can confirm manual edits before the
     next command.

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
