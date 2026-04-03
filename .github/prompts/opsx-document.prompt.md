---
description: Update project documentation to reflect a completed change — ADRs, README, architecture docs
---

Update project documentation to reflect what was built.

**Input**: Optionally specify a change name after `/opsx:document` (e.g., `/opsx:document add-auth`). If omitted, check if it can be inferred from conversation context. If vague or ambiguous you MUST prompt for available changes.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` and use the **AskUserQuestion tool** to let the user choose

   Announce: "Documenting change: <name>"

2. **Read the change artifacts**

   Read:
   - `openspec/changes/<name>/proposal.md`
   - `openspec/changes/<name>/design.md` (if present)
   - `openspec/changes/<name>/tasks.md`

3. **Assess documentation impact**

   Determine which docs need updating based on what changed:

   | If the change... | Then update... |
   |---|---|
   | Introduces a new architectural decision | `docs/adr/` — create a new ADR |
   | Changes a public API or package interface | Package `README.md` |
   | Changes the system architecture or data flow | `docs/architecture/` |
   | Adds or removes packages/apps | Root `README.md`, `AGENTS.md` repository layout |
   | Changes the tech stack or tooling | `AGENTS.md`, `copilot-instructions.md` |

4. **Apply documentation updates**

   For each file that needs updating:
   - Read the current content first
   - Make the minimum necessary change to keep it accurate
   - Do not rewrite unaffected sections

   **ADR format** (when creating a new one):
   ```markdown
   # ADR-NNN: <title>

   ## Status
   Accepted

   ## Context
   <why this decision was needed>

   ## Decision
   <what was decided>

   ## Consequences
   <what this means going forward>
   ```

5. **Report result**

   ```
   ## Documentation Updated ✅

   **Change:** <name>
   **Files updated:**
   - docs/adr/ADR-NNN-<title>.md (new)
   - docs/architecture/module-boundaries.md (updated)

   Ready to archive. Run /opsx:archive
   ```

   If no changes were needed:
   ```
   ## Documentation Check Complete ✅

   **Change:** <name>
   No documentation updates required for this change.

   Ready to archive. Run /opsx:archive
   ```
