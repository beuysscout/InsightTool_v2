Compare the current codebase against the project plan (`projectplan.md`) for a specific phase.

## Instructions
1. Read `projectplan.md` and extract all deliverables for the requested phase.
   - If no phase is specified via $ARGUMENTS, check **all phases** and give a high-level overview.
   - If a phase number is given (e.g., `1`, `2`, `3`), do a deep-dive on that phase only.

2. For each deliverable, inspect the relevant backend and frontend code to determine:
   - **Done**: Fully implemented and wired end-to-end (API + UI).
   - **Partial**: Backend or frontend exists but not fully connected, or has known gaps.
   - **Not started**: No meaningful code exists for this item.

3. Output a checklist:
   ```
   Phase X: [Phase Name]
   [x] Item 1 — notes
   [~] Item 2 — partial, missing frontend wiring
   [ ] Item 3 — not started
   ```

4. List any **gaps or issues** found (e.g., dead code, missing error handling, incomplete UI flows).

5. If checking all phases, end with a recommendation of which phase/item to tackle next.

$ARGUMENTS
