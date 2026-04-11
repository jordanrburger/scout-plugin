---
phase: mode
name: feedback-processing
slot: dreaming-phase-1
mode: [dreaming]
requires: slack
---

## Phase 1: Feedback Processing

This is the self-improvement loop. Harvest feedback from {{USER_NAME}}'s reactions and replies to {{INSTANCE_NAME}}'s messages, classify signals, update the mistake audit, and apply or propose improvements.

---

### Step 1a: Harvest Feedback from Slack

Read the bot's DM conversation with {{USER_NAME}} using `slack_read_channel` with channel_id `{{USER_SLACK_ID}}`.

**Determine the time window:**
1. Check the Recent Sessions table in `knowledge-base.md` for the last dreaming session entry.
2. If a previous dreaming entry exists, look back to that timestamp.
3. If no previous dreaming entry exists (first run), look back 24 hours from now.

**For each message authored by {{INSTANCE_NAME}} (the bot) within the time window:**
1. Call `slack_read_thread` on that message's timestamp to retrieve all thread replies and reactions.
2. Collect and record:
   - **Message content**: the original text {{INSTANCE_NAME}} sent
   - **Reactions**: each emoji name and who added it (user ID + display name if available)
   - **Thread replies**: each reply's full text, author (user ID + display name), and timestamp

Skip messages not authored by {{INSTANCE_NAME}}. Only harvest feedback on the bot's own outputs.

---

### Step 1b: Classify Feedback Signals

Categorize every piece of harvested feedback into one of these signal types:

| Signal Type | Indicators | Action |
|---|---|---|
| **Positive confirmation** | `+1`, thumbsup, checkmark, heart, or praise in thread replies ("great", "perfect", "exactly right") | Log what worked — the content, format, or behavior that earned approval |
| **Negative flag** | `x`, thumbsdown, `-1`, or criticism in thread replies ("wrong", "bad", "don't do this") | Log what failed — the specific output or behavior that was rejected |
| **Correction with context** | A thread reply that explains what was wrong AND provides the correct information or reasoning | Extract a concrete rule or heuristic from the correction. This is the highest-value signal. |
| **Mixed** | Positive reactions on some parts of a message, negative on others; or a reply that says "X was good but Y was wrong" | Separate into individual positive and negative items, handle each independently |

**Rules for classification:**
- A bare reaction with no thread context is a weaker signal than a reply with explanation. Still record it, but weight corrections with context higher.
- If the same message has conflicting signals from different people, note the conflict but weight {{USER_NAME}}'s signal highest.
- If a reaction is ambiguous (e.g., a thinking-face emoji), do not classify it as positive or negative. Skip it.

---

### Step 1c: Cross-Reference with Mistake Audit

Read `knowledge-base/scout-mistake-audit.md`. For every negative or correction signal from Step 1b:

**If the signal matches an existing pattern in the mistake audit:**
- Increment the occurrence count for that pattern.
- Add this instance as a new evidence entry (date, message content, feedback received).
- If the pattern's status was `Fixed` but this is a recurrence, change status back to `Open` and add a `[regression]` flag with the date. This is the most important update — regressions indicate the fix was incomplete.

**If the signal does NOT match any existing pattern:**
- Add a new entry to the mistake audit with:
  - **Error type**: category (e.g., "stale data", "wrong attribution", "hallucinated detail", "formatting issue", "missed context")
  - **What happened**: specific description of the incorrect output
  - **Root cause**: best assessment of why the error occurred (e.g., "relied on cached KB data without re-querying", "assumed person X was still on team Y")
  - **Fix needed**: concrete corrective action (e.g., "always re-query issue status before reporting", "cross-reference people.md entries with live sources")
  - **Occurrences**: 1
  - **Status**: Open

**For positive signals on previously problematic areas:**
- If a positive confirmation relates to a topic or behavior that has an Open or Fixed entry in the mistake audit, update the entry:
  - If status is `Open` and the positive signal shows the fix is working, change to `Fixed` with evidence (date + the positive feedback).
  - If status is already `Fixed`, add the positive signal as corroborating evidence.

---

### Step 1d: Determine and Apply Improvements

Based on the classified signals and mistake audit updates, determine what changes to make. Use this autonomy table:

| Target File | Autonomy Level | Action |
|---|---|---|
| `knowledge-base/scout-mistake-audit.md` | **Direct edit** | Apply updates from Step 1c immediately |
| KB files (content corrections) | **Direct edit** | Fix factual errors identified by feedback (e.g., wrong status, wrong person, outdated info) |
| `DREAMING.md` | **Direct edit** | Improve dreaming behavior based on patterns (e.g., adjust scoring weights, add checklist items) |
| `SKILL.md` | **PROPOSAL ONLY** | Never edit directly. Write a proposal to `dreaming-proposals.md` (see Step 1e) |
| New KB files or structural changes | **Direct edit** | Only if supported by clear evidence from multiple feedback signals |

**Guardrails:**
- Never remove content from `SKILL.md` without a proposal. Even if feedback says a behavior is wrong, the fix may need nuance that a proposal review provides.
- For KB content fixes, always cite the feedback that triggered the change: "Corrected per {{USER_NAME}} feedback on [date]: [brief description]."
- If a correction contradicts information from a live connector, investigate before changing. The correction may be about interpretation, not raw data.

---

### Step 1e: Handle Proposals

**First: check for approved proposals.**

Read `dreaming-proposals.md`. For any proposal with status `Approved`:
1. Apply the proposed change to `SKILL.md` exactly as specified in the proposal's "Proposed change" section.
2. Update the proposal's status to `Applied — [today's date]`.
3. Commit this change separately:
   ```bash
   git -C {{SCOUT_DIR}} add -A && git -C {{SCOUT_DIR}} commit -m "dreaming [HH:MM]: applied approved proposal — <short description>"
   ```

**Then: write new proposals.**

For every improvement that targets `SKILL.md` (from Step 1d), write a proposal using this format:

```markdown
### [Date] — [Short description]
**Trigger:** [specific feedback or pattern that prompted this]
**Proposed change:** [specific edit with before/after text, or exact addition with location]
**Rationale:** [why this change prevents the issue or improves behavior]
**Evidence:** [specific feedback instances — dates, message content, reactions]
**Status:** Pending
```

**Quality bar for proposals:** Every proposal must be specific enough that a future dreaming run can apply it mechanically without ambiguity. "Make Scout better at X" is not a proposal. "In SKILL.md section Y, change line Z from 'always do A' to 'do A only when B, otherwise do C'" is a proposal.

---

### Step 1f: Commit

If Phase 1 made any changes (mistake audit updates, KB fixes, dreaming improvements, applied proposals, new proposals):

```bash
git -C {{SCOUT_DIR}} add -A && git -C {{SCOUT_DIR}} commit -m "dreaming [HH:MM]: feedback processing — <summary of changes>"
```

The summary should mention what was processed: e.g., "3 feedback signals, 1 new mistake pattern, 2 KB fixes" or "applied 1 approved proposal, added 2 new proposals."

If Phase 1 found no actionable feedback (no reactions, no thread replies in the time window), skip the commit and proceed to Phase 2. Log "No feedback signals found in time window" in the session entry.
