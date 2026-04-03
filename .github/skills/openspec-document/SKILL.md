---
name: openspec-document
description: Update project documentation to reflect a completed change. Use after verification passes and before archiving. Updates ADRs, README, architecture docs, and any affected reference material.
license: MIT
compatibility: Requires openspec CLI.
metadata:
  author: openspec
  version: "1.0"
---

Update project documentation to reflect what was built.

**Input**: Optionally specify a change name. If omitted, infer from context or prompt for selection.

**Steps**

1. **Select the change**

   If a name is provided, use it. Otherwise:
   - Infer from conversation context
   - Auto-select if only one active change exists
   - If ambiguous, run `openspec list --json` and ask the user to choose

   Announce: "Documenting change: <name>"

2. **Read the change artifacts**

   Read:
   - `openspec/changes/<name>/proposal.md` — what was built and why
   - `openspec/changes/<name>/design.md` — architectural decisions (if present)
   - `openspec/changes/<name>/tasks.md` — completed tasks

3. **Assess documentation impact**

   Determine which areas require updates based on what changed:

   | If the change... | Then update... |
   |---|---|
   | Introduces a new architectural decision | `docs/adr/` — create a new ADR |
   | Changes a public API or package interface | Package `README.md` |
   | Changes the system architecture or data flow | `docs/architecture/` |
   | Adds or removes packages/apps | Root `README.md`, `AGENTS.md` repository layout |
   | Changes the tech stack or tooling | `AGENTS.md` tech stack, `copilot-instructions.md` |
   | Changes the OpenSpec workflow itself | `AGENTS.md`, `copilot-instructions.md` |

4. **Apply documentation updates**

   For each file that needs updating:
   - Read the current content first
   - Make the minimum necessary change to keep it accurate
   - Do not rewrite sections that are unaffected

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

5. **Report documentation updates**

   ```
   ## Documentation Updated ✅

   **Change:** <name>
   **Files updated:**
   - docs/adr/ADR-NNN-<title>.md (new)
   - docs/architecture/module-boundaries.md (updated)
   - packages/memory/README.md (updated)

   Ready to archive. Run /opsx:archive
   ```

   If no documentation changes were needed:
   ```
   ## Documentation Check Complete ✅

   **Change:** <name>
   No documentation updates required for this change.

   Ready to archive. Run /opsx:archive
   ```

**Guardrails**
- Always read the current file content before editing
- Only update what is directly affected by the change
- Do not skip this step even if the change seems small — confirm explicitly that no docs need updating
- Never proceed to archive without completing this step
