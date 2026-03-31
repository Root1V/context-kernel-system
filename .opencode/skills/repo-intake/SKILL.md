---
name: repo-intake
description: "Executes a rigorous repository context analysis, identifying modular boundaries, contracts, and mandatory documentation prior to any implementation."
---

# Trigger: When to Use This Skill
Execute this skill IMMEDIATELY when initializing a complex user task, when onboarding to the repository, or before addressing any request that requires multi-module architectural planning.

# Execution Workflow (Step-by-Step)

You must execute the following steps sequentially using your available file-reading tools:

### Step 1: Root Context Alignment
- **Action**: Read the global `AGENTS.md` file located at the root of the repository.
- **Goal**: Assimilate the "Global Principles" and "Working Protocols" governing the codebase.

### Step 2: High-Level Architecture Assessment
- **Action**: Read `docs/vision/system-overview.md` and `docs/architecture/module-boundaries.md`.
- **Goal**: Map the macro-level system topology, module isolation rules, and domain boundaries.

### Step 3: Modular Deep-Dive Analysis
- **Action**: Identify which specific sub-modules or domains are affected by the user's request.
- **Action**: Locate and read the module-specific `AGENTS.md` files nested within those identified directories (e.g., `packages/[module_name]/AGENTS.md`).

### Step 4: Dynamic Context Loading
Evaluate the task domain and read the corresponding secondary context only if required:
- If the task impacts databases or explicit states -> **Read `docs/architecture/storage-model.md`**
- If the task impacts async lifecycles or processes -> **Read `docs/architecture/runtime-flows.md`**
- If the task impacts strict system limits/constants -> **Read `docs/vision/invariants.md`**

### Step 5: Risk & Dependency Mapping
- **Action**: Analyze structural dependencies across the identified modules.
- **Goal**: Evaluate the risk of breaking "Separation of Concerns" or causing architectural regressions.

# Required Output Formatter

Generate your final intake report strictly using the following markdown structure:

### 1. Architectural Summary
[Synthesize the current state of the architecture relevant to the parsed request]

### 2. Affected Boundaries & Modules
[Bulleted list explicitly naming the isolated modules that the task will span across]

### 3. Documentation Gaps
[List any missing explicit contracts, absent modular `AGENTS.md` files, or missing Architecture Decision Records (ADRs) that must be created before coding]

### 4. Risk Analysis & Dependencies
[Highlight critical breaking changes, implicit coupling threats, or token budget risks]

### 5. Recommended Next Action (Orchestration)
[Specify which specialized subagent, such as `@planner`, `@context-architect`, or `@backend-builder`, should be invoked next to continue the overarching DAG pipeline]
