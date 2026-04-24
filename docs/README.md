# Scout Plugin Docs

This directory holds design specs, implementation plans, and ongoing
tracking for the Scout unification effort. For code and CI, see
`../engine/` and `../.github/workflows/`.

## Layout

- **`specs/`** — approved design specs. Each file is dated and scoped to a single
  coherent design. Specs are the source of truth for what's being built and why.
- **`plans/`** — implementation plans derived from specs. Each plan produces
  working, testable software on its own; plans are numbered (`plan-1`, `plan-2`)
  when a spec is big enough to span multiple PRs.
- **`FOLLOWUPS.md`** — consolidated list of non-blocking followup items
  surfaced during reviews. New items land here; PRs that address items move
  them to the `Resolved` section at the bottom.

## Current scope

The Scout system consists of three pieces that must stay coordinated:

1. **`scout-plugin` (this repo)** — the Claude Code plugin and Python engine
   (`scoutctl` CLI, hooks, runners, ontology parser, TUI). This is the
   canonical home for shippable engine code after unification.
2. **`scout-app`** (`github.com/jordanrburger/Scout`) — SwiftUI Mac menu-bar
   app that drives the engine and renders telemetry.
3. **User data directory** (default `~/Scout`) — per-user knowledge base,
   action items, drafts, logs. Never in git; created by `scoutctl setup`.

The unification spec (`specs/2026-04-24-scout-unification-design.md`) captures
the target architecture. Plan 1 (engine scaffolding, merged) landed the
Python package foundation. Plans 2–7 follow.

## Contributing

If you're picking up a followup item or starting a new plan:

1. Read the spec section the work targets.
2. Check `FOLLOWUPS.md` for any related pending items.
3. Open a PR that either (a) lands a plan task with tests + CI, or (b) resolves
   one or more followup items (move to `Resolved` in the same PR).
