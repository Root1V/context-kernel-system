---
name: module-implementation
description: "Executes backend programming tasks prioritizing TDD, clean interfaces, localized module boundaries, and strict type checking."
---

# Trigger: When to Use This Skill
Execute this skill when implementing abstract contracts, refactoring an existing module, or writing python logic previously designed by an architect or planner. This skill is optimized for the `@backend-builder`.

# Execution Workflow (Step-by-Step)

You must execute the following programming protocol sequentially:

### Step 1: Localized Context Loading
- **Action**: Locate the target module directory. 
- **Action**: Read the localized `AGENTS.md` file residing within that specific sub-module (e.g., `packages/[module_name]/AGENTS.md`).
- **Goal**: Assimilate the micro-level rules, invariants, and boundaries isolated solely for this functional domain.

### Step 2: Test-Driven Development (TDD) Kickoff
- **Action**: Before modifying any application code, write the initial `pytest` scripts corresponding to the architects' contracts.
- **Goal**: Lock in the mathematical and structural invariants. The tests MUST logically fail at this stage.

### Step 3: Minimal Safe Implementation
- **Action**: Write or modify the core logic (`.py` files), focusing strictly on fulfilling the newly written tests and explicit public interfaces.
- **Goal**: Achieve a passing test state without introducing circular dependencies, technical debt, or "feature creep". Type everything strictly using `mypy` standards.

### Step 4: Documentation Synchronization
- **Action**: If public interfaces, method signatures, or architectural contracts were altered, you must update the local `/docs` or the module's `README.md`.
- **Goal**: Validate the `Documentation-Driven` principle enforced by the global project guidelines.

### Step 5: Local QA Check
- **Action**: Verify syntactical correctness and ensure all bounded context lines described in `module-boundaries.md` were respected.

# Required Output Formatter

Generate your final Implementation Log strictly using the following markdown structure:

### 1. Module Impact Scope
[List the absolute path of the target module and confirm its associated `AGENTS.md` was parsed]

### 2. TDD & Pytest Implementation
[Provide the paths to the test files created/modified, and briefly describe the invariants mathematically tested]

### 3. Application Code Changes
[List the implementation summary, explicitly mentioning new interfaces, classes, or logic blocks built]

### 4. Code Quality & Strict Typing Status
[Confirm that all new logic includes strict static types and comprehensive docstrings]

### 5. Documentation Updates
[List any `README.md`, ADRs, or Architecture documents that were updated due to contract shifts]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** cross module boundaries. Do not import or modify files outside the specifically bounded context of the target module.
2. **Never** write "ghost code" (hardcoded application logic without a corresponding `pytest` or lacking `mypy` signatures).
