---
name: test-strategy
description: "Formulates rigorous QA plans, mapping specific module changes to the requisite Unit, Integration, Mock, and Golden Regression tests defined in AGENTS.md."
---

# Trigger: When to Use This Skill
Execute this skill when preparing an implementation pipeline, right before handing over tasks to the `@backend-builder` or defining the pass/fail scenarios for the `@evaluator`. 

# Execution Workflow (Step-by-Step)

You must execute the following analytical protocol sequentially to craft a comprehensive Testing Strategy:

### Step 1: Policy Identification
- **Action**: Assess what type of subsystem is being modified (e.g., Context Assembly, Memory Update, MCP Tool, or Offline Compaction).
- **Goal**: Classify the scope of the change to determine the necessary testing paradigm.

### Step 2: Global Rule Mapping
- **Action**: Strictly apply the mapping established in the root `AGENTS.md` file:
  - If a **Context Assembly Policy** changes -> Plan **Unit Tests**.
  - If a **Memory Update / Storage Operation** changes -> Plan **Integration Tests** targeting explicit state models.
  - If an **MCP Tool Runtime** is modified -> Plan **Fixtures or Mock Tests**.
  - If a **Compaction / Sleep-Time Policy** changes -> Plan deterministic **"Golden" Regression Tests**.
- **Goal**: Lock in the architectural testing demands avoiding any "Test-Driven" debt.

### Step 3: Pytest Scaffold Design
- **Action**: Outline the necessary `pytest` directory structure, fixture functions (`conftest.py`), and mock boundaries.
- **Goal**: Ensure the `@backend-builder` knows exactly what tests to write first, maintaining proper Separation of Concerns (e.g., tests shouldn't make real DB calls if mock tests are required).

### Step 4: Coverage Limits
- **Action**: Define explicit mathematical invariants for success, avoiding tests that only verify syntax.
- **Goal**: Force the creation of logic-heavy assertions (e.g., MRR relevance, strict 25% token budget reductions, valid JSON schemas).

# Required Output Formatter

Generate your final Test Strategy artifact strictly using the following markdown structure:

### 1. Target Subsystem & Test Type
[Identify the module being modified and precisely state which of the 4 AGENTS.md test categories is mandated]

### 2. Test Execution Objectives
[List the explicit invariants or behaviors that the tests MUST mathematically or logically prove]

### 3. Mock & Fixture Requirements
[Detail if any fake data representations, fake DB states, or mocked HTTP clients are required prior to writing the `pytest` scenarios]

### 4. Golden Test Baselines (If Applicable)
[If this touches offline compaction or retrieval policies, explain where the Golden expected data resides and how the output will be deterministically diffed]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** propose end-to-end tests relying on external mutating states unless specifically testing a final unified integration endpoint.
2. **Never** omit testing requirements for a Context or Memory modification. The `evaluator` will instantly fail undocumented logic changes.
