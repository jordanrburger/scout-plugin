---
phase: mode
name: wishlist
slot: dreaming-phase-3
mode: [dreaming]
requires: null
---

## Phase 3: Wishlist Processing

Process items from {{USER_NAME}}'s wishlist — feature requests, improvements, and ideas that {{USER_NAME}} wants {{INSTANCE_NAME}} to implement during dreaming runs.

---

### Step 3a: Read the Wishlist

Read the three wishlist files, in this order:

1. `docs/Wishlist.md` — new items, not yet picked up
2. `docs/Wishlist-in-progress.md` — items actively being worked on across dreaming runs
3. `docs/Wishlist-done.md` — archive of completed items (read only to avoid re-doing work)

Item-state conventions:

| Format | State | Typical location |
|---|---|---|
| Bare text (no marker) | Not started | `Wishlist.md` |
| `[in progress]` suffix or prefix | Work has begun | `Wishlist-in-progress.md` (move here when you start) |
| `[done]` suffix or ~~strikethrough~~ | Completed | `Wishlist-done.md` (move here after completion) |

The three-file split keeps the active wishlist token-efficient. When you start a new item, move it from `Wishlist.md` into `Wishlist-in-progress.md`. When you finish an item, move it from `Wishlist-in-progress.md` into `Wishlist-done.md`.

Identify all items and their current state before proceeding.

---

### Step 3b: Identify Actionable Items

Scan for items that are neither `[done]` nor `[in progress]`. For each not-started item, assess feasibility:

**Implementable in one run:** The item is clear, scoped, and can be fully completed in this dreaming session. Examples: "add a new section to SKILL.md", "create a KB template for architecture decisions", "update the freshness standards table."

**Multi-run effort:** The item is too large for a single session but can be broken into sub-tasks. Examples: "audit all project files for consistency", "redesign the action items format." Break these into concrete sub-tasks that can each be completed independently.

**Too ambiguous:** The item is unclear enough that attempting it risks wasted work or incorrect implementation. Examples: "make Scout smarter", "improve the KB." Skip these — they need clarification from {{USER_NAME}} before work begins. Do not guess at intent.

---

### Step 3c: Maximize Wishlist Progress

Select actionable items and push as far as possible. Don't artificially limit yourself to one sub-task — complete multiple sub-tasks or even multiple items if time allows. The constraint is quality, not count.

**Priority order:**
1. Items {{USER_NAME}} has explicitly flagged as important (check recent feedback)
2. First actionable item on the list (not done, not blocked)
3. In-progress items with remaining sub-tasks

**Execution rules by item type:**

- **Skill or documentation changes**: Edit the target file directly. Follow existing conventions and formatting in the file. (SKILL.md changes must go through the proposal gate — write proposals to `dreaming-proposals.md`.)
- **New files**: Create following the naming conventions and structure patterns established in the codebase. Link new files from their parent/index files.
- **Configuration changes**: Edit the relevant config file. Test that the change is syntactically valid.
- **Research items**: Do real research (check docs, test locally, query sources) — don't give superficial answers.
- **Multi-run efforts**: Complete as many sub-tasks as you can per run, not just one.

**Scope guard**: If an item turns out to be larger than expected mid-implementation, stop at a clean checkpoint. Mark it `[in progress]` with a note about what was completed and what remains. Do not leave half-finished work in an inconsistent state.

---

### Step 3d: Update the Wishlist Files

After executing (or deciding to skip), move items between the three files as appropriate.

**For completed items → `docs/Wishlist-done.md`:**
```markdown
- ~~Original item text~~ [done] — Delivered in dreaming run [date]. [One-sentence description of what was created/changed.]
```
Delete the item from `Wishlist.md` or `Wishlist-in-progress.md` (wherever it lived) in the same commit.

**For newly-started items → `docs/Wishlist-in-progress.md`:**
Move the item out of `Wishlist.md` and into `Wishlist-in-progress.md` with sub-tasks spelled out:
```markdown
- Original item text [in progress]
  - [x] Sub-task 1 — completed [date]
  - [ ] Sub-task 2 — remaining
  - [ ] Sub-task 3 — remaining
```

**For items continuing from a prior run:**
Update the checkbox list in `Wishlist-in-progress.md` in place. Add newly-identified sub-tasks as needed.

**For items skipped as ambiguous:**
Do not move or modify the item. Leave it in `Wishlist.md` for {{USER_NAME}} to clarify. Optionally log which item was skipped and why in the session summary.

The three-file split is how the active wishlist stays token-efficient. Never leave `[done]` items sitting in `Wishlist.md` — they belong in `Wishlist-done.md`.

---

### Step 3e: Commit

```bash
git -C {{SCOUT_DIR}} add -A && git -C {{SCOUT_DIR}} commit -m "dreaming [HH:MM]: wishlist — <description of what was done>"
```

The description should name the wishlist item: e.g., "wishlist — added architecture decision KB template" or "wishlist — completed sub-task 2/4 for action items format redesign."

If no wishlist items were actionable (all done, all in progress, all ambiguous), skip the commit and note "No actionable wishlist items" in the session log.
