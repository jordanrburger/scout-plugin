---
phase: core
name: action-items
slot: action-items
mode: [briefing, consolidation]
requires: null
---

## Step 0: Archive Old Action Items

Move any `action-items/action-items-*.md` files older than 7 days into `action-items/archive/`. Create the archive folder if it doesn't exist. Use the date in the filename to determine age.

```bash
mkdir -p {{SCOUT_DIR}}/action-items/archive
# Move files older than 7 days based on filename date
```

## Action Item Categories

Categorize every action item using these levels:

- **🔴 Urgent**: Needs attention today
- **🟡 To Do**: Should be done soon
- **🟢 Watching**: Tracking but no action needed yet
- **✅ Done**: Completed with evidence of completion

## Action Items File Format

Create `action-items/action-items-YYYY-MM-DD.md` using today's date. Include:

```markdown
# Action Items — YYYY-MM-DD

**Last consolidated:** YYYY-MM-DD HH:MM [timezone]

## 🔴 Urgent

- **[Item title]** — [Description with specific details, not vague summaries]
  - Source: [Which connector(s) confirmed this]
  - Context: [[wikilink-to-relevant-kb-file]]

## 🟡 To Do

- **[Item title]** — [Description]
  - Source: [connector evidence]
  - Context: [[wikilink]]

## 🟢 Watching

- **[Item title]** — [What you're tracking and why]
  - Source: [connector evidence]
  - Context: [[wikilink]]

## ✅ Done

- **[Item title]** — [What was completed and how]
  - Evidence: [Link to message, PR, calendar change, or other proof]
  - Completed: [date/time]

## Carryover

Items carried forward from previous days that are still open.

- **[Item title]** — [Status update since last check]
  - Originally from: action-items-YYYY-MM-DD
  - Current status: [what's changed]
```

All action items files must include `[[wikilinks]]` to any KB files referenced by action items.

## Mandatory Cross-Check

**Before ANY item becomes a To Do, it must pass ALL available cross-checks.** The cross-check adapts to your connected services:

- **If Calendar connected:** Is this already scheduled? Does a meeting already exist for this? Was an event recently cancelled (meaning {{USER_NAME}} already handled it)?
- **If project tracker connected (e.g., Linear, GitHub Issues, Jira):** Does a ticket already exist? Has it already been resolved?
- **If messaging connected (e.g., Slack, email):** Did {{USER_NAME}} already handle this? Search outbound messages about this topic. If {{USER_NAME}} sent a message about it, the item is likely handled or in progress.
- **If code host connected (e.g., GitHub, GitLab):** Did {{USER_NAME}} already submit a PR, merge code, or commit changes related to this? Check recent activity.
- **Always (regardless of connectors):** Is this the same item phrased differently? Deduplication pass across all candidates.

For each candidate action item, apply every available cross-check from the list above. The number of checks scales with your connected services — a 2-connector setup uses 2 checks, a 5-connector setup uses all 5. Every check that CAN be run MUST be run before an item is written.

## Source Equality for Action Items

**Meeting transcripts and messages are signals, not facts.** Every action item candidate must be verified against other available sources before being written down. A meeting transcript saying "{{USER_NAME}} will do X" does not mean X is a valid action item — it means X is a *candidate* that must survive the cross-check.

**{{USER_NAME}}'s own actions are the most important signal.** What {{USER_NAME}} has actually DONE (messages sent, meetings cancelled, code committed, PRs submitted) always takes priority over what notes say they should do. If a meeting transcript says "{{USER_NAME}} will send the proposal" but {{USER_NAME}} already sent it (found in outbound messages or sent mail), the item is Done, not To Do.

## Per-Item Reconciliation (Consolidation Mode)

During consolidation runs, every action item being written or updated must go through individual reconciliation. This is the most important step — do not batch or shortcut it.

**For EVERY action item:**

### 1. Check if {{USER_NAME}} already handled it
Search for evidence that {{USER_NAME}} completed or progressed the item:
- Outbound messages or DMs about the topic
- Calendar changes (cancelled events, new events created)
- Code commits, PRs opened or merged
- Documents created or edited
- Session history showing work done with AI tools

If evidence of completion exists, mark the item ✅ Done with a citation to the evidence.

### 2. Do a targeted topic search
Search specifically for the topic keywords across all available connectors. Don't rely on the broad scan — do a focused search for this specific item. This catches context that a general sweep might miss.

### 3. Enrich with specifics
Never write vague action items. If a meeting transcript says "{{USER_NAME}} will PR something," don't write that — search the code host for the actual PR. If a to-do says "contact someone about a project," check messaging and the issue tracker to see if that's already been done and what the actual next steps are.

**Bad:** "Follow up on the deployment issue"
**Good:** "Reply to [Person]'s message in #project-channel about the staging deployment failure (error: connection timeout on service X) — they asked for help debugging at 2:15 PM"

### 4. Apply the cross-check
Run every available cross-check (calendar, issue tracker, messaging, code host, deduplication) against this specific item.

### 5. Write with full context and evidence
- If completed: mark ✅ with evidence (link to the message, calendar change, PR, commit, etc.)
- If partially done: describe what's done and what specifically remains
- If not started: include the full context from all sources, not just the one that surfaced it
- Always include source citations showing which connectors confirmed the item

Update the "Last consolidated" timestamp in the action items file after reconciliation is complete.
