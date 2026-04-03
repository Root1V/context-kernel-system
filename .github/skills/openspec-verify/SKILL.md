---
name: openspec-verify
description: Verify that the implemented change matches what was proposed. Use after apply is complete and before documenting or archiving. Runs the quality gate and cross-checks deliverables against the proposal.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
---

Verify that what was built matches what was agreed in the spec.

**Input**: Optionally specify a change name. If omitted, infer from context or prompt for selection.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` and ask the user to choose

   Announce: "Verifying change: <name>"

2. **Read the proposal and tasks**

   Read the following files:
   - `openspec/changes/<name>/proposal.md` — what was requested and why
   - `openspec/changes/<name>/tasks.md` — the task checklist
   - `openspec/changes/<name>/design.md` — how it was designed (if present)

3. **Check task completion**

   Count `- [x]` (complete) vs `- [ ]` (incomplete) in tasks.md.

   **If incomplete tasks found:**
   - List them explicitly
   - Block verification and report: "Verification blocked: N tasks are still incomplete."
   - Do NOT proceed — return to `opsx:apply`

4. **Run the quality gate**

   ```bash
   bash .git/hooks/pre-push
   ```

   This runs: ruff lint, ruff format check, mypy, and all 10 test suites.

   **If any check fails:**
   - Show which checks failed
   - Block verification: "Verification blocked: quality gate failed."
   - Do NOT proceed — fix the issues first

5. **Cross-check deliverables against the proposal**

   For each goal or requirement stated in `proposal.md`:
   - Identify the corresponding task(s) in `tasks.md`
   - Confirm the task is marked complete
   - If the proposal includes acceptance criteria, validate them explicitly

   Flag any requirement in the proposal that has no corresponding completed task.

6. **Report verification result**

   **If all checks pass:**
   ```
   ## Verification Passed ✅

   **Change:** <name>
   **Tasks:** N/N complete
   **Quality gate:** ruff ✓ | mypy ✓ | tests ✓ (N passed)
   **Proposal coverage:** All requirements mapped to completed tasks

   Ready to document. Run /opsx:document
   ```

   **If any check fails:**
   ```
   ## Verification Failed ❌

   **Change:** <name>
   **Blockers:**
   - [ ] <issue 1>
   - [ ] <issue 2>

   Fix the blockers above and re-run /opsx:verify
   ```

**Guardrails**
- Never mark verification as passed if the quality gate fails
- Never mark verification as passed if tasks are incomplete
- Surface every unmatched proposal requirement explicitly
- Do not proceed to document or archive if verification fails
