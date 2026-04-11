---
phase: mode
name: kb-deep-work
slot: dreaming-phase-2
mode: [dreaming]
requires: null
---

## Phase 2: KB Deep Work

This is the substantive knowledge-base improvement phase. Score every KB file, pick a work mode, execute deep improvements, and leave the KB meaningfully better than you found it.

---

### Step 2a: Score All KB Files

Read every file in `knowledge-base/`. Score each file on four dimensions (0-3 each). Total possible score: 12. Higher scores = higher priority for work.

#### Dimension 1: Staleness (0-3)

Compare each file's "Last verified" or "Last updated" date against the freshness standard for its type. Score based on how far overdue the file is.

| File Type | Freshness Standard | Score 0 | Score 1 | Score 2 | Score 3 |
|---|---|---|---|---|---|
| High priority projects | 3 days | Within 3d | 3-4d overdue | 4-6d overdue | >6d overdue |
| Medium priority projects | 7 days | Within 7d | 7-10d overdue | 10-14d overdue | >14d overdue |
| Low priority projects | 14 days | Within 14d | 14-21d overdue | 21-28d overdue | >28d overdue |
| `people.md` | 7 days | Within 7d | 7-10d overdue | 10-14d overdue | >14d overdue |
| Issue tracker file | Every run | Updated this run | 1 run behind | 2 runs behind | 3+ runs behind |
| `channels.md` | 14 days | Within 14d | 14-21d overdue | 21-28d overdue | >28d overdue |
| `knowledge-base.md` (root) | Every run | Updated this run | 1 run behind | 2 runs behind | 3+ runs behind |

If a file has no "Last verified" date at all, assign staleness score 3 automatically.

#### Dimension 2: Gaps (0-3)

Assess missing content relative to what a file of this type should contain (see KB management guidelines for expected sections).

| Score | Meaning |
|---|---|
| 3 | Severely thin — missing multiple expected sections, stub-level content |
| 2 | Missing 1-2 important sections that would materially help {{USER_NAME}} |
| 1 | Reasonably complete — one area could be expanded for better coverage |
| 0 | Comprehensive — all expected sections present with substantive content |

#### Dimension 3: Structural Integrity (0-3)

Assess navigation, cross-references, and formatting.

| Score | Meaning |
|---|---|
| 3 | Multiple broken or missing `[[wikilinks]]`, not linked from parent file, orphaned from the KB graph |
| 2 | Missing 2+ expected `[[wikilinks]]`, verification levels not applied to claims |
| 1 | One missing wikilink or minor formatting inconsistency |
| 0 | Well-linked, properly formatted, all cross-references intact |

#### Dimension 4: Feedback Signal (0-3)

Based on findings from Phase 1 (feedback processing). If Phase 1 was skipped (no Slack), all files score 0 on this dimension.

| Score | Meaning |
|---|---|
| 3 | Explicit negative feedback about this file's topic (e.g., "the info about project X was wrong") |
| 2 | This file's topic was mentioned in feedback (positive or negative) |
| 1 | Related to a feedback signal (e.g., a person mentioned in feedback has a project file) |
| 0 | No feedback signal related to this file |

#### Scoring Rules

- **Total** = Staleness + Gaps + Structural Integrity + Feedback Signal (max 12).
- **Tiebreaker**: Feedback Signal score wins ties. A file with score 7 (including Feedback 3) ranks above a file with score 7 (Feedback 0).
- **Deprioritize same-day work**: Files that were audited earlier the same calendar day by a consolidation or briefing run get -3 to their total (minimum 0). This creates natural rotation between daytime and nighttime work.

Record the scoring table for the session log.

---

### Step 2b: Pick Work Mode

Based on the scoring distribution, select a work mode:

**Deep Dive** (when any file scores 8 or higher):
- Pick the highest-scoring file.
- Perform a full audit: query ALL available connectors for the topic of that file.
- Rewrite sections as needed. Verify every claim against live sources.
- Goal: bring the file from its current state to comprehensive and verified.

**Gap Hunt** (when many files score 4-7, but nothing scores 8+):
- Scan across the KB for systemic gaps: missing projects, people who appear in connectors but not in `people.md`, decisions made but not logged, channels used but not tracked.
- Create new files or sections as needed.
- Goal: fill the biggest holes in KB coverage.

**Structural Pass** (when staleness and gaps are low but structural scores are high):
- Fix broken and missing `[[wikilinks]]` across the KB.
- Verify the KB graph: every file reachable from `knowledge-base.md`, no orphans.
- Apply verification levels (`[single-source]`, `[unverified]`, etc.) to claims that lack them.
- Goal: make the KB navigable and trustworthy.

**Blended**: You can combine modes within a single run. For example, deep-dive one file and then do a quick structural pass on related files. Use judgment based on the scoring distribution.

---

### Step 2c: Execute

Perform the selected work. During execution:

- **Query connectors as needed.** You have full access to all connected tools for the purpose of KB improvement. Use them to verify claims, fill gaps, and gather fresh data.
- **Follow all KB management guidelines** from the `kb-management` phase. Apply verification levels, maintain cross-references, use `[[wikilinks]]`, and route uncertain claims to `review-queue.md`.
- **Update "Last verified" dates** on every file you touch, noting which sources were checked.
- **Do not duplicate daytime work.** If a consolidation run already updated a file today, focus on areas that run did not cover rather than re-verifying the same data.

---

### Step 2d: Depth Self-Check (HARD GATE)

Before proceeding to commit, answer this question honestly:

> "If {{USER_NAME}} read the KB files I touched tonight, would they learn something they didn't know before?"

**If YES**: proceed to commit.

**If NO**: the work was superficial. Go back to Step 2c and find real work:
- Update a "Last verified" date without actually verifying anything? Not real work.
- Fix a typo and nothing else? Not real work.
- Add a wikilink to a file that already had adequate navigation? Not real work.
- Rephrase existing content without adding information? Not real work.

Real work means: new facts verified from live sources, stale information corrected with current data, missing context filled in, genuinely broken navigation fixed.

This gate exists because the easiest failure mode of an automated KB system is busywork that looks productive but adds no value. Do not pass this gate unless the work is substantive.

---

### Step 2e: Commit

```bash
git -C {{SCOUT_DIR}} add -A && git -C {{SCOUT_DIR}} commit -m "dreaming [HH:MM]: KB deep work — <summary>"
```

The summary should describe what was improved: e.g., "deep dive on project-alpha (verified 12 claims, updated status, added 3 decisions)" or "gap hunt: added 4 missing people, created channel entries for 2 new channels."

---

### Step 2f: Track Work

Add a session entry to the Recent Sessions table in `knowledge-base.md`:

| Date | Time | Mode | Summary |
|---|---|---|---|
| [today] | [HH:MM] | Dreaming | [Brief description of Phase 1 + Phase 2 + Phase 3 work] |

Include:
- What feedback was processed (or "no feedback signals")
- Which KB files were worked on and what was improved
- Any wishlist items completed
- The scoring table or at least the top-3 scored files and their totals

---

### Step 2g: Complement Daytime Runs

Dreaming runs should complement, not duplicate, daytime consolidation and briefing runs. Strategies:

- **Deprioritize same-day files**: Files audited by a consolidation run earlier today get the -3 scoring penalty (see Step 2a).
- **Prefer different dimensions**: If daytime runs focused on staleness (re-verifying current state), nighttime can focus on gaps (adding missing context) or structural integrity (fixing navigation).
- **Go deeper**: Daytime runs often do quick spot-checks. Dreaming runs can do full audits — querying multiple connectors for a single topic, verifying every claim in a file, expanding thin sections.
- **Cover the long tail**: Daytime runs naturally prioritize high-priority, frequently-changing files. Dreaming runs should pick up medium and low priority files that rarely get attention.

This creates a natural rotation where the full KB gets regular coverage without redundant work.
