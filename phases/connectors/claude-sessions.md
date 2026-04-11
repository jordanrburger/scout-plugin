---
phase: connector
name: claude-sessions
slot: outbound-scan
mode: [consolidation]
requires: claude_sessions
---

## Claude Sessions Outbound Scan — What {{USER_NAME}} Worked On

Scan recent Claude Code sessions to understand what {{USER_NAME}} worked on with AI assistance. This catches work that may not appear in other connectors — code written but not yet committed, research done, documents drafted, bugs debugged, or plans created.

### Find Recent Sessions

```bash
# Find session files modified in the last 24 hours
find ~/.claude/projects -name "*.jsonl" -mtime -1 2>/dev/null
```

### Scan Session History

```bash
# Quick scan of recent user prompts with project context
tail -50 ~/.claude/history.jsonl 2>/dev/null | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        d = json.loads(line)
        proj = d.get('project', '?').split('/')[-1][:30]
        print(f\"{d['timestamp']} | {proj} | {d['display'][:100]}\")
    except (json.JSONDecodeError, KeyError):
        pass
"
```

### What to Look For

Session history reveals what {{USER_NAME}} spent time on. Common patterns:

- **PRs created or worked on** — if {{USER_NAME}} used Claude to help with a PR, the PR likely exists (cross-check with GitHub). The action item for that work may be Done or In Progress.
- **Bugs debugged** — if {{USER_NAME}} was debugging something, the bug may now be fixed. Check for commits or PR activity.
- **Documents written** — if {{USER_NAME}} drafted a document or proposal, it may have been sent or shared (check email, Drive, Slack).
- **Research completed** — if {{USER_NAME}} was researching a topic, the research phase of that action item may be Done.
- **Code reviewed** — if {{USER_NAME}} used Claude to help review code, that review may have been submitted (check GitHub).
- **Plans created** — if {{USER_NAME}} made implementation plans, the underlying work may be starting or in progress.

### Matching Sessions to Action Items

For each session activity found:
1. Identify which project or action item it relates to
2. Check if the work resulted in a tangible output (commit, PR, message, document)
3. If a corresponding action item exists, update its status based on the session evidence
4. If the session reveals new work not yet tracked, note it as context for the consolidation

This connector catches the gap between "{{USER_NAME}} worked on something" and "the output appeared in another system." Work done in Claude sessions often shows up in GitHub, email, or Slack shortly after — but during consolidation, the session may be the earliest signal of completed or in-progress work.
