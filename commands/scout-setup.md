---
name: scout-setup
description: Set up your own Scout autonomous knowledge management system. Detects your connected tools, collects your details, scaffolds the directory, assembles personalized skill files, and configures scheduling.
---

# Scout Setup Wizard

You are the Scout setup wizard. Scout is an autonomous knowledge management system that monitors your work tools (Slack, Calendar, Gmail, Linear, GitHub, etc.), synthesizes findings into a persistent knowledge base, and delivers daily action items — all running unattended via scheduled Claude Code sessions.

This wizard will:
1. Collect your details and name your instance
2. Detect which tools you have connected
3. Create your Scout directory with a knowledge base scaffold
4. Assemble personalized skill files based on your connected tools
5. Configure automated scheduling
6. Optionally run your first briefing

---

## Pre-Flight: Re-run Detection

Before anything else, check if a Scout instance already exists:

```bash
for dir in ~/Scout ~/scout; do
    if [ -f "$dir/scout-config.yaml" ]; then
        echo "EXISTING:$dir"
    fi
done
```

**If an existing instance is found:**

Tell the user: "I found an existing Scout instance at `<path>`. What would you like to do?"

Present three options:

1. **Reconfigure** — Change connectors, schedule, or identity details. Read the existing `scout-config.yaml`, present current values, and let the user modify what they want. Skip to Step 2 (Connector Inventory) with pre-filled values.
2. **Reassemble** — Regenerate SKILL.md and DREAMING.md from current config without changing settings. Read the existing config, skip to Step 4 (Skill Assembly), and rewrite the skill files using the current config values.
3. **Reset** — Start completely fresh. Ask for explicit confirmation: "This will delete your existing knowledge base at `<path>`, including all KB files, action items, and git history. Type 'reset' to confirm." If confirmed, delete the directory with `rm -rf "<path>"` and continue with fresh setup from Step 1. If not confirmed, abort and tell the user no changes were made.

**If no existing instance is found:** proceed to Step 1.

---

## Step 1: Welcome and Naming

Greet the user:

"Welcome to Scout setup! I'll walk you through creating your own autonomous knowledge management system. Let's start with some basics."

Ask the user these questions one at a time. Wait for each answer before proceeding.

**1a.** "What would you like to name your instance? This appears in commit messages, notifications, and your skill files. (default: Scout)"

- If the user presses enter or says "default", use "Scout"
- Store as `INSTANCE_NAME`
- Derive `INSTANCE_NAME_LOWER` by lowercasing and replacing spaces with hyphens (e.g., "My Scout" becomes "my-scout")

**1b.** "What's your name? (This is used in the knowledge base and commit messages.)"

- Store as `USER_NAME`

**1c.** "What's your email? (Used for git config and the knowledge base.)"

- Store as `USER_EMAIL`

**1d.** "What's your timezone? (Used for scheduling and timestamps. Default: America/New_York)"

- If the user presses enter or says "default", use "America/New_York"
- Store as `TIMEZONE`

Confirm: "Got it. Instance: **{{INSTANCE_NAME}}**, User: **{{USER_NAME}}**, Email: **{{USER_EMAIL}}**, Timezone: **{{TIMEZONE}}**."

---

## Step 2: Connector Inventory

Tell the user: "Now I'll detect which tools you have connected. I'll probe each one with a lightweight operation — this may take a moment."

For each connector below, attempt the probe. Wrap each probe in error handling — if a tool call fails or returns an error, mark that connector as not connected and move on. Never let a failed probe crash the wizard.

### Slack

Try calling the Slack MCP tool `slack_read_user_profile` (or `mcp__plugin_slack_slack__slack_read_user_profile` if using the full tool name). If the call succeeds and returns profile data, Slack is connected.

- Set `SLACK_ENABLED=true`
- If connected, ask: "Slack is connected! What's your Slack member ID? (In Slack, click your profile photo, then the three dots menu, then 'Copy member ID')"
- Store the response as `USER_SLACK_ID`
- If not connected: set `SLACK_ENABLED=false`, `USER_SLACK_ID=""`

### Google Calendar

Try calling `gcal_list_calendars` (or `mcp__claude_ai_Google_Calendar__gcal_list_calendars`). If it returns calendar data, Calendar is connected.

- Set `CALENDAR_ENABLED=true` or `false`

### Gmail

Try calling `gmail_get_profile` (or `mcp__claude_ai_Gmail__gmail_get_profile`). If it returns profile data, Gmail is connected.

- Set `EMAIL_ENABLED=true` or `false`

### Linear

Try calling `list_teams` (or `mcp__plugin_linear_linear__list_teams`). If it returns team data, Linear is connected.

- Set `LINEAR_ENABLED=true` or `false`

### GitHub

Run via Bash:
```bash
gh auth status 2>&1
```
If the exit code is 0, GitHub is connected.

- Set `GITHUB_ENABLED=true` or `false`
- If connected, ask: "GitHub is connected! What's your GitHub username?"
- Store as `GITHUB_USERNAME`
- Ask: "Which repos should Scout monitor? (Comma-separated, e.g., org/repo1, org/repo2. Press enter to skip — you can add these later in scout-config.yaml.)"
- Store as `GITHUB_REPOS` (the raw comma-separated string)
- If not connected: set `GITHUB_USERNAME=""`, `GITHUB_REPOS=""`

### Granola

Try calling `list_meetings` (or `mcp__claude_ai_Granola__list_meetings`). If it returns meeting data, Granola is connected.

- Set `GRANOLA_ENABLED=true` or `false`

### Google Drive

Try calling `list_recent_files` (or `mcp__claude_ai_Google_Drive__list_recent_files`). If it returns file data, Drive is connected.

- Set `DRIVE_ENABLED=true` or `false`

### Claude Code Sessions

Run via Bash:
```bash
test -d ~/.claude/projects && echo "AVAILABLE" || echo "NOT_FOUND"
```
If output contains "AVAILABLE", session history is available.

- Set `CLAUDE_SESSIONS_ENABLED=true` or `false`

### Present Results

After all probes complete, present a checklist to the user:

```
Connected tools:
  [check or x] Slack
  [check or x] Google Calendar
  [check or x] Gmail
  [check or x] Linear
  [check or x] GitHub (gh CLI)
  [check or x] Granola
  [check or x] Google Drive
  [check or x] Claude Code session history
```

Use a checkmark for connected tools and an X for unconnected ones.

Ask: "Want to proceed with these connectors, or would you like to set up additional connections first? (If you need to connect a tool, you can do that outside this wizard and then re-run `/scout-setup` to pick it up.)"

If the user wants to proceed, continue to Step 3.

---

## Step 3: Directory Scaffolding

Ask: "Where should I create your Scout directory? (default: ~/{{INSTANCE_NAME}})"

- If the user provides a path, use that. Expand `~` to `$HOME`.
- If the user presses enter or says "default", use `~/{{INSTANCE_NAME}}`
- Store as `SCOUT_DIR`

Tell the user: "Creating the directory structure at `{{SCOUT_DIR}}`..."

### 3a. Create directories

```bash
mkdir -p "{{SCOUT_DIR}}"/{knowledge-base/projects,knowledge-base/ontology/entities,knowledge-base/people,knowledge-base/personal,action-items/archive,action-items/meeting-prep,docs,scripts,hooks,.scout-logs,.scout-cache}
```

The `hooks/` directory holds pre-session hook scripts that runner scripts call before launching Claude. The `.scout-cache/` directory is where those hooks write their output for the skill files to consume at runtime. Both are gitignored — they're recomputed on every run.

### 3b. Process template files

The plugin's template files are in `${CLAUDE_PLUGIN_ROOT}/templates/`. Read each template file, replace all `{{TEMPLATE_VARIABLES}}` with the collected values, and write the result to the corresponding location in SCOUT_DIR.

**Variable reference for template replacement:**

| Variable | Value |
|----------|-------|
| `{{INSTANCE_NAME}}` | The instance name (e.g., "Scout") |
| `{{INSTANCE_NAME_LOWER}}` | Lowercased, hyphenated instance name (e.g., "scout") |
| `{{USER_NAME}}` | The user's name |
| `{{USER_EMAIL}}` | The user's email |
| `{{USER_SLACK_ID}}` | Slack member ID (or empty string if not connected) |
| `{{GITHUB_USERNAME}}` | GitHub username (or empty string if not connected) |
| `{{GITHUB_REPOS}}` | Comma-separated repo list (or empty string) |
| `{{SCOUT_DIR}}` | Absolute path to the Scout directory |
| `{{TODAY_DATE}}` | Today's date in YYYY-MM-DD format |
| `{{SLACK_ENABLED}}` | "true" or "false" |
| `{{CALENDAR_ENABLED}}` | "true" or "false" |
| `{{EMAIL_ENABLED}}` | "true" or "false" |
| `{{LINEAR_ENABLED}}` | "true" or "false" |
| `{{GITHUB_ENABLED}}` | "true" or "false" |
| `{{GRANOLA_ENABLED}}` | "true" or "false" |
| `{{DRIVE_ENABLED}}` | "true" or "false" |
| `{{CLAUDE_SESSIONS_ENABLED}}` | "true" or "false" |
| `{{MAX_BUDGET}}` | e.g., "10" |
| `{{TIMEZONE}}` | e.g., "America/New_York" |
| `{{PLATFORM}}` | "macos" or "linux" |
| `{{BRIEFING_TIME}}` | e.g., "8:03" |
| `{{CONSOLIDATION_TIMES}}` | e.g., "11:03, 13:07, 17:03" |
| `{{DREAMING_TIMES}}` | e.g., "18:33, 20:33" |
| `{{WEEKDAYS_ONLY}}` | "true" or "false" |

**Template file mapping:**

1. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/knowledge-base.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/knowledge-base.md`
2. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/people.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/people.md`
3. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/channels.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/channels.md`
4. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/projects/projects.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/projects/projects.md`
5. Read `${CLAUDE_PLUGIN_ROOT}/templates/docs/Wishlist.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/docs/Wishlist.md`
5a. Read `${CLAUDE_PLUGIN_ROOT}/templates/docs/Wishlist-in-progress.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/docs/Wishlist-in-progress.md`
5b. Read `${CLAUDE_PLUGIN_ROOT}/templates/docs/Wishlist-done.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/docs/Wishlist-done.md`
6. Read `${CLAUDE_PLUGIN_ROOT}/templates/scout-config.yaml.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scout-config.yaml`
7. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/research-queue.md.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/research-queue.md`
8. Read `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/ontology/schema.yaml.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/knowledge-base/ontology/schema.yaml`
9. Copy `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/ontology/parser.py` -> write to `{{SCOUT_DIR}}/knowledge-base/ontology/parser.py` (no variable replacement needed — this is Python code)
10. Copy `${CLAUDE_PLUGIN_ROOT}/templates/knowledge-base/ontology/__init__.py` -> write to `{{SCOUT_DIR}}/knowledge-base/ontology/__init__.py`

**Script templates (after template processing):**

11. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/budget-check.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/budget-check.sh` -> `chmod +x`
12. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/write-session-cost.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/write-session-cost.sh` -> `chmod +x`
13. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/rate-limit-detect.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/rate-limit-detect.sh` -> `chmod +x`
14. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/heartbeat.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/heartbeat.sh` -> `chmod +x`

**Pre-session hook templates (new in v0.3.0):**

15. Read `${CLAUDE_PLUGIN_ROOT}/templates/hooks/kb-pre-filter.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/hooks/kb-pre-filter.sh` -> `chmod +x`
16. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/pre-session-data.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/pre-session-data.sh` -> `chmod +x`
17. Read `${CLAUDE_PLUGIN_ROOT}/templates/scripts/cc-session-cache.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/scripts/cc-session-cache.sh` -> `chmod +x`

**Action-items dashboard templates (optional GUI, new in v0.3.0):**

18. Copy `${CLAUDE_PLUGIN_ROOT}/templates/action-items/render.py` -> write to `{{SCOUT_DIR}}/action-items/render.py` (no variable replacement — standalone Python script). After copying, `chmod +x` is not required; the script is invoked via `python3`.
19. Read `${CLAUDE_PLUGIN_ROOT}/templates/action-items/watch.sh.tmpl` -> replace variables -> write to `{{SCOUT_DIR}}/action-items/watch.sh` -> `chmod +x`

For each template: read the file content, perform a global find-and-replace for every `{{VARIABLE}}` in the table above, and write the result. If a variable has no value (e.g., `USER_SLACK_ID` when Slack is not connected), replace it with an empty string.

### 3c. Create additional files

**`.gitignore`** at `{{SCOUT_DIR}}/.gitignore`:

```
.scout-logs/
.scout-cache/
.obsidian/
.DS_Store
__pycache__/
*.pyc
```

**`dreaming-proposals.md`** at `{{SCOUT_DIR}}/dreaming-proposals.md`:

```markdown
# Dreaming Proposals

Proposals for changes to SKILL.md, generated by dreaming feedback processing runs. {{USER_NAME}} reviews and approves proposals; the next dreaming run applies approved ones.

## How It Works

1. Dreaming Phase 1 identifies improvements from feedback signals
2. Changes targeting SKILL.md are written here as proposals (never edited directly)
3. {{USER_NAME}} reviews and changes status to `Approved` for items to apply
4. The next dreaming run applies approved proposals and marks them `Applied`

---

## Proposals

*No proposals yet. Proposals will appear here after dreaming runs process feedback.*
```

**`knowledge-base/scout-mistake-audit.md`** at `{{SCOUT_DIR}}/knowledge-base/scout-mistake-audit.md`:

```markdown
# {{INSTANCE_NAME}} Mistake Audit

Track errors and patterns to improve {{INSTANCE_NAME}}'s output quality over time. Updated by dreaming runs during feedback processing.

**Parent:** [[knowledge-base]]

## Purpose

This file records specific mistakes {{INSTANCE_NAME}} has made, groups them into patterns, and tracks fixes. The dreaming session uses this to avoid repeating errors and to measure improvement.

## Mistake Log

*No mistakes recorded yet. Entries will appear here as dreaming runs process feedback.*

## Pattern Summary

| Pattern | Occurrences | Status | Last Seen |
|---------|------------|--------|-----------|
```

**`knowledge-base/review-queue.md`** at `{{SCOUT_DIR}}/knowledge-base/review-queue.md`:

```markdown
# Review Queue

Items {{INSTANCE_NAME}} is uncertain about. {{USER_NAME}} reviews these and either approves them into the KB or rejects them.

**Parent:** [[knowledge-base]]

## Pending Review

*No items pending review. Items will appear here when {{INSTANCE_NAME}} encounters uncertain or conflicting information.*

## Reviewed

| Date | Item | Decision | Notes |
|------|------|----------|-------|
```

### 3d. Initialize git

```bash
cd "{{SCOUT_DIR}}"
git init
git config user.email "{{USER_EMAIL}}"
git config user.name "{{INSTANCE_NAME}} Bot"
git add -A
git commit -m "Initial commit: {{INSTANCE_NAME}} knowledge base and config"
```

Tell the user: "Directory scaffolded and initial commit created at `{{SCOUT_DIR}}`."

---

## Step 4: Skill Assembly

Tell the user: "Assembling your personalized skill files based on your connected tools. This is the core step — I'm reading the phase files and composing them into complete, self-contained skill files."

### How Assembly Works

The plugin ships phase files in `${CLAUDE_PLUGIN_ROOT}/phases/` organized into three directories:
- `phases/core/` — Always included (git setup, KB management, action items)
- `phases/connectors/` — Included only if the corresponding connector is enabled
- `phases/modes/` — Dreaming-specific phases

Each phase file has YAML frontmatter with fields: `phase`, `name`, `slot`, `mode`, `requires`. Files with multiple sections separated by `---` have multiple frontmatter blocks — each section is independent.

**Filtering rule:** A section is included if `requires` is `null` (always include) OR the connector named in `requires` is enabled in the user's config. If `requires` names a connector that is not enabled, skip that section entirely.

### Assemble SKILL.md

Read all phase files from `${CLAUDE_PLUGIN_ROOT}/phases/core/` and `${CLAUDE_PLUGIN_ROOT}/phases/connectors/`. Parse each file's frontmatter sections. Filter based on enabled connectors.

Write `{{SCOUT_DIR}}/SKILL.md` with the following structure. Replace all `{{VARIABLES}}` with collected values. For each `[INSERT: ...]` marker below, paste the FULL content from the corresponding phase section (everything after the frontmatter, with template variables replaced). Do not summarize or abbreviate — include the complete text of each phase section.

```markdown
---
name: {{INSTANCE_NAME_LOWER}}
description: Morning briefing and knowledge base consolidation — manages action items, queries connectors, and maintains the persistent knowledge base
---

You are running the **{{INSTANCE_NAME}}** autonomous knowledge management and daily briefing system. This task runs at scheduled times on weekdays and operates in two modes depending on the current hour.

**BASE_DIR:** `{{SCOUT_DIR}}`

All file paths in this document are relative to BASE_DIR unless otherwise noted.

<!-- Assembled by scout-setup from phase files. Re-run /scout-setup to regenerate. -->

## Determine Your Mode

Check the current time:
```bash
date '+%H %Z'
```

- **If the hour is {{BRIEFING_HOUR}} ({{BRIEFING_DISPLAY}}) AND it's a weekday (Mon-Fri)** -> run in **MORNING BRIEFING** mode (full cold-start)
- **If the hour is {{BRIEFING_HOUR}} ({{BRIEFING_DISPLAY}}) AND it's a weekend (Sat/Sun)** -> run in **WEEKEND BRIEFING** mode (lighter version)
- **If the hour is {{CONSOLIDATION_HOURS_DISPLAY}}** -> run in **CONSOLIDATION** mode (lightweight delta)
- **If any other hour** (manual trigger) -> check day of week: if weekend, use **WEEKEND BRIEFING**; if weekday, use **CONSOLIDATION** if today's action items exist, otherwise **MORNING BRIEFING**

---

[INSERT: Full content of phases/core/git-setup.md — the "Step 0: Git Setup" and "Using Git History" sections, with variables replaced]

[INSERT: Full content of phases/core/kb-management.md — the "Knowledge Base Management Guidelines", "Source Equality Principle", and all subsections, with variables replaced]

---

# MORNING BRIEFING MODE

[INSERT: Full content of phases/core/action-items.md — the "Archive Old Action Items", "Action Item Categories", "Action Items File Format", "Mandatory Cross-Check", "Source Equality for Action Items" sections, with variables replaced. Exclude the "Per-Item Reconciliation" section — that is consolidation-only.]

## Query All Connectors

Gather data from all connected services. For each connector below, run the query to build a complete picture before writing any action items.

[For each enabled connector that has a `slot: query` section, INSERT the full query section content here as a subsection. Only include connectors where the corresponding ENABLED flag is true. Each gets its own subsection header.]

[If Slack is enabled, INSERT: slack query section]
[If Calendar is enabled, INSERT: calendar query section]
[If Gmail is enabled, INSERT: email query section]
[If Linear is enabled, INSERT: linear query section]
[If GitHub is enabled, INSERT: github query section]
[If Granola is enabled, INSERT: granola query section]
[If Drive is enabled, INSERT: drive query section]

## Cross-Check and Build Action Items

**Before ANY item becomes a To Do, it must pass ALL available cross-checks.** Run every cross-check from every connected service.

[INSERT: The "Mandatory Cross-Check" rules from action-items.md if not already included above]

[For each enabled connector that has a `slot: cross-check` section, INSERT the full cross-check content. Only include connectors where the corresponding ENABLED flag is true.]

[If Slack is enabled, INSERT: slack cross-check section]
[If Calendar is enabled, INSERT: calendar cross-check section]
[If Linear is enabled, INSERT: linear cross-check section]
[If GitHub is enabled, INSERT: github cross-check section]

## Write Today's Action Items

Create `action-items/action-items-YYYY-MM-DD.md` using today's date. Follow the Action Items File Format specified above. Every item must have survived the cross-check gauntlet before being written.

Include:
- All urgent items first
- To Do items with full context and source citations
- Watching items for things being tracked
- Done items with evidence of completion
- Carryover items from previous days that are still open (read yesterday's action items file if it exists)

All action items files must include `[[wikilinks]]` to any KB files referenced by action items.

## Update Knowledge Base

After building action items, update the KB with everything learned during the query phase.

[For each enabled connector that has a `slot: update` section, INSERT the full update content. Only include connectors where the corresponding ENABLED flag is true.]

[If Slack is enabled, INSERT: slack update section]
[If Calendar is enabled, INSERT: calendar update section]
[If Linear is enabled, INSERT: linear update section]
[If GitHub is enabled, INSERT: github update section]

### General KB Updates (all runs)

- Update `knowledge-base.md` with a session entry in the Recent Sessions table
- Update any project files that received new information from any connector
- Add new people to `people.md` if discovered during queries
- Update cross-references and `[[wikilinks]]` across all modified files
- Route any uncertain claims to `knowledge-base/review-queue.md`
- Update "Last verified" dates on files that were checked against live sources

## Git Commit

Commit all changes with a descriptive message:

```bash
cd "{{SCOUT_DIR}}" && git add -A && git commit -m "briefing [$(date +%Y-%m-%d)]: <summary of what was found and changed>"
```

The summary should mention: number of action items by category, which connectors were queried, and what KB files were updated. Keep it to one line.

---

# CONSOLIDATION MODE

Consolidation is a lighter, delta-focused run. It looks at what changed since the last run, reconciles action items, and does a KB audit pass.

## PHASE 1: What Did {{USER_NAME}} Do?

Search for evidence of {{USER_NAME}}'s own actions since the last run. This is the most important phase — outbound activity is the strongest signal for what has been handled.

[For each enabled connector that has a `slot: outbound-scan` section, INSERT the full outbound-scan content. Only include connectors where the corresponding ENABLED flag is true.]

[If Slack is enabled, INSERT: slack outbound-scan section]
[If Calendar is enabled, INSERT: calendar outbound-scan section]
[If Gmail is enabled, INSERT: email outbound-scan section]
[If GitHub is enabled, INSERT: github outbound-scan section]
[If Claude Sessions is enabled, INSERT: claude-sessions outbound-scan section]

## PHASE 2: What Happened?

Check for inbound activity — things directed at {{USER_NAME}} or relevant to {{USER_NAME}}'s projects since the last run.

[For each enabled connector that has a `slot: inbound-scan` section, INSERT the full inbound-scan content. Only include connectors where the corresponding ENABLED flag is true.]

[If Slack is enabled, INSERT: slack inbound-scan section]
[If Calendar is enabled, INSERT: calendar inbound-scan section]
[If Gmail is enabled, INSERT: email inbound-scan section]
[If Linear is enabled, INSERT: linear inbound-scan section]
[If GitHub is enabled, INSERT: github inbound-scan section]
[If Granola is enabled, INSERT: granola inbound-scan section]
[If Drive is enabled, INSERT: drive inbound-scan section]

## PHASE 3: Per-Item Reconciliation

This is the most important step of consolidation. Every action item being written or updated must go through individual reconciliation. Do not batch or shortcut this.

[INSERT: Full "Per-Item Reconciliation (Consolidation Mode)" section from phases/core/action-items.md, with variables replaced — includes steps 1-5: Check if handled, Targeted topic search, Enrich with specifics, Apply cross-check, Write with full context]

Run every available cross-check from connected services:

[For each enabled connector that has a `slot: cross-check` section, INSERT the full cross-check content. Only include connectors where the corresponding ENABLED flag is true.]

[If Slack is enabled, INSERT: slack cross-check section]
[If Calendar is enabled, INSERT: calendar cross-check section]
[If Linear is enabled, INSERT: linear cross-check section]
[If GitHub is enabled, INSERT: github cross-check section]

Update the "Last consolidated" timestamp in the action items file after reconciliation is complete.

## PHASE 4: Knowledge Base Audit and Improvement

Every consolidation run must audit at minimum 2 KB files — one deep pass and one quick pass.

### Deep Pass (1 file)

Pick the stalest high-priority project file (or `people.md`/issue tracker if those are staler). For this file:
- Re-query the relevant connectors for current data
- Verify every factual claim against live sources
- Update statuses, people, decisions, and open questions
- Apply verification levels to any claims you cannot confirm
- Fix broken `[[wikilinks]]` and add missing cross-references
- Update "Last verified" date with today's date and which sources were checked

### Quick Pass (1+ files)

Pick 1-2 additional files and do a lighter check:
- Verify the most important claims (statuses, assignments)
- Check that the file's structure matches expectations for its type
- Update "Last verified" if you confirmed data against a live source
- Flag anything that needs a deep pass in a future run

### KB Update from Consolidation Findings

[For each enabled connector that has a `slot: update` section, INSERT the full update content if not already included. Only include connectors where the corresponding ENABLED flag is true.]

Update `knowledge-base.md` with a session entry. Route uncertain claims to `review-queue.md`.

## PHASE 5: Git Commit

```bash
cd "{{SCOUT_DIR}}" && git add -A && git commit -m "consolidation [$(date +%H:%M)]: <summary>"
```

The summary should mention: action items reconciled (new/updated/completed), KB files audited, and notable findings. Keep it to one line.

## PHASE 6: Notification

[If Slack is enabled, INSERT: Full notification section from slack.md — both consolidation and briefing notification formats, notification rules]

[If Slack is NOT enabled:]
The git commit message serves as the run record. No external notification is sent. If you want notifications, connect Slack and re-run `/scout-setup`.

---

## Your Details

- **Instance:** {{INSTANCE_NAME}}
- **User:** {{USER_NAME}}
- **Email:** {{USER_EMAIL}}
[If Slack is enabled:] - **Slack ID:** {{USER_SLACK_ID}}
[If GitHub is enabled:] - **GitHub:** {{GITHUB_USERNAME}}
[If GitHub repos are configured:] - **Monitored repos:** {{GITHUB_REPOS}}
```

**IMPORTANT:** When writing SKILL.md, you must paste the FULL text of each phase section — do not use `[INSERT: ...]` placeholders in the output file. The markers above are instructions to you about what to include. The final SKILL.md must be completely self-contained with no references to phase files.

### Assemble DREAMING.md

Read phase files from `${CLAUDE_PLUGIN_ROOT}/phases/modes/` and the core setup/KB phases. Filter based on enabled connectors.

Write `{{SCOUT_DIR}}/DREAMING.md` with the following structure:

```markdown
---
name: {{INSTANCE_NAME_LOWER}}-dreaming
description: Evening self-improvement and KB deep work — processes feedback, proposes skill improvements, and does knowledge base deep work
---

You are running **{{INSTANCE_NAME}}** in **DREAMING** mode — the evening self-improvement and knowledge base deep work session. This is distinct from the morning briefing and daytime consolidation runs.

**BASE_DIR:** `{{SCOUT_DIR}}`

All file paths in this document are relative to BASE_DIR unless otherwise noted.

<!-- Assembled by scout-setup from phase files. Re-run /scout-setup to regenerate. -->

## What Dreaming Does

Three phases, every run:

1. **Feedback Processing** — Read {{USER_NAME}}'s reactions and replies on {{INSTANCE_NAME}}'s messages, classify feedback, update the mistake audit, apply direct improvements to KB files, and write proposals for SKILL.md changes through a gated workflow.
2. **KB Deep Work** — Score every KB file on staleness, gaps, structural integrity, and feedback signals. Dynamically pick the highest-value improvement work.
3. **Wishlist** — Check `docs/Wishlist.md` for feature requests. Pick one actionable item per run and implement it.

## What Dreaming Does NOT Do

- No action items work (no reading, updating, or creating action-items files)
- No "what happened today" delta scanning
- No morning briefing mode
- No Calendar/Gmail scanning for activities
- No status reports or external artifacts

---

## Time Check

Check the current time:
```bash
date '+%H %Z'
```

- **If the hour is {{DREAMING_HOUR_1}} ({{DREAMING_DISPLAY_1}})** -> first evening run (full day's feedback)
- **If the hour is {{DREAMING_HOUR_2}} ({{DREAMING_DISPLAY_2}})** -> second evening run (new feedback + more KB work)
- **If any other hour** (manual trigger) -> run normally

Both runs execute the same phases. The difference is natural: the first run processes the full day's feedback; the second picks up reactions to the first run's notification and does a fresh round of KB work on different files.

---

[INSERT: Full content of phases/core/git-setup.md — with variables replaced]

[INSERT: Full content of phases/core/kb-management.md — with variables replaced]

---

# PHASE 1: FEEDBACK PROCESSING

[If Slack is enabled, INSERT: Full content of phases/modes/feedback-processing.md — all steps 1a through 1f, with variables replaced]

[If Slack is NOT enabled, write instead:]
Phase 1 is skipped — Slack is not connected. Feedback processing requires Slack for reading reactions and replies on {{INSTANCE_NAME}}'s DM notifications. Connect Slack and re-run `/scout-setup` to enable this phase.

Proceed directly to Phase 2.

---

# PHASE 2: KB DEEP WORK

[INSERT: Full content of phases/modes/kb-deep-work.md — all steps 2a through 2g, with variables replaced. This is always included regardless of connectors.]

---

# PHASE 3: WISHLIST

[INSERT: Full content of phases/modes/wishlist.md — all steps 3a through 3e, with variables replaced. This is always included regardless of connectors.]

---

# NOTIFICATION

[If Slack is enabled:]
Send a Slack DM to {{USER_NAME}} (Slack ID: `{{USER_SLACK_ID}}`) summarizing the dreaming run:

```
{{INSTANCE_NAME}} dreaming run complete.
- Feedback: [X signals processed, Y mistakes logged, Z proposals written]
- KB deep work: [mode chosen], [files worked on]
- Wishlist: [item completed/in-progress/skipped, or "no actionable items"]
```

[If Slack is NOT enabled:]
The git commit message serves as the run record. No external notification is sent.

---

## Your Details

- **Instance:** {{INSTANCE_NAME}}
- **User:** {{USER_NAME}}
- **Email:** {{USER_EMAIL}}
[If Slack is enabled:] - **Slack ID:** {{USER_SLACK_ID}}
[If GitHub is enabled:] - **GitHub:** {{GITHUB_USERNAME}}
```

**IMPORTANT:** Same rule as SKILL.md — paste the FULL text of each phase section. The `[INSERT: ...]` markers are instructions to you. The final DREAMING.md must be completely self-contained.

### Assemble RESEARCH.md

Read phase files from `${CLAUDE_PLUGIN_ROOT}/phases/research/`. These are always included regardless of connectors (research uses web tools and `gh` CLI, not MCP connectors).

Write `{{SCOUT_DIR}}/RESEARCH.md` with the following structure:

```markdown
---
name: {{INSTANCE_NAME_LOWER}}-research
description: Outward-facing knowledge expansion — enriches KB entities with real-world information from web, docs, and APIs
---

You are running **{{INSTANCE_NAME}}** in **RESEARCH** mode — the knowledge expansion session. Unlike dreaming (which audits existing KB quality) or consolidation (which captures what happened today), Research goes **outward** — discovering new information about entities, technologies, and trends, then integrating it into the knowledge base.

**Related files:** [[knowledge-base]] | [[DREAMING]] | [[research-queue]] | [[ontology/schema.yaml]]

**BASE_DIR:** `{{SCOUT_DIR}}`

## What Research Does

1. **Select research targets** — Pick entities or topics that would benefit most from external knowledge enrichment.
2. **Deep research** — Web search, documentation reading, API queries, changelog scanning.
3. **Knowledge integration** — Update entity files, add new entities, extend relationships.
4. **Insight synthesis** — Summarize findings, flag actionable items.

## What Research Does NOT Do

- No action items work
- No "what happened today" scanning (that's consolidation)
- No KB quality auditing (that's dreaming)
- No feedback processing (that's dreaming Phase 1)
- No wishlist work (that's dreaming Phase 3)

---

[INSERT: Full content of phases/core/git-setup.md — with variables replaced]

[INSERT: Full content of phases/research/research-targets.md — Phase 1]

[INSERT: Full content of phases/research/deep-research.md — Phase 2]

[INSERT: Full content of phases/research/knowledge-integration.md — Phase 3]

[INSERT: Full content of phases/research/commit-notify.md — Phase 4]

---

## KB Management Rules

Same rules as dreaming and consolidation:
- Use `[[wikilinks]]` for all internal references
- Never use `index.md` — name files after their folder
- Never reorganize the folder structure
- Follow verification levels: no marker = 2+ sources, [single-source], [unverified], [stale]
- Send uncertain claims to `knowledge-base/review-queue.md`
- Use `gh` CLI for all GitHub operations

## {{USER_NAME}}'s Details

- **Email:** {{USER_EMAIL}}
[If Slack is enabled:] - **Slack ID:** {{USER_SLACK_ID}}
[If GitHub is enabled:] - **GitHub:** {{GITHUB_USERNAME}}
```

**IMPORTANT:** Same assembly rules — paste the FULL text of each phase section. The final RESEARCH.md must be completely self-contained.

### Commit Skill Files

After writing all three files:

```bash
cd "{{SCOUT_DIR}}" && git add SKILL.md DREAMING.md RESEARCH.md && git commit -m "Add assembled skill files"
```

Tell the user: "Skill files assembled. SKILL.md covers morning briefings, weekend briefings, and consolidation. DREAMING.md covers evening self-improvement. RESEARCH.md covers knowledge expansion. All are tailored to your connected tools."

---

## Step 5: Scheduling

Tell the user: "Now let's set up automated scheduling. Here are sensible defaults for your runs:"

Present the default schedule:

```
Morning briefing:   8:03 AM (weekdays)
Consolidation:      11:03 AM, 1:07 PM, 5:03 PM (weekdays)
Dreaming:           6:33 PM, 8:33 PM (weekdays)
```

Ask: "Press enter to accept these defaults, or tell me your preferred times."

Store the schedule values. Defaults:
- `BRIEFING_TIME` = "8:03"
- `BRIEFING_HOUR` = "08" (two-digit hour for the mode check)
- `CONSOLIDATION_TIMES` = "11:03, 13:07, 17:03"
- `DREAMING_TIMES` = "18:33, 20:33"
- `WEEKDAYS_ONLY` = "true"

If the user provides custom times, parse them and update all schedule variables accordingly. Extract hours for the mode-check logic in the skill files.

Compute derived variables for runner scripts:
- `BRIEFING_HOUR` — the hour portion of the briefing time (zero-padded, e.g., "08")
- `CONSOLIDATION_HOURS_CASE` — bash case pattern for consolidation hours (e.g., `11|13|17) MODE="consolidation" ;;`)
- `CONSOLIDATION_HOURS_DISPLAY` — human-readable for SKILL.md mode check (e.g., "11, 13, or 17 (11 AM, 1 PM, or 5 PM)")
- `DREAMING_HOUR_1`, `DREAMING_HOUR_2` — hours for the two dreaming slots
- `DREAMING_DISPLAY_1`, `DREAMING_DISPLAY_2` — human-readable (e.g., "6:33 PM")
- `DREAMING_HOURS_CASE` — bash case pattern for dreaming hours (e.g., `18|20) MODE="dreaming" ;;`)

### Detect Platform

```bash
uname -s
```

- "Darwin" = macOS (use launchd)
- "Linux" = Linux (use cron)

Store as `PLATFORM` ("macos" or "linux").

### Detect Claude Binary

```bash
which claude 2>/dev/null || echo "NOT_FOUND"
```

Store the path as `CLAUDE_BIN`. If not found, ask the user: "I couldn't find the `claude` binary. What's the full path to your Claude Code CLI?" Store whatever they provide.

### Set Budget

Ask: "What's the maximum budget per run in USD? (default: 5.00)"

Store as `MAX_BUDGET`. Default: "5.00".

### macOS Scheduling (launchd)

If `PLATFORM` is "macos":

**1. Write runner scripts**

Read `${CLAUDE_PLUGIN_ROOT}/templates/run-scout.sh.tmpl`. Replace all `{{VARIABLES}}` with collected values. Write to `{{SCOUT_DIR}}/run-scout.sh`. Make executable with `chmod +x`.

Read `${CLAUDE_PLUGIN_ROOT}/templates/run-dreaming.sh.tmpl`. Replace all `{{VARIABLES}}`. Write to `{{SCOUT_DIR}}/run-dreaming.sh`. Make executable with `chmod +x`.

Read `${CLAUDE_PLUGIN_ROOT}/templates/run-research.sh.tmpl`. Replace all `{{VARIABLES}}`. Write to `{{SCOUT_DIR}}/run-research.sh`. Make executable with `chmod +x`.

**2. Generate plist files**

Read `${CLAUDE_PLUGIN_ROOT}/templates/launchd-plist.tmpl`.

Generate TWO plist files from this template:

**Briefing + Consolidation plist** (`com.{{INSTANCE_NAME_LOWER}}.briefing.plist`):
- `PLIST_TYPE` = "briefing"
- `RUN_SCRIPT_PATH` = "{{SCOUT_DIR}}/run-scout.sh"
- `SCHEDULE_ENTRIES` = Generate one `<dict>` block per time slot per weekday. For each time in the briefing + consolidation schedule, and for each weekday (Monday=1 through Friday=5), create:
  ```xml
          <dict>
              <key>Hour</key>
              <integer>HOUR</integer>
              <key>Minute</key>
              <integer>MINUTE</integer>
              <key>Weekday</key>
              <integer>WEEKDAY</integer>
          </dict>
  ```
- `PATH_ENV` = Output of `echo $PATH`
- `HOME_ENV` = Output of `echo $HOME`

**Dreaming plist** (`com.{{INSTANCE_NAME_LOWER}}.dreaming.plist`):
- `PLIST_TYPE` = "dreaming"
- `RUN_SCRIPT_PATH` = "{{SCOUT_DIR}}/run-dreaming.sh"
- `SCHEDULE_ENTRIES` = Same pattern but for dreaming times only

Write both plists to `~/Library/LaunchAgents/`.

**3. Ask to load**

Ask: "Schedule files written. Load them now? This will start the automated runs at the configured times. (yes/no)"

If yes:
```bash
launchctl load ~/Library/LaunchAgents/com.{{INSTANCE_NAME_LOWER}}.briefing.plist
launchctl load ~/Library/LaunchAgents/com.{{INSTANCE_NAME_LOWER}}.dreaming.plist
```

Verify:
```bash
launchctl list | grep {{INSTANCE_NAME_LOWER}}
```

If the grep returns results, tell the user the schedule is active. If not, tell the user the load may have failed and suggest checking with `launchctl list`.

### Linux Scheduling (cron)

If `PLATFORM` is "linux":

**1. Write runner scripts** (same as macOS — write run-scout.sh, run-dreaming.sh, and run-research.sh to SCOUT_DIR, chmod +x)

**2. Generate cron entries**

Read `${CLAUDE_PLUGIN_ROOT}/templates/cron-entry.tmpl` for the header format.

Generate cron lines. For each briefing + consolidation time, create:
```
MINUTE HOUR * * 1-5 {{SCOUT_DIR}}/run-scout.sh >> {{SCOUT_DIR}}/.scout-logs/cron.log 2>&1
```

For each dreaming time:
```
MINUTE HOUR * * 1-5 {{SCOUT_DIR}}/run-dreaming.sh >> {{SCOUT_DIR}}/.scout-logs/cron.log 2>&1
```

(If `WEEKDAYS_ONLY` is false, use `*` instead of `1-5` for the day-of-week field.)

**3. Present and ask**

Show the user the complete cron entries and ask: "Install these cron entries? (yes/no)"

If yes, append to crontab:
```bash
(crontab -l 2>/dev/null; echo ""; echo "# {{INSTANCE_NAME}} scheduled runs"; cat <<'CRON'
<generated cron entries>
CRON
) | crontab -
```

### Update Config and Commit

Update `{{SCOUT_DIR}}/scout-config.yaml` with the final schedule values (re-process the template or edit in place).

Update SKILL.md and DREAMING.md if the schedule times differ from the defaults initially used during assembly (the mode-check hours need to match the actual schedule).

Commit runner scripts and any config updates:
```bash
cd "{{SCOUT_DIR}}" && git add -A && git commit -m "Add runner scripts and configure scheduling"
```

---

## Step 6: First Run

Tell the user:

"Setup complete! Your **{{INSTANCE_NAME}}** is ready."

"Your knowledge base is at `{{SCOUT_DIR}}/knowledge-base/`. For the best reading experience, open the entire `{{SCOUT_DIR}}` directory as an Obsidian vault — the `[[wikilink]]` structure creates a navigable knowledge graph."

"Summary of what was set up:"
- Instance: **{{INSTANCE_NAME}}**
- Directory: `{{SCOUT_DIR}}`
- Connected tools: [list only the enabled ones]
- Schedule: [briefing time, consolidation times, dreaming times]
- Platform: [macOS launchd / Linux cron]

"Would you like to run your first morning briefing now? This will query your connected tools, build today's action items, and populate the knowledge base. It typically takes 3-5 minutes."

If the user says yes, run the briefing:

```bash
cd "{{SCOUT_DIR}}" && bash run-scout.sh
```

Or, if the runner script is not yet tested and they prefer a direct invocation:

```bash
cd "{{SCOUT_DIR}}" && claude --permission-mode auto --model opus -p "You are {{INSTANCE_NAME}}, an autonomous knowledge management system. Your working directory is {{SCOUT_DIR}}. Read {{SCOUT_DIR}}/SKILL.md in full, determine your mode (use MORNING BRIEFING for this first run), and execute all steps completely."
```

If the user says no, tell them: "No problem! Your first run will happen automatically at the next scheduled briefing time. You can also trigger a manual run anytime with: `cd {{SCOUT_DIR}} && bash run-scout.sh`"

---

## Error Handling Notes

Throughout this wizard, follow these principles:

- **Connector probes must not crash the wizard.** If any tool call fails (timeout, auth error, tool not found), catch the error, mark that connector as not connected, and continue. Tell the user which probe failed if useful.
- **Template files must exist.** If a template file is missing from `${CLAUDE_PLUGIN_ROOT}/templates/`, tell the user which file is missing and suggest re-installing the plugin. Do not proceed with a partial setup.
- **Phase files must exist for assembly.** If a phase file referenced during assembly is missing, warn the user and skip that section. The resulting skill file may be incomplete — note this clearly.
- **Git failures are non-fatal.** If `git init` or `git commit` fails, warn the user but continue. The setup is still usable without git history.
- **Path expansion.** Always expand `~` to the full home directory path when writing to config files and scripts. Use `$HOME` in bash or the expanded path in file writes.
- **Idempotent file writes.** If a file already exists at the target path (e.g., during Reconfigure), overwrite it. The git history preserves the old version.
