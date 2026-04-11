# Scout

Autonomous knowledge management and daily briefing system for Claude Code. Scout monitors your work tools — Slack, Calendar, Gmail, Linear, GitHub, meeting transcripts, and more — synthesizes findings into a persistent, interlinked knowledge base, and delivers daily action items. It runs unattended as scheduled Claude Code sessions, multiple times per day.

You shouldn't have to manually track what happened across seven different tools yesterday, what's still pending from last week, or what changed while you were in meetings. Scout does that automatically. It reads your tools, cross-checks findings against each other, writes a coherent knowledge base, and surfaces only what matters. The knowledge base is browsable in Obsidian as an interlinked graph of projects, people, channels, and action items.

## Quick Start

```
claude plugin add <repo-url>
```

Then run `/scout-setup` in any Claude Code session. The setup wizard detects your connected tools (MCP connectors, `gh` CLI, local directories), collects your details (name, Slack ID, email), scaffolds the Scout directory, assembles personalized skill files from phase modules matching your connectors, and configures scheduling. Done in under 5 minutes.

Check your installation at any time:

```
/scout-status
```

This shows connector health, schedule status, knowledge base freshness, and recent run history.

## How It Works

Three session types form a daily rhythm:

### Morning Briefing (once per day)

Full cold-start. Reads the entire knowledge base, queries every connected tool, cross-checks findings against each other, writes a fresh action items file, and updates the KB. Every action item must pass a multi-point cross-check before being committed — a meeting on your calendar is verified against transcripts, a Linear issue is verified against GitHub PRs, an email thread is verified against Slack messages. The briefing ends with a notification summarizing what needs your attention today.

### Consolidation (2-3x per day)

Lightweight delta scan in six phases:

1. **What the user did** — Reads recent Claude Code sessions, sent messages, committed code, and updated issues to build a picture of your activity since the last run.
2. **What happened** — Queries all connectors for new events: messages, meetings, emails, issue updates, PR activity.
3. **Per-item reconciliation** — Walks each KB file and reconciles it against fresh data. Updates, flags staleness, resolves contradictions.
4. **KB audit** — Picks files for deep review. Every audit must pass a depth gate: "Would the user learn something new from what I touched?" Surface-level timestamp updates don't count.
5. **Commit** — Stages all changes and commits with a descriptive message summarizing what was found.
6. **Notification** — Sends a summary of new findings, updated action items, and KB changes.

### Dreaming (evening, 1-2x)

Self-improvement loop:

1. **Feedback processing** — Reads reactions and replies on Scout's notifications. A thumbs-up on an action item confirms it was useful. A thumbs-down flags a pattern to avoid. These signals feed back into future runs.
2. **KB deep work** — Scores KB files by staleness, importance, and interconnectedness. Picks the highest-value targets for deep improvement — restructuring, merging related notes, surfacing buried insights.
3. **Wishlist** — Checks the wishlist for user-requested features or improvements and works through them.

Everything is a git repo. Every change Scout makes is committed with a descriptive message. The commit history is as much a part of the system as the files.

## Supported Connectors

| Connector | What it provides | Required? |
|-----------|-----------------|-----------|
| Slack | Message monitoring, outbound tracking, feedback loop | No (enables dreaming feedback) |
| Google Calendar | Meeting context, scheduling verification | No |
| Gmail | Email tracking, sent mail verification | No |
| Linear | Issue tracking, status sync | No |
| GitHub (`gh` CLI) | PR tracking, commit monitoring, review requests | No |
| Granola | Meeting transcripts | No |
| Google Drive | Documents, meeting notes | No |
| Claude Code sessions | Work session history | No (auto-detected) |

Scout works with any subset of connectors. More connectors means richer cross-checking, but even a Calendar-only Scout is useful. The setup wizard detects what you have and assembles skill files accordingly.

## Architecture

Scout is built from **phase modules** — small, focused markdown files that each handle one aspect of the workflow. During setup, the wizard selects the modules matching your connected tools and assembles them into complete, self-contained skill files.

### Plugin structure

```
scout-plugin/
  plugin.json               -- Plugin manifest
  commands/
    scout-setup.md          -- Interactive setup wizard
    scout-status.md         -- Dashboard command
  phases/
    core/                   -- Always included (git, KB management, action items)
    connectors/             -- One per tool (Slack, Calendar, Linear, etc.)
    modes/                  -- Dreaming-specific (feedback, KB deep work, wishlist)
  templates/                -- Runner scripts, schedulers, KB scaffold
```

### What gets created in your Scout directory

```
~/Scout/
  SKILL.md                  -- Assembled skill file (briefing + consolidation)
  DREAMING.md               -- Assembled skill file (dreaming)
  run-scout.sh              -- Runner script
  run-dreaming.sh           -- Dreaming runner
  scout-config.yaml         -- Your configuration
  dreaming-proposals.md     -- Proposal gate for skill improvements
  knowledge-base/           -- Your persistent knowledge base (Obsidian vault)
  action-items/             -- Daily action items
  docs/Wishlist.md          -- Feature requests for your instance
```

The assembled skill files are self-contained — they don't reference the plugin at runtime. You can customize them freely. Run `/scout-setup` again to regenerate from the latest phase modules.

## Customization

- **Edit skill files directly**: The assembled `SKILL.md` and `DREAMING.md` are yours to modify. Add checks, remove sections, change wording — they're plain markdown.
- **Change schedule**: Edit the launchd plist or cron entries, or re-run `/scout-setup` to reconfigure timing.
- **Add KB files**: Create new project folders following the convention `projects/<name>/<name>.md`. Scout will pick them up on the next run.
- **Adjust cross-checks**: The cross-check logic in `SKILL.md` scales with connectors — add or remove verification points as needed.
- **Re-assemble**: After plugin updates, run `/scout-setup` and choose Reassemble to regenerate skill files with new improvements while preserving your configuration.

## Design Philosophy

The principles that make Scout work:

### Source Equality

No single connector is treated as authoritative. A meeting transcript is a signal, not a fact. A Slack message is context, not ground truth. Everything gets verified against other sources before it becomes a KB entry or an action item.

### Verification Levels

KB content is tagged by confidence:

- No marker — verified by 2+ sources
- `[single-source]` — only one source, plausible but unverified
- `[unverified]` — mentioned but not corroborated
- `[stale]` — was accurate, hasn't been confirmed recently
- `[contradicted]` — sources disagree

This makes trust explicit. When you read the KB, you know exactly how much weight to give each piece of information.

### KB as Persistent Memory

The knowledge base isn't a log or a copy of your tools. It synthesizes information into a coherent picture — who's working on what, which projects are blocked, what decisions were made and why. Action items are ephemeral (regenerated each morning); the KB is permanent and evolving.

### Git as Foundation

Every change is committed. The history is the system's memory of its own evolution. Scout uses `git log` and `git diff` to detect what changed since the last run, avoid duplicate work, and provide an audit trail. If something goes wrong, you can always trace back to when and why.

### Feedback Loop

Scout sends notifications. You react with a thumbs-up or thumbs-down. Dreaming sessions process the feedback, identify patterns (action items that were always dismissed, KB entries that were always wrong), and feed those patterns into skill improvements. Future runs get better because past runs were evaluated.

### Depth Self-Check

Every KB audit must pass a gate: "Would the user learn something new from what I touched?" Touching a file to bump a timestamp doesn't count. Rewriting a paragraph to say the same thing in different words doesn't count. The audit must produce genuine insight or it doesn't get committed.

### Adaptive Cross-Checking

The more connectors you have, the more verification points each action item passes through. A 2-connector setup still produces useful results. A 7-connector setup produces thoroughly verified ones. The system adapts its verification depth to what's available rather than failing when a connector is missing.

## FAQ / Troubleshooting

**My scheduled runs aren't firing.**
On macOS, check `launchctl list | grep scout`. Make sure your machine is awake at scheduled times — launchd won't fire if the lid is closed. Verify the plist is loaded with `launchctl list`. Check logs in `.scout-logs/` for errors from the last attempted run.

**A connector stopped working.**
Re-authenticate the MCP connector in Claude Code settings. Run `/scout-status` to see which tools are currently available and which are returning errors.

**The KB is getting stale.**
Check run logs in `.scout-logs/`. Verify your schedule is active with `launchctl list | grep scout` or by checking cron with `crontab -l`. Run `/scout-status` to see file freshness — it reports the last-modified time for every KB file.

**I want to add a new connector.**
Run `/scout-setup` and choose Reconfigure. The wizard will re-detect available tools and reassemble your skill files to include the new connector's phase modules.

**I want to customize the skill file.**
Edit `SKILL.md` or `DREAMING.md` directly in your Scout directory. Your changes persist until you explicitly run Reassemble from `/scout-setup`. The plugin never overwrites your skill files without asking.

**Can I use this without Obsidian?**
Yes. The KB is just markdown files with `[[wikilinks]]` between them. Obsidian provides the best reading experience — you get a graph view of how projects, people, and channels connect — but any markdown viewer or text editor works fine.

**Can multiple people use Scout on the same team?**
Each person runs their own Scout instance with their own KB. Scout is designed around individual context — your meetings, your messages, your action items. Team-wide knowledge sharing happens through your normal tools; Scout helps each person stay on top of what matters to them.

**How do I update the plugin?**
Pull the latest version of the plugin repo. Then run `/scout-setup` and choose Reassemble to regenerate your skill files with the latest phase module improvements. Your configuration and KB are preserved.
