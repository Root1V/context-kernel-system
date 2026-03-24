---
name: rag-retrieval-design
description: "Designs extraction, chunking, embedding generation, semantic/BM25 search flows, and RAG architectures."
---

# Trigger: When to Use This Skill
Execute this skill when tasked with configuring vector indexes, chunking unformatted input text, optimizing hybrid search policies, or establishing dynamic "just-in-time" RAG data pipelines.

# Execution Workflow (Step-by-Step)

You must process RAG and indexing tasks through the following architectural pipeline:

### Step 1: Source & Index Analysis
- **Action**: Inspect the type, scale, and density of the unstructured text or data being indexed.
- **Goal**: Define the ideal ingestion pipeline to maintain a "High-Signal" context footprint avoiding raw, noisy data dumps.

### Step 2: Chunking & Enrichment Definitions
- **Action**: Formalize exact string manipulation algorithms, specifying character/token limits per chunk, chunk overlap, and injected metadata schemas.
- **Goal**: Ensure the embeddings generated possess strong structural constraints (e.g., attributing every chunk with explicit context like `origin_id`, `type`, and `timestamp`).

### Step 3: Hybrid Search Algorithm (Semantic + Lexical)
- **Action**: Outline the weight distribution between purely lexical keyword search (e.g., BM25) and semantic vector search distances (e.g., Cosine Similarity).
- **Goal**: Construct the abstract search query logic that will pull the most relevant facts from the vector/search databases.

### Step 4: Post-Search Attention Reranking
- **Action**: Establish an attention-scoring cutoff or mathematical re-ranking mechanism for fetched context chunks before handing them to the Context Assembler.
- **Goal**: Eliminate low-quality context "hallucinations" or matches immediately post-search to preserve tight token budgets.

# Required Output Formatter

Generate your final Retrieval Architecture report strictly using the following markdown structure:

### 1. Ingestion / Chunking Policy
[Rule set establishing how many characters/tokens equal one chunk, the overlap ratio, and explicitly required JSON metadata attributes]

### 2. Querying Typology
[Abstract query definition explaining the weights of exact-match/lexical vs semantic embedding lookups]

### 3. Relevance Reranking Cutoffs
[List the explicit mathematical logic (e.g., Cosine Similarity > 0.8) required for a retrieved fact block to survive filtering]

### 4. Search Domain Interfaces
```python
# Provide strict python typing (mypy compliant), describing the Search Query class inputs and the Retrieved Documents array format.
```

---

## ⛔ Anti-Patterns (NEVER VIOLATE)
1. **Never** dump raw retrieved documents directly into the active prompt without passing them through an Attention/Reranking cut-off filter.
2. **Never** design vector schemas without structural metadata indexing. Explicit integration with state tracking requires timestamps and absolute origin references.
