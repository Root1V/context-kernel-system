---
name: memory-policy-design
description: "Designs explicit memory hierarchies (Core, Recall, Archival), off-cycle data consolidation rules, and triggers for sleep-time compute."
---

# Trigger: When to Use This Skill
Execute this skill when engineering or modifying how the system manages persisted state, defining off-line memory summarization jobs, or charting data promotion rules across different memory tiers.

# Execution Workflow (Step-by-Step)

You must execute the following protocol sequentially to design explicit state persistence strategies:

### Step 1: Memory Tier Mapping
- **Action**: Evaluate the raw data inputs and establish clear topological rules for where different types of data belong.
- **Goal**: Classify the information strictly into:
  - **Core Memory**: Active, always-in-prompt state variables.
  - **Recall Memory**: Short-term logs or immediate historical session arrays.
  - **Archival Memory**: Long-term, vectorized, or highly summarized explicit facts.

### Step 2: Policy & Lifecycle Formulation
- **Action**: Define explicit algorithms controlling the lifecycle of a single fact or block of data.
- **Goal**: Create definitive rules for:
  - *Promotion*: When does recall memory become archival?
  - *Update*: How is existing core memory mutated by new incoming facts?
  - *Eviction*: When is noise discarded permanently?

### Step 3: Sleep-Time Compute & Consolidation Design
- **Action**: Draft the threshold triggers and procedural algorithms for offline ("sleep-time") memory consolidation.
- **Goal**: Formulate the strict programmatic instructions that the `@sleep-time-worker` will use to compress logs and trace events when the system is idle.

### Step 4: Constraints & Testing Modeling
- **Action**: Formalize mathematical invariants to prevent data corruption, loss of context, or unbounded memory bloat.
- **Goal**: Ensure the compaction algorithms are bulletproof and deterministically testable.

# Required Output Formatter

Generate your final Memory Policy design artifact strictly using the following markdown structure:

### 1. Data Classification Rules
[Provide the logical conditions that dictate whether incoming data is placed into Core, Recall, or Archival storage tiers]

### 2. Lifecycles & Promotion Matrices
[State the exact logic triggers and mathematical bounds for promoting data between tiers or dropping it from the context bounds]

### 3. Consolidation (Sleep-Time) Algorithm
[Pseudocode or structured workflow dictating how the Background Worker should asynchronously summarize, merge, and clean the memory blocks]

### 4. Memory Test Cases & Invariants
[Define the explicit `pytest` scenarios required. e.g., "The consolidation algorithm MUST never drop a verified fact block from Core memory. The token footprint MUST be reduced by >= 25% post-consolidation in Recall."]

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** assume infinite memory capacities. All state policies MUST include a deterministic eviction, limits, or compaction safety-valve.
2. **Never** design unstructured logs as memory. All memory formats must be perfectly mapped into Explicit State (JSON or Dataclasses).
