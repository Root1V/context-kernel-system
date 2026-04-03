---
description: Verify that the implemented change matches what was proposed — runs quality gate and cross-checks deliverables
---

Verify that what was built matches what was agreed in the spec.

**Input**: Optionally specify a change name after `/opsx:verify` (e.g., `/opsx:verify add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` and use the **AskUserQuestion tool** to let the user choose

   Announce: "Verifying change: <name>"

2. **Read proposal and tasks**

   Read:
   - `openspec/changes/<name>/proposal.md`
   - `openspec/changes/<name>/tasks.md`
   - `openspec/changes/<name>/design.md` (if present)

3. **Check task completion**

   Count `- [x]` vs `- [ ]` in tasks.md.

   If incomplete tasks found: list them and block — "Verification blocked: N tasks are still incomplete." Do NOT proceed.

4. **Run the quality gate**

   ```bash
   bash .git/hooks/pre-push
   ```

   If any check fails: show which ones failed and block — "Verification blocked: quality gate failed." Do NOT proceed.

5. **Cross-check deliverables against the proposal**

   For each goal or requirement stated in `proposal.md`, confirm a corresponding completed task exists.
   Flag any requirement with no matching completed task.

6. **Report result**

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
   - [ ] <issue>

   Fix the blockers above and re-run /opsx:verify
   ```
