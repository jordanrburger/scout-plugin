---
name: scout-status
description: Show the current state of your Scout installation — config, last runs, KB health, pending proposals, and wishlist status.
---

# Scout Status Dashboard

You are displaying a status dashboard for the user's Scout installation. Follow each section below in order. Present the final output as a clean, readable dashboard — not as a series of intermediate steps.

---

## Step 1: Locate the Scout Config

Check for `scout-config.yaml` in these locations, in order:

1. The current working directory (`./scout-config.yaml`)
2. `~/Scout/scout-config.yaml`
3. `~/scout/scout-config.yaml`

```bash
for f in "./scout-config.yaml" "$HOME/Scout/scout-config.yaml" "$HOME/scout/scout-config.yaml"; do
    if [ -f "$f" ]; then echo "FOUND:$f"; break; fi
done
```

**If no config is found:**

Tell the user:

```
No Scout installation found. Run `/scout-setup` to create one.
```

Stop here. Do not proceed with the dashboard.

**If found:** note the path as `SCOUT_CONFIG` and derive `SCOUT_DIR` as its parent directory. Read the config file, then continue.

---

## Step 2: Parse the Config

From the YAML config, extract:

- `instance_name` → `INSTANCE_NAME`
- `user.name` → `USER_NAME`
- `user.email` → `USER_EMAIL`
- `connectors` block → `CONNECTORS` (the map of service → true/false)
- `schedule.briefing` → `BRIEFING_TIME`
- `schedule.consolidation` → `CONSOLIDATION_TIMES`
- `schedule.dreaming` → `DREAMING_TIMES`
- `platform` → `PLATFORM`
- `scout_dir` → `SCOUT_DIR` (use this if present; otherwise use the parent directory of the config file)

---

## Step 3: Gather Data

Run all of the following data-gathering steps before composing the dashboard output.

### 3a. Last Runs (git log)

```bash
git -C "SCOUT_DIR" log --oneline -10
```

Collect the 10 most recent commit messages. Identify the most recent commit that mentions "briefing", "consolidation", and "dreaming" respectively (case-insensitive match on the commit message).

### 3b. KB Health

```bash
find "SCOUT_DIR/knowledge-base" -type f -name "*.md" | sort
```

For each file found, read it and look for a line matching either:
- `**Last verified:**`
- `**Last updated:**`

Extract the date from that line. Compare it to today's date to determine staleness.

Staleness thresholds (apply per-file based on its content — if no priority signal is obvious, default to medium):

| Priority | Stale after |
|----------|-------------|
| High     | 3 days      |
| Medium   | 7 days      |
| Low      | 14 days     |

Files without any date marker count as "unknown" — flag them separately but do not count them as stale.

### 3c. Pending Proposals

Read `SCOUT_DIR/dreaming-proposals.md`.

Look for proposal blocks with status `Pending` or `Approved` (i.e., not yet `Applied` or `Rejected`). A proposal block typically looks like:

```
### Proposal N: ...
**Status:** Pending
```

Count how many Pending and Approved proposals exist.

### 3d. Wishlist

Read `SCOUT_DIR/docs/Wishlist.md` (if it exists).

Collect all items that are NOT marked `[done]`. An item is done if the line starts with `- [done]`. Items marked `[in progress]` or with no status marker are considered active.

### 3e. Scheduler Health (macOS only)

Only run this step if `PLATFORM` is `macos` or if running on macOS (Darwin).

```bash
INSTANCE_LOWER=$(echo "INSTANCE_NAME" | tr '[:upper:]' '[:space:]' | tr ' ' '-' | tr -d '\n' | tr '[:upper:]' '[:lower:]')
launchctl list | grep "$INSTANCE_LOWER"
```

Note: derive `INSTANCE_LOWER` by lowercasing `INSTANCE_NAME` and replacing spaces with hyphens.

Collect the output lines. Each loaded plist appears as a row with PID (or `-`), last exit code, and label. Exit code `0` means healthy; any other value is a warning.

---

## Step 4: Compose and Display the Dashboard

Present the dashboard as follows. Use clean Markdown with headers and lists. Do not show raw shell output — interpret it into human-readable form.

---

```
╔══════════════════════════════════════════════════╗
║           SCOUT STATUS — <INSTANCE_NAME>         ║
╚══════════════════════════════════════════════════╝
```

### Config

| Field    | Value                                |
|----------|--------------------------------------|
| Instance | `<INSTANCE_NAME>`                    |
| User     | `<USER_NAME>` (`<USER_EMAIL>`)       |
| Dir      | `<SCOUT_DIR>`                        |
| Platform | `<PLATFORM>`                         |

### Connected Services

List every connector from the config. Use ✅ for `true` and ❌ for `false`:

```
  ✅ Slack
  ❌ Google Calendar
  ✅ Gmail
  ...
```

### Schedule

```
  Briefing:       <BRIEFING_TIME>
  Consolidation:  <CONSOLIDATION_TIMES>
  Dreaming:       <DREAMING_TIMES>
```

---

### Last 10 Runs

Show the 10 most recent git log entries as a simple list (hash + message):

```
  abc1234  briefing [09:03]: ...
  def5678  consolidation [17:00]: ...
  ...
```

Then below the list, highlight:

```
  Last briefing:       <commit message and date/time if identifiable>
  Last consolidation:  <commit message and date/time if identifiable>
  Last dreaming:       <commit message and date/time if identifiable>
```

If a run type hasn't happened yet, show: `(none found)`

---

### KB Health

```
  Total files:    X
  Up to date:     Y
  Need attention: Z
  Unknown dates:  W
```

If any files need attention, list them:

```
  ⚠️  knowledge-base/people.md  — last updated 12d ago (medium priority, stale after 7d)
  ⚠️  knowledge-base/channels.md — no date marker found
```

If all files are up to date:

```
  ✅ All KB files are fresh.
```

---

### Pending Proposals

If there are Pending or Approved proposals, list their titles and statuses:

```
  • [Pending]  Proposal 1: Add LinkedIn connector
  • [Approved] Proposal 2: Expand Slack channel coverage
```

If none:

```
  No pending proposals.
```

---

### Wishlist

If there are active (non-done) wishlist items, list them:

```
  • [in progress] Sharing the Scout skill with others internally
  • Custom GUI and TUI for working through action items
  • ...
```

If all items are done or the file doesn't exist:

```
  Wishlist is clear.
```

---

### Scheduler Health *(macOS only)*

If not on macOS, omit this section entirely.

For each launchctl entry found:

```
  ✅ com.scout.briefing      — running (PID 12345)
  ✅ com.scout.consolidation  — idle (last exit: 0)
  ⚠️  com.scout.dreaming       — last exit: 1  ← check logs
```

If no entries are found for this instance:

```
  ⚠️  No launchd plists found for '<INSTANCE_NAME_LOWER>'. Scheduler may not be configured.
  Run `/scout-setup` and choose "Reconfigure" to set up scheduling.
```

---

End the dashboard with a one-line summary:

```
Scout is healthy. / Scout needs attention — Z KB files stale, X proposals pending.
```

Choose the appropriate variant based on findings. "Needs attention" if any of: KB files stale, proposals pending with Approved status, scheduler entries missing or with non-zero exit codes.
