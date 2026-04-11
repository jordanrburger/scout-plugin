---
phase: core
name: git-setup
slot: setup
mode: [briefing, consolidation, dreaming]
requires: null
---

## Step 0: Git Setup

Silently ensure git is ready. Run every time without commentary:

```bash
cd {{SCOUT_DIR}}
git config user.email "{{USER_EMAIL}}"
git config user.name "{{INSTANCE_NAME}} Bot"
```

Do not mention git setup in your output unless something goes wrong.

## Using Git History

Git is a core part of the {{INSTANCE_NAME}} system — every change is committed with descriptive messages. Use git history actively during runs:

- `git log --oneline -20` — see what recent runs did (avoid duplicate work)
- `git diff HEAD~1` — inspect what the last run changed
- `git log --since="8 hours ago" --oneline` — understand what happened today
- `git show <commit>` — inspect a specific change when you need provenance

The commit history is as valuable as the files themselves. When verifying KB claims or understanding what was already audited, check git before querying connectors.
