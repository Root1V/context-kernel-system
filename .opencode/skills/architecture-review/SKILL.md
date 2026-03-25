---
name: architecture-review
description: "Executes a rigorous architectural health assessment to evaluate proposed changes against global invariants, module boundaries, and token budgets."
---

# Trigger: When to Use This Skill
Execute this skill when reviewing a proposed Execution Plan (from `@planner`), before approving new system abstractions, or when validating that a complex task does not violate the "Separation of Concerns".

# Execution Workflow (Step-by-Step)

You must execute the following analytical protocol sequentially to perform a high-signal Architecture Review:

### Step 1: Constraint Verification
- **Action**: Cross-reference the proposed architecture or plan against the global `docs/vision/invariants.md`.
- **Goal**: Ensure the design does not inherently breach mandatory system constants (e.g., maximum token budgets, critical logic paths, core memory capacities).

### Step 2: Boundary Contamination Check
- **Action**: Analyze the targeted modules in the proposal and compare them strictly against `docs/architecture/module-boundaries.md`.
- **Goal**: Identify and strictly forbid any "cross-module contamination" (e.g., mixing raw database queries directly inside context assembly logic). 

### Step 3: Contract-First Validation
- **Action**: Verify if definitive, explicitly typed API Interfaces and Models exist for the boundaries being crossed.
- **Goal**: Block any proposed implementation that lacks a preceding formal explicit contract (No blind coding allowed).

### Step 4: Explicit State Assessment
- **Action**: Evaluate the proposal's effect on Explicit State memory schemas.
- **Goal**: Ensure the new logic conforms to explicit persistence models, relying on strict `JSON` or `Dataclasses` rather than unstructured session histories.

# Required Output Formatter

Generate your final Architecture Review report strictly using the following markdown structure:

### 1. Proposal Viability Status
[State definitively: **[APPROVED]** - Ready for implementation, **[REJECTED]** - Fundamental rule violation, or **[NEEDS REVISION]** - Minor contract gaps detected]

### 2. Boundary Violations
[Identify any specific logic blocks that blur the "Separation of Concerns" or breach isolation limits. State "Clean Boundaries" if none found]

### 3. Contract Definition Readiness
[Confirm whether the builder has sufficient strict definitions (mypy/interfaces) to begin coding. List any specific missing contracts]

### 4. Technical Debt & Risks
[Acknowledge long-term operational risks, implicit dependencies, testing complexities, or token payload bloat introduced by the proposal]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** approve a cross-module change without ensuring a preceding Architecture Decision Record (ADR) or explicit contract is defined.
2. **Never** pass a plan that relies on "implicit" memory or unstructured historical logging rather than strict "Explicit State" models.
