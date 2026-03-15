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

You may compose matrices using any combination of the following facets. **Facet 1 is mandatory** for all matrices.

### Facet 1: The Pipeline & Workflow View (Mandatory Base)
Describes the core data pipeline (`what the software is doing`) overlaid with the Manager Layer (`what the human is doing`).

**The Application Operations (ITVDE + Safety):**
*   `[I]` **Ingest:** Read external state or persisted cache into memory.
*   `[T]` **Transform:** Modify shape/structure of data. Apply business logic.
*   `[V]` **Validate:** Check integrity, compute diffs, enforce rules.
*   `[D]` **Distribute:** Route data to disk caches, network, or stdout.
*   `[E]` **Execute:** Mutate the physical external world (e.g., disk I/O, API calls).
*   `[B]` **Backup:** Preserving state before a destructive mutation (Composed `[I]` + `[D]`).

**The Manager Layer Modifiers (Super-Headers):**
Apply these to column headers to represent Human-in-the-Loop workflows:
*   `[W-Cfg]` **Configure:** Human defines parameters shaping the pipeline.
*   `[W-Rev]` **Review:** Pipeline halts for human auditing (read-only).
*   `[W-App]` **Approve:** Human pulls the trigger on high-risk execution.
*   `[W-Bak]` **Checkpoint:** Human triggers/verifies a safety net.

### Facet 2: The State Transition View (Lineage & Immutability)
Use this facet when the user asks about functional purity, data lineage, or state changes.
*   **Versioning:** Split rows to represent immutable states (e.g., `Entity (v1)`, `Entity (v2)`).
*   **Direction:** Append `(src)` or `(dst)` to cell operations to show the flow of functional inputs and outputs.
*   **Functional Operators:** Use `[Y] Yield`, `[R] Reduce`, `[F] Filter` in place of `[T] Transform` to be mathematically precise about the mutation.

### Facet 3: The Formal Constraint View (Alloy Extension)
Use this facet when the user asks about formal verification, relational multiplicity, or test prerequisites.
*   **Multiplicity:** Append cardinality to operations: `[1]` (exactly one), `[?]` (zero or one), `[*]` (zero or more), `[+]` (one or more). Example: `[D] [1]`
*   **Constraints:** Add a `Constraint:` row to the bottom of the matrix. Provide a mathematical or logical assertion that must be true for that column's phase (e.g., `v2 ⊆ v1` or `Records > 0`).

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

## Caching & The Dive Stack (State Management)
To rapidly respond to semantic zoom requests (e.g., "Dive one layer deeper with '4.3 Intersection...'") without having to slowly re-read or search the codebase blindly, you MUST maintain a stateful Dive Stack in a local cache file (e.g. `.gemini/pdm_stack_cache.md`).

1. **Initialization:** When creating the first top-level PDM diagram, save it to `.gemini/pdm_stack_cache.md` using the `write_file` tool. Include both the Layer Index and the full Table Stack.
2. **Reading the Stack:** When asked to dive deeper, ALWAYS begin by reading `.gemini/pdm_stack_cache.md` using the `read_file` tool. This instantly gives you:
    * The current layer depth (e.g., Level 2).
    * The parent macro-phases, exact column names, and row entities.
    * The context of the entity being zoomed into (e.g., "4.3 Intersection [V] Extract joint").
3. **Optimized Targeting:** By checking the cache first, you avoid running slow, wide `grep_search` commands across the whole project. You can immediately identify the bounds of the macro-phase and logically deduce which specific source file or module contains the sub-process to analyze.
4. **Updating the Stack:** After generating the new micro-matrix, append it to the cache file (or overwrite it with the complete, updated stack) using the `write_file` tool.

## Best Practices
1. **Implementation Neutrality:** Keep the vocabulary language-agnostic. Focus on the abstract data structures ("Entities", "Manifests", "Caches", "Streams") and pure functional operations, rather than language-specific constructs (like classes, dicts, combinators, or specific libraries).
2. **Semantic Zooming & Layered Anchoring:** When diving deeper into a sub-process (e.g., zooming from a macro phase into micro-routines):
    *   **Stack matrices vertically**, using blockquotes (`> `) to visually indent and indicate zooming depth.
    *   **Always display the parent (Macro) matrices** above the zoomed (Micro) matrix. The top-level diagram should NEVER be missing.
    *   **Bold macro-entities** in the micro-matrix to show they are inherited inputs/outputs.
    *   **Italicize transient entities** that only exist within the zoomed context.
    *   **Number columns hierarchically** (e.g., Macro Phase 3 becomes Micro 3.1, 3.2).
3. **Keep it Data-Centric:** Do not include rows for transient, unimportant variables. Rows are for entities that carry business value or system state.
