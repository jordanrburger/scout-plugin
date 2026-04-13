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

Read `docs/Wishlist.md`. Understand the current state of every item using these conventions:

| Format | State |
|---|---|
| Bare text (no marker) | Not started |
| `[in progress]` suffix or prefix | Work has begun but is not complete |
| `[done]` suffix or ~~strikethrough~~ | Completed |

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

### Step 3d: Update the Wishlist

After executing (or deciding to skip), update `docs/Wishlist.md`:

**For completed items:**
```markdown
- ~~Original item text~~ [done] — Delivered in dreaming run [date]. [One-sentence description of what was created/changed.]
```

**For partially completed items (multi-run):**
```markdown
- Original item text [in progress]
  - [x] Sub-task 1 — completed [date]
  - [x] Sub-task 2 — completed [date]
  - [ ] Sub-task 3 — remaining
  - [ ] Sub-task 4 — remaining
```

**For items skipped as ambiguous:**
Do not modify the item. Leave it as-is for {{USER_NAME}} to clarify. Optionally add a comment in the session log noting which item was skipped and why.

**Archive done items:** Move any `[done]` items (including their description and implementation notes) from `docs/Wishlist.md` to `docs/Wishlist-done.md` and delete them from the active file. This keeps the active wishlist small and token-efficient.

---

### Step 3e: Commit

```bash
git -C {{SCOUT_DIR}} add -A && git -C {{SCOUT_DIR}} commit -m "dreaming [HH:MM]: wishlist — <description of what was done>"
```

The description should name the wishlist item: e.g., "wishlist — added architecture decision KB template" or "wishlist — completed sub-task 2/4 for action items format redesign."

If no wishlist items were actionable (all done, all in progress, all ambiguous), skip the commit and note "No actionable wishlist items" in the session log.
