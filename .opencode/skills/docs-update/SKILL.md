---
name: docs-update
description: "Synchronizes modular documentation, local AGENTS.md, and Architecture Decision Records (ADRs) with implemented code changes."
---

# Trigger: When to Use This Skill
Execute this skill IMMEDIATELY after establishing a new architectural contract, modifying public interfaces, executing cross-module changes, or concluding an implementation task.

# Execution Workflow (Step-by-Step)

You must execute the following documentation protocol sequentially to enforce a strict "Documentation-Driven" environment:

### Step 1: Impact Scope Analysis
- **Action**: Examine the recent codebase modifications, file diffs, or the Architect's approved plans.
- **Goal**: Identify exactly which isolated modules, public contracts, or system-level topologies have shifted. 

### Step 2: Architecture Decision Record (ADR) Update
- **Condition**: IF the change spans multiple modules OR introduces a new structural concept.
- **Action**: Draft or amend the official Architecture Decision Record (ADR) in the designated `$MODULE/docs/` or global `/docs/architecture/` directory.
- **Goal**: Persist the "Why" behind the technical shift before the implementation details are merged.

### Step 3: Localized Module (`AGENTS.md`) Updates
- **Condition**: IF the specific module's contract, internal responsibilities, or testing requirements changed.
- **Action**: Locate the target module's internal `AGENTS.md` file and rewrite the affected boundaries or rules.
- **Goal**: Ensure that future agents modifying this module possess up-to-date explicit context.

### Step 4: Component Documentation (READMEs)
- **Action**: Update the isolated `README.md` or localized docstrings associated STRICTLY with the affected files.
- **Goal**: Reflect the physical code changes without bloating unrelated readmes. Maintain strict *Granularity*.

# Required Output Formatter

Generate your final Documentation Sync Log strictly using the following markdown structure:

### 1. Architectural Impact 
[Summarize what fundamental paradigm was shifted and justify why it warranted a documentation update]

### 2. ADR Status
[List the absolute path of the created/modified Architecture Decision Record, or state "N/A - Isolated logic change only"]

### 3. Local `AGENTS.md` Patches
[List the module-specific `AGENTS.md` files that were updated with new interface rules, boundaries, or invariants]

### 4. Component / README Syncs
[List all localized `README.md` files successfully updated to reflect the new state]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never Monolithic**: Do not document every system change in a single "giant" root file. Force `Granularity`; map the docs intimately next to the isolated code they describe.
2. **Never Desync**: Do not change an explicit code contract or module boundary without concurrently updating its local `AGENTS.md` and triggering this sync skill.
