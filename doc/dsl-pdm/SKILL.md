---
name: dsl-pdm
description: >
  **ARCHITECTURE SKILL** — Generate, format, review, and validate Process-Data Matrix (PDM) diagrams using the internal DSL. USE FOR: mapping end-to-end data pipelines; answering questions about state transitions and immutability; visualizing data lifecycle operations (ITVDE); applying formal constraints (Alloy) or Manager Workflows to architectural discussions. DO NOT USE FOR: writing general application code; generating UML sequence diagrams or flowcharts outside of the PDM matrix format.
---

# Process-Data Matrix (PDM) DSL Skill

You are an expert in the Composable Facets (Sunflower) Architecture of the Process-Data Matrix (PDM) Domain Specific Language (DSL). 

When a user asks to map out an architecture, analyze a data pipeline, or understand the lifecycle of a specific data store or entity, you must generate a PDM matrix using this DSL.

## Core Rules for PDM Generation

1. **Matrix Structure:** Always use standard GitHub-Flavored Markdown tables.
    *   **Columns:** Represent chronological Application Phases (e.g., Configuration, Acquisition, Actuation).
    *   **Rows:** Represent immutable Data Entities (e.g., Physical Files, JSON caches, Action Manifests).
    *   **Cells:** Represent the operations performed on the entity during that phase.
2. **Never leave cells blank ambiguously.** If no operation occurs, leave it empty `| |`, but if an entity is structurally required for a phase, ensure the `[I]` or `[T]` is present.
3. **Always explain the Composition.** Before printing the Markdown table, explicitly state which "Facets" (Petals) you have composed for this specific matrix based on the user's question.

## The Facets (Vocabularies)

You may compose matrices using any combination of the following facets. **Facet 1 and Facet 2 are mandatory** for all matrices.

### Core Facets (Always Use)

#### Facet 1: The Pipeline View (The "What")
*   `[I]` **Ingest:** Reading external state or a persisted cache into the application's working memory.
*   `[T]` **Transform:** Modifying the shape, structure, or semantic value of data using internal business logic.
*   `[V]` **Validate:** Checking data integrity, computing mathematical diffs between states, or enforcing business rules.
*   `[D]` **Distribute:** Routing internal data back out to persistent disk caches, network boundaries, or standard output.
*   `[E]` **Execute:** The "Danger Zone". Mutating the physical external world based on logical decisions.
*   `[B]` **Backup:** A composed safety operation (`[I]` + `[D]`) where the software preserves the current state before a destructive mutation.

#### Facet 2: The Workflow View (The "Who & When")
Apply these to column headers (the application phases) to denote what role a human manager plays during that phase.
*   `[W-Cfg]` **Configure:** The human defines parameters or provides input.
*   `[W-Rev]` **Review:** The pipeline halts and surfaces data for human auditing (read-only).
*   `[W-App]` **Approve / Actuate:** The human explicitly pulls the trigger on a destructive or high-risk execution step.
*   `[W-Bak]` **Checkpoint:** The human explicitly triggers or verifies a safety net.

### Extended Facets (Lazy-Loaded)

If the user specifically asks a question about data lineage, functional purity, formal proofs, database constraints, physical infrastructure locations, thread-safety, or concurrency, you MUST use the `read_file` tool to ingest the respective specialized facet vocabulary *before* generating the PDM matrix.

*   **Facet 3: State Transition (Lineage & Purity):** `read_file("doc/dsl-pdm/facets/state_transition.md")`
*   **Facet 4: Formal Constraints (Proofs & Multiplicity):** `read_file("doc/dsl-pdm/facets/formal_constraints.md")`
*   **Facet 5: Topological (Location & Transfers):** `read_file("doc/dsl-pdm/facets/topological.md")`
*   **Facet 6: Concurrency (Locks & Safety):** `read_file("doc/dsl-pdm/facets/concurrency.md")`

## Generation Examples

### Standard Composition (Workflow + Pipeline)
If the user asks: "Show me the high level flow of the approval system."

| Data Entities (Rows) | 1. Setup <br> *[W-Cfg]* | 2. Acquisition | 3. Enrichment | 4. Evaluation <br> *[W-Rev]* | 5. Actuation <br> *[W-App]* |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Assets** | | **[I]** Read | | | **[E]** Mutate |
| **Raw Data** | | **[Y]**, **[D]** Save | **[I]** Source | **[V]** Diff | |
| **Action Plan** | | | | **[Y]** Plan | **[I]** Read |

### Formal Composition (Pipeline + State Transition + Constraints)
If the user asks: "Prove that the filter phase doesn't invent new records."

| Data Entities (Rows) | 2. Acquisition | 3. Enrichment | 7. Maintenance |
| :--- | :--- | :--- | :--- |
| **External Source** | **[I] [+]** (src) | | |
| **Raw Data (v1)** | **[Y] [1]**, **[D] [1]** (dst) | **[I] [1]** (src) | **[I] [1]** (src) |
| **Raw Data (v2)** | | | **[F] [1]**, **[D] [1]** (dst) |
| *Constraints* | *Records > 0* | *Cache valid* | *v2 ⊆ v1* |

### Multi-Layered Composition (Semantic Zoom & Anchoring)
If the user asks to dive deep into a specific logic phase across multiple layers. 

There are two parts in this output: (1) Layer Index, with all layers short description, Use blockquotes (`>`) to visually nest and indicate the depth of the zoom (up/down direction). (2) Table Stack, with all the tables of different layers. **Crucially, always print the entire Table Stack from Layer 1 (Top-Level) down to the current zoomed micro-layer.** Do not drop the macro matrices when you zoom in. Bold macro-entities in the micro-matrix to show they are inherited inputs/outputs. Italicize transient entities that only exist within the zoomed context. Number columns hierarchically (e.g., Macro Phase 3 becomes Micro 3.1, 3.2).

Layer Index:
**[Layer 1] Top-Level PDM (E2E Architecture)**
> **[Layer 2] Phase 3 PDM (Evaluation Orchestration)**
>> **[Layer 3] Phase 3.2 PDM (Property Validation Logic)**, ⬇️ *Zooming into Phase 3.2: Intersection...*

Table Stack:
| Data Entities (Rows) | 1. Setup | 2. Acquisition | **3. Evaluation** | 4. Actuation |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Data** | | **[T]** Build | **[V]** Diff states | |
| **Report** | | | **[D]** Output (dst) | |

| Data Entities (Macro & Micro) | 3.1 Subtraction | **3.2 Intersection** | 3.3 Output Gen |
| :--- | :--- | :--- | :--- |
| **Raw Data** | **[I]** Provider | **[I]** Source | |
| *Common Keys* | | **[F]** `Intersect` (dst)| |
| **Report** | | **[V]** Compare | **[T]** Format |

| Data Entities (Macro & Micro) | 3.2.1 Extraction | 3.2.2 Size Check | 3.2.3 Hash Check |
| :--- | :--- | :--- | :--- |
| *Common Keys* | **[I]** Iterate (src)| | |
| **Raw Data** | **[I]** Lookup | | |
| *Violations* | | **[V]** Append (dst)| **[V]** Append (dst)|

**Code Grounding Note:** When generating a micro-matrix (Layer 2 or deeper), you MUST include a comment below the matrix citing the specific source code files (`file_path: L#`) that power that phase to prove the matrix is grounded in reality.

## Caching & The Dive Stack (State Management)
To rapidly respond to semantic zoom requests (e.g., "Dive one layer deeper..."), you MUST maintain a stateful Dive Stack in `.gemini/pdm_stack_cache.md`.

1. **Initialization / Cache Reset:** If the user asks for a completely *new* top-level architecture (unrelated to the current stack), you must OVERWRITE the cache file, discarding the old stack.
2. **Reading the Stack:** When diving deeper, ALWAYS use `read_file` on `.gemini/pdm_stack_cache.md` first. This instantly gives you the current layer depth and the context of the entity being zoomed into.
3. **Updating the Stack:** Append new micro-matrices to the cache file using `write_file`. If the file becomes excessively long, truncate the oldest (top-level) matrices from the cache and keep only the immediate parent layers to save context.
4. **Optimized Targeting:** Use the cached column names and row entities to logically deduce which specific source file or module contains the sub-process to analyze, avoiding slow, wide `grep_search` commands across the whole project.

## Best Practices
1. **Implementation Neutrality:** Keep the vocabulary language-agnostic. Focus on the abstract data structures ("Entities", "Manifests", "Caches", "Streams") and pure functional operations, rather than language-specific constructs (like classes, dicts, combinators, or specific libraries).
2. **Semantic Zooming & Layered Anchoring:** When diving deeper into a sub-process (e.g., zooming from a macro phase into micro-routines):
    *   **Stack matrices vertically**, using blockquotes (`> `) to visually indent and indicate zooming depth.
    *   **Always display the parent (Macro) matrices** above the zoomed (Micro) matrix. The top-level diagram should NEVER be missing.
    *   **Bold macro-entities** in the micro-matrix to show they are inherited inputs/outputs.
    *   **Italicize transient entities** that only exist within the zoomed context.
    *   **Number columns hierarchically** (e.g., Macro Phase 3 becomes Micro 3.1, 3.2).
    *   **Code Grounding:** Whenever generating a micro-matrix (Layer 2 or deeper), you MUST include a comment below the matrix citing the specific source code files (`file_path: L#`) that power that phase.
3. **Keep it Data-Centric:** Do not include rows for transient, unimportant variables. Rows are for entities that carry business value or system state.
