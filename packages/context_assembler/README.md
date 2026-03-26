# context_assembler

## Purpose

`context_assembler` builds the **active context** for a single model call.

It is the module responsible for turning a larger stateful system into a bounded,
ordered, high-signal context payload that the model can actually use.

This module is central to Context Kernel.

---

## What this module owns

- active context composition
- token budgeting
- section ordering
- section inclusion/exclusion
- compaction hooks
- duplicate reduction
- final assembly object creation

---

## What this module does NOT own

- model provider specifics
- memory persistence
- retrieval execution
- tool execution
- HTTP concerns
- session persistence

Those concerns belong to:
- `model_adapter`
- `memory`
- `retrieval`
- `tool_runtime`
- `apps/api`
- `state` / `storage`

---

## Why this module exists

Without a dedicated assembler, systems tend to drift into one of these failures:

- context assembled ad hoc in controllers
- no explicit token budgeting
- duplicated information across sections
- inconsistent ordering
- memory and retrieval leaking into prompt composition
- hard-to-debug model behavior

This module exists to make active context:
- explicit
- deterministic
- testable
- auditable

---

## Mental model

```text
total system state
   |
   +-- task state
   +-- session state
   +-- core memory
   +-- message buffer
   +-- retrieved context
   +-- files / artifacts
   +-- tools metadata
   |
   v
context assembler
   |
   +-- select
   +-- order
   +-- compact
   +-- reserve output budget
   +-- remove duplicates
   |
   v
active context
   |
   v
model call

Core responsibilities
1. Token budgeting
The assembler must respect model limits.
It should:
know total available context
reserve output budget
estimate section sizes
decide when to compact or drop low-priority sections
2. Section ordering
Different types of context should appear in predictable order.
Typical order:
system instructions
execution metadata / constraints
task state
core memory
recent message buffer
files/artifacts
retrieved context
current user request
The exact order may evolve, but it must be deterministic.
3. Section filtering
Not every available piece of context should enter the final payload.
The assembler decides:
what enters
what stays out
what gets summarized
what is only referenced indirectly
4. Compaction
If the assembly is too large, the assembler should support compaction hooks.
Examples:
summarize message buffer
trim repeated evidence
shorten tool outputs
prefer summaries over raw fragments
5. Duplicate reduction
The same fact should not appear repeatedly across:
memory blocks
message buffer
retrieved context
task state

Inputs
A typical assembly request should include:
normalized request
runtime state
memory snapshot
retrieved context
tool metadata
model limits
optional assembly policy/profile

Output
The primary output is a structured ContextAssembly.
It should contain at least:
selected sections
section order
budget metadata
compaction metadata
references to included evidence
final serialized or serializable payload

Example assembly shape
ContextAssembly
 |- model_limits
 |- reserved_output_tokens
 |- total_input_budget
 |- sections[]
 |    |- system_prompt
 |    |- task_state
 |    |- memory_blocks
 |    |- message_buffer
 |    |- files_artifacts
 |    |- retrieved_context
 |    `- user_request
 |- included_references[]
 |- compaction_actions[]
 `- final_payload

Package layout
context_assembler/
|
|-- assembler.py
|-- token_budget.py
|-- sections/
|   |-- system_prompt.py
|   |-- tool_context.py
|   |-- memory_blocks.py
|   |-- message_buffer.py
|   |-- files_artifacts.py
|   `-- retrieved_context.py
|
`-- policies/
   |-- compaction_policy.py
   `-- ordering_policy.py

Key design rules
This is the only module that composes final active context.
Ordering must be deterministic.
Policies must be testable.
Budgeting must be explicit.
The module should prefer minimal high-signal context over maximal raw context.
It must remain provider-agnostic except for limits/contracts read from model_adapter.

Testing strategy
This module should have:
Unit tests
token budgeting
ordering policy
duplicate reduction helpers
section inclusion logic
Golden tests
full context assemblies for reference scenarios
compaction outcomes
overflow handling
Edge cases
zero retrieved context
huge message buffer
oversized memory blocks
very small output budget
repeated evidence across sections

Non-goals
This module is not:
a retrieval system
a memory store
a chat controller
a tool execution engine
a model provider client

Practical quality checklist
Before merging a change here, ask:
Does the assembler still own final composition?
Is the section order deterministic?
Is the budget explicit?
Is duplicate handling improved or preserved?
Is the change testable without a live model?
Did we accidentally move policy into another module?
