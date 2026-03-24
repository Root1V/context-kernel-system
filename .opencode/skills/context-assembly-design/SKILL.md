---
name: context-assembly-design
description: "Designs or modifies Context Assemblers, Token Budgets, Ordering Policies, and Compaction Triggers ensuring strict separation of concerns."
---

# Trigger: When to Use This Skill
Execute this skill when designing a new prompt assembly mechanism, refining the active context window boundaries, or overhauling the token budget and section ordering policies for an Agentic Runtime.

# Execution Workflow (Step-by-Step)

You must execute the following protocol sequentially:

### Step 1: Constraint & Capacity Analysis
- **Action**: Evaluate the aggregate token budget limit and latency requirements for the target system call.
- **Goal**: Identify the exact mathematical boundaries the assembly framework must operate within.

### Step 2: Context Sectioning
- **Action**: Categorize the ingested data into explicit prompt sections (e.g., System Prompts, Core Memory, Recalled/Indexed Context, User Prompts, Tool Schemas).
- **Goal**: Establish a clear macro-level layout topology before defining injection logic.

### Step 3: Policy Formulation (Order & Truncation)
- **Action**: Draft the rigorous rules for "Ordering Policies" (dictating item precedence) and "Compaction Policies" (dictating what is truncated, summarized, or evicted when hitting boundaries).
- **Goal**: Create a highly deterministic strategy for automated context evaluation.

### Step 4: Strict Isolation Verification
- **Action**: Verify that the Context Assembly logic is completely decoupled from the data transport layer.
- **Goal**: Guarantee the design strictly obeys the `AGENTS.md` mandate for "Separation of Concerns".

# Required Output Formatter

Generate your final Context Assembly design artifact strictly using the following markdown structure:

### 1. Assembly Input/Output Contract
```python
# Provide strict typing (mypy compliant), dataclass signatures for the Context Request (Input) and the Final Assembled Prompt (Output).
```

### 2. Context Topology (Sections)
[List the absolute order of the prompt sections, e.g., 1. System Rules -> 2. Retrieved Docs -> 3. Action History]

### 3. Ordering & Eviction Policy
[Logical algorithm or pseudocode dictating the exact priority queue and numerical triggers for context compaction and token truncation]

### 4. Test Cases & Invariants
[Define the explicit `pytest` operational scenarios required. e.g., "Must dynamically truncate Section 3 if the total token estimation exceeds 8192. Must NEVER truncate Section 1."]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** mix Context Assembly logic into API controllers or external HTTP handler modules.
2. **Never** define hardcoded prompt strings or logic bounds without simultaneously writing their corresponding programmatic tests.
