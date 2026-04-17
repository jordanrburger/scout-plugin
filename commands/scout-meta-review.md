---
name: scout-meta-review
description: Run an interactive Scout meta-review — a system-level audit that sits above the individual session types. Checks whether sessions are running, mistake audit is trending well, proposals are flowing, KB files are healthy, and data-source coverage is consistent across session types. Runs in the current conversation.
---

# Scout Meta Review

Run an interactive Scout **Meta Review** — a system-level audit that sits ABOVE the individual session types (briefing, consolidation, dreaming, research, work).

This is NOT a Scout session. It does not read SKILL.md or DREAMING.md. It reviews the Scout system itself: are all the parts working together? Are improvements actually improving things? Is anything rotting, stalling, or drifting?

Run this in the **current conversation** so the user has full visibility. Run it weekly, or whenever something feels off.

---

## Phase 1: System Health Check

Read `scout-config.yaml` first to locate the Scout directory (`scout_dir`) and the user's Slack ID (if Slack is enabled).

### 1a: Session Execution Audit

Check whether Scout sessions are actually running and completing:

```bash
# Count sessions by type in the last 7 days
for type in scout dreaming research; do
  echo "=== $type ==="
  ls -1 <SCOUT_DIR>/.scout-logs/${type}-*.log 2>/dev/null | while read f; do
    mod=$(stat -f '%Sm' -t '%Y-%m-%d' "$f" 2>/dev/null || stat -c '%y' "$f" 2>/dev/null | cut -d' ' -f1)
    echo "$mod $(basename "$f")"
  done | sort -r | head -20
done
```

```bash
# Check for failures
cat <SCOUT_DIR>/.scout-logs/failures.log 2>/dev/null | tail -20
```

```bash
# macOS: check launchd. Linux: check cron.
launchctl list | grep -i scout 2>/dev/null || crontab -l 2>/dev/null | grep -i scout || echo "No scheduled jobs found"
```

**Report:**
- Sessions per day by type (last 7 days)
- Failure rate (failures / total runs)
- Any session types not running at all
- Gaps in schedule (e.g., no afternoon consolidation for 3 days)

### 1b: Git Health

```bash
cd <SCOUT_DIR> && git log --oneline --since="7 days ago" | head -30
cd <SCOUT_DIR> && git status
```

- Are sessions committing? Average commits per day?
- Any uncommitted changes lingering?
- Commit message patterns — are they following conventions (`briefing [HH:MM]:`, `dreaming [HH:MM]:`, `work [HH:MM]:`)?

### 1c: Budget & Cost

```bash
cat <SCOUT_DIR>/.scout-logs/usage-tracker.jsonl 2>/dev/null | tail -20
```

- What's the recent spending trend?
- Any rate limit events?
- Are budget caps being hit?

---

## Phase 2: Quality Trend Analysis

### 2a: Mistake Audit Trends

Read `knowledge-base/scout-mistake-audit.md` and analyze:

1. **Total patterns logged** — how many?
2. **Open vs resolved** — are patterns getting fixed or just accumulating?
3. **Repeat offenders** — which patterns have multiple instances? (These are the systemic failures.)
4. **Age distribution** — are old patterns still open? How old is the oldest unresolved pattern?
5. **Category breakdown** — what types of errors dominate? (data source gaps? KB staleness? false positives? process failures?)

**Verdict:** Is the system getting better, plateauing, or getting worse? Back it up with data.

### 2b: Dreaming Proposals Pipeline

Read `dreaming-proposals.md` (and `dreaming-proposals-archive.md` if it exists):

1. **Total pending** — how many proposals are waiting for review?
2. **Age of oldest pending** — how long has it been waiting?
3. **Throughput** — how many proposals were applied in the last 7 days?
4. **Bottleneck diagnosis** — is the bottleneck proposal generation, review, or application?

**Verdict:** Is the improvement pipeline flowing or clogged?

### 2c: Feedback Signal Analysis

If Slack is connected, read Scout's recent DMs to the user. For the last 7 days of DMs:

1. Count **+1 reactions** (positive signal)
2. Count **-1 reactions** (negative signal)
3. Count **thread replies** that are corrections vs. confirmations
4. Calculate a **signal ratio** (+1 / total reactions)

**Verdict:** Is user satisfaction trending up or down? Any session types consistently getting negative feedback?

---

## Phase 3: Architecture Coherence

### 3a: KB File Health

For every file in `knowledge-base/`:

1. Check **"Last updated" timestamps** — which files haven't been touched in 7+ days?
2. Check **file sizes** — which files are over 200 lines? (Candidates for splitting)
3. Check **wikilink integrity** — sample 10 wikilinks across KB files. Do the targets exist?
4. Check **knowledge-base.md root** — does it link to all projects? Is the session history current?

**Report:** Stale files, oversized files, broken links.

### 3b: Action Items Continuity

Read the last 3 days of action items files. Check:

1. **Carryover integrity** — did all unchecked items from Day N appear on Day N+1? (Or were they dropped?)
2. **Completion tracking** — are completed items being moved to the "Recently Completed" section consistently?
3. **Category hygiene** — are items in the right sections (urgent vs to-do vs watching vs personal)?
4. **Meeting prep** — are prep docs being generated for all calendar meetings?

**Report:** Items that were dropped, miscategorized items, missing prep docs.

### 3c: Ontology & Knowledge Graph

```bash
ls <SCOUT_DIR>/knowledge-base/ontology/entities/*.md 2>/dev/null | wc -l
ls <SCOUT_DIR>/knowledge-base/people/*.md 2>/dev/null | wc -l
ls <SCOUT_DIR>/knowledge-base/personal/*.md 2>/dev/null | wc -l
```

```bash
cd <SCOUT_DIR> && python knowledge-base/ontology/parser.py stats
cd <SCOUT_DIR> && python knowledge-base/ontology/parser.py validate
```

- Is the graph growing?
- Are personal entities being created?
- Does validation pass?
- Quick-check `ontology/schema.yaml` against actual entity frontmatter.

---

## Phase 4: Skill & Session Effectiveness

### 4a: Cross-Skill Consistency

Read all skill files and check for contradictions or gaps:
- `SKILL.md` (briefing/consolidation)
- `DREAMING.md` (dreaming)
- `RESEARCH.md` (research)
- `.claude/commands/scout-work.md` (if installed locally)

Look for:
- Contradictory instructions between skills
- Data sources mentioned in one skill but not others (when they should be shared)
- Formatting conventions that differ between skills
- Commit message formats — consistent?

### 4b: Data Source Coverage Matrix

Build a matrix of which data sources are checked by which session types:

| Source | Briefing | Consolidation | Dreaming | Research | Work |
|--------|----------|---------------|----------|----------|------|
| Slack | ? | ? | ? | ? | ? |
| Gmail | ? | ? | ? | ? | ? |
| Calendar | ? | ? | ? | ? | ? |
| Linear | ? | ? | ? | ? | ? |
| GitHub | ? | ? | ? | ? | ? |
| Claude Code sessions | ? | ? | ? | ? | ? |
| Granola | ? | ? | ? | ? | ? |
| Google Drive | ? | ? | ? | ? | ? |

Flag any session type that SHOULD check a source but doesn't (based on mistake audit patterns).

---

## Phase 5: Report & Fix

### 5a: Generate the Meta Review Report

Write a report to `knowledge-base/meta-review-YYYY-MM-DD.md` with:

1. **System Health Score** (0-10) — based on session execution, failure rate, budget
2. **Quality Trend** (improving / stable / degrading) — based on mistake patterns, feedback signals
3. **Architecture Coherence Score** (0-10) — based on KB health, action items continuity, ontology growth
4. **Top 3 Systemic Issues** — the biggest problems found, with evidence
5. **Top 3 Strengths** — what's working well (so future reviews don't break it)
6. **Recommended Actions** — specific, actionable fixes ranked by impact

### 5b: Apply Quick Fixes

For any issues found that are:
- **Low risk** (formatting, broken links, stale timestamps)
- **Clearly correct** (no judgment call needed)
- **Immediately fixable** (edit a file, not a process change)

Fix them directly. Commit as: `meta-review [HH:MM]: <summary of fix>`

### 5c: Propose Structural Changes

For issues that require:
- Skill file changes → write a dreaming proposal in `dreaming-proposals.md`
- Hook changes → note in the report with a recommended implementation
- New tooling → note in the report for the user's review

### 5d: Present to the User

End by presenting a concise summary in the conversation:

```
## Scout Meta Review — [date]

**Health:** [score]/10 | **Quality trend:** [direction] | **Coherence:** [score]/10

### What's working
- [strength 1]
- [strength 2]

### What needs attention
- [issue 1] — [quick fix applied / proposal written / needs user's decision]
- [issue 2] — ...

### Quick fixes applied
- [fix 1]
- [fix 2]

Full report: knowledge-base/meta-review-YYYY-MM-DD.md
```

---

## Important Notes

- This is a **diagnostic** routine, not an operational one. It doesn't produce action items or scan for today's activity.
- Run this weekly, or when something feels off. It's the "are we actually getting better?" check.
- Be honest in scoring. A 10/10 system doesn't need a meta-review. If things are working perfectly, say so briefly and spend less time here.
- When in doubt about whether to fix something directly vs. propose it, ask the user — this runs interactively for a reason.
