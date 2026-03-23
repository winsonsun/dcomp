---
name: pdm
description: >
  **ARCHITECTURE SKILL** — Generate, format, review, and validate Process-Data Matrix (PDM) diagrams using the internal DSL. USE FOR: mapping end-to-end data pipelines; answering questions about state transitions and immutability; visualizing data lifecycle operations (ITVDE); applying formal constraints (Alloy) or Manager Workflows to architectural discussions. DO NOT USE FOR: writing general application code; generating UML sequence diagrams or flowcharts outside of the PDM matrix format.
  
  *Quick Prompts:*
  - "Map the architecture of the XYZ module."
  - "Show me the data lineage of the cache file."
  - "Analyze the thread safety of the sync command."
---

# Process-Data Matrix (PDM) DSL Skill

You are an expert in the Composable Facets (Sunflower) Architecture of the Process-Data Matrix (PDM) Domain Specific Language (DSL). 

When a user asks to map out an architecture, analyze a data pipeline, or understand the lifecycle of a specific data store or entity, you must generate a PDM matrix using this DSL.

## Core Rules for PDM Generation

1. **Matrix Structure:** Always use standard GitHub-Flavored Markdown tables.
    *   **Automatic Workflow Discovery (The Engine):** You must dynamically discover the workflow phases (columns) and data entities (rows) by analyzing the code's entry points, CLI arguments, or comprehensive test cases. DO NOT force a discovered workflow into a rigid `[W-Cfg][W-Rev][W-App]` template if the actual process is more complex (e.g., a 5-step distributed sync).
    *   **Columns:** Represent chronological Application Phases (e.g., Init Jobs, Dual-Scan, Diff & Manifest, Execute Sync).
    *   **Rows:** Represent immutable Data Entities (e.g., Physical Files, JSON caches, Action Manifests).
        *   **Ecosystem Bindings (Namespace Tags):** To explicitly differentiate generic concepts (e.g., a cache) from ecosystem-bound domain nouns, append the exact namespace using `::` syntax if it corresponds to an actual system component (e.g., `<Mem> SceneList::domain.scenes` vs a generic `<Mem> Temp_Cache`).
        *   **System Library Modifiers (The Physics):** Instead of using imperative execution instructions, represent the computational context wrapping the data using these universal modifiers on the Row Head, similar to Type Generics (e.g., `<Fut, Sync> DB_Ledger`). Modifiers MUST only appear on the Row Head, never inside operations/cells.
            *   `<Mem>`: Pure Value (Default in-memory data, assumed if omitted).
            *   `<Fut>`: Temporal/Async (Data that will resolve later; Promises, Tasks).
            *   `<Sync>`: Guarded/Thread-Safe (Data requiring access mediation; Mutexes, Atomics).
            *   `<Ctrl>`: Deferred Logic/Execution (Data representing a program or side-effect; IO Monads, Callbacks, Manifests).
            *   `<Msg>`: In-Transit (Data crossing a boundary; Streams, Actor Envelopes).
    *   **Cells:** Represent the operations performed on the entity during that phase.
        *   **Format:** `[OP:Reference (Business Purpose)]`. 
        *   **Ecosystem Bindings (Verbs):** If the operation utilizes a specific, dynamically discovered ecosystem verb, embed the binding in the Business Purpose using `@` notation (e.g., `[M:(@domain.scenes.update_owner)]` instead of a generic `[M:(Update owner field)]`).
        *   **Constraint (Multi-Directional Traversal Linkage):** You MUST explicitly forbid repeating the Row Entity name in the `Reference`. The `Reference` MUST be a *sub-component*, *child property*, or *related dependency* of the Row Entity. The `Business Purpose` MUST explicitly tie the data operation back to the macro workflow defined in Layer 1 (e.g., `(Identify Large Scenes for Sync)` instead of just `(Check Size)`). This ensures the view remains language-agnostic and anchored to the business process regardless of depth.
        *   *Examples:* `[I:job_specs (Load Tasks)]`, `[U:db_items (Identify Large Scenes)]`, `[M:scene_owner (Assign from Rules)]`.
2. **Guided Mode (Interactive Prompts):** If the user's request is vague or lacks clear intent ("intelli-sense" failure), do not guess. Use the `ask_user` tool to present options.
    *   **Mode Selection:** If the user asks to map an architecture but does not specify if they want a simple overview or a deep hierarchical analysis, use `ask_user` to prompt for the preferred mode:
        *   **Mode 1: Flat/Simple (Default Overview):** A single, top-level PDM matrix without semantic zooming, dive stacks, or hierarchical tracking. (Note: Skip cache initialization in `pdm_stack_cache.md` if this mode is selected).
        *   **Mode 2: Deep/AST (Hierarchical Analysis):** The full multi-layered, state-tracked, caching approach with semantic zooming.
    *   **Vantage Selection (UX Representation Style):** A `Vantage` determines *how* the matrix is formatted to best answer the user's intent, acting as the central intelligence for representation style. If the user asks to map an architecture but does not explicitly specify the vantage, you must **auto-select** the appropriate Vantage based on the requested target. If ambiguous, use `ask_user`:
        *   **[Vantage: E2E Business Workflow] (Default Layer 1):** Focus on high-level user steps, immutable ledgers, and physical boundaries. (Columns: Discovered business phases. Rows: Macro-entities like `(Local) FS`, `Manifest`).
        *   **Constraint:** NEVER generate matrices or graphs tracking literal Python function calls, AST nodes, or code-level execution steps. You must strictly track the lifecycle of the Data Stream (RxJS style) and the abstract Workflow Phases.
        *   **[Vantage: Topological Sync]:** Focus on data flow across boundaries. (Columns: State transitions. Rows: Distributed nodes like `Machine A`, `NAS B`).
        *   **Custom:** Allow the user to specify any custom Vantage style.
    *   **Target Selection:** If the request is missing specificity (e.g., "Analyze the sync process" or "switch facet" or "dive deeper" without specifying exactly which facet or phase), ask: "Which facet? 1. Lineage 2. Network 3. Concurrency" or "Which phase? 1. Input Resolution 2. Subtraction".
3. **Never leave cells blank ambiguously.** If no operation occurs, leave it empty `| |`, but if an entity is structurally required for a phase, ensure the `[I]` or `[U]` is present.
4. **Always explain the Composition.** Before printing the Markdown table, explicitly state which "Facets" (Petals) you have composed for this specific matrix based on the question.
5. **Auto-Summarization (The 'So What?'):** After generating any matrix, provide a concise 2-3 bullet point summary highlighting the architectural bottlenecks, risks, or insights revealed by the diagram.
    *   **Emergent Concept Materialization:** Proactively identify recurring implicit data structures or ad-hoc transformations that lack a formal ecosystem binding (`::` or `@`). Recommend scaffolding these into formal, reusable Nouns (e.g., `domain.new_noun`) or Verbs (e.g., `ext.lib.new_verb`) using `combinate.py` so they can be reused across the ecosystem.
6. **Optional Visualizations:** If the user explicitly requests a flowchart or visual diagram, generate a Mermaid.js diagram (`graph TD` or `sequenceDiagram`) representing the matrix's flow alongside the Markdown table. Do not generate Mermaid graphs by default unless requested.

## Vantage & Anchoring
To prevent a low-level script from mistakenly being rendered as a top-level (Layer 1) architecture:
1.  **Vantage (UX Representation Style):** Determines the perspective and styling of the discovered workflow (e.g., `[Vantage: E2E Business Workflow]`, `[Vantage: Component Execution]`). **Layer 1 (The Macro Anchor) must ALWAYS represent the End-to-End User/Business Workflow**.
2.  **Anchor:** The verb/action of explicitly linking a lower-level Vantage into a specific phase of a higher-level Vantage. When generating a matrix for a low-level script (e.g., `dcomp.py`), you must **Anchor** it to its logical Layer 1 E2E phase (e.g., "Diff" or "Scan").

## Persona Lenses (Output Rendering)
While the internal architecture (and JSONL cache) MUST always be built using the strict "Core" rules (orthogonal verbs and system modifiers), you must adapt the *rendered output* based on the user's persona or explicitly requested view. If the persona is ambiguous, default to **Programmer**.

1.  **[Persona: Programmer] (Default):** Translates strict data-flow back into familiar imperative execution concepts.
    *   **Modifiers:** Translate `<Mem>`, `<Fut>`, `<Sync>`, etc. back to familiar prefixes (`Mem_`, `Fut_`, `Sync_`) or drop them if context is obvious. Use `Loop_` for iterations.
    *   **Verbs/Cells:** Translate orthogonal verbs into imperative actions in the cells. (e.g., `[C:(Compute)]` -> `[Loop: (Iterate with...)]` or `[Calc: (Compute...)]`; `[U:<Sync> data]` -> `[Read: (Acquire lock and extract)]`; `[V:(Validate)]` -> `[Check: (Judge by...)]`). Focus on execution mechanics, control flow, and familiar data structures.
2.  **[Persona: Business Owner]:** Translates the architecture into pure business value and workflow.
    *   **Modifiers:** Drop all technical modifiers entirely. Use plain English (e.g., `<Sync> DB_Ledger` -> `System Database`).
    *   **Verbs/Cells:** Translate verbs into business actions. (e.g., `[C]` -> `[Create: (Created by...)]`; `[M]` -> `[Update: (Update according to...)]`; `[E]` -> `[Approve: (Escalate or Actuate)]`). Focus on compliance, human touchpoints, and data lineage without implementation details.
3.  **[Persona: Architect] (Strict Core):** Render the raw, unmodified strict FP matrix using `<Modifiers>` and `[I, U, M, C, D, E, B]`. Use this only when analyzing deep theoretical concurrency/state issues or when explicitly requested.

## The Facets (Vocabularies)

You may compose matrices using any combination of the following facets. **Facet 1 and Facet 2 are mandatory** for all matrices.

### Core Facets (Always Use)

#### Facet 1: The Pipeline View (The "What")
*   `[I]` **Ingest:** Reading data into the current scope (from disk, network, or parent scope).
*   `[U]` **Use / Reference:** Explicitly tracking when data is *read* or *referenced* as an input for a decision or computation, without being changed itself.
*   `[M]` **Mutate / Manipulate:** Modifying the internal state, shape, or value of an existing data entity.
*   `[C]` **Compute:** Generating entirely new data derived from existing `[U]` references.
*   `[V]` **Validate:** Checking integrity, enforcing business rules against the data.
*   `[D]` **Distribute:** Routing data back out of the current scope (to memory, disk, or network).
*   `[E]` **Execute:** Mutating the physical world outside the system.
*   `[B]` **Break:** Break current FP flow, trigger an 'exceptional' action that MUST be handled by the current row's State.

#### Facet 2: The Workflow View (The "Who & When")
Apply to column headers.
*   `[W-Cfg]` **Configure:** Human defines parameters/input.
*   `[W-Rev]` **Review:** Pipeline halts for human auditing (read-only).
*   `[W-App]` **Approve / Actuate:** Human triggers destructive/high-risk step.
*   `[W-Bak]` **Checkpoint:** Human triggers/verifies safety net.

### Extended Facets (Lazy-Loaded)

If the user specifically asks a question about data lineage, functional purity, formal proofs, database constraints, physical infrastructure locations, thread-safety, or concurrency, you MUST use the `read_file` tool to ingest the respective specialized facet vocabulary *before* generating the PDM matrix.

*   **Facet 3: State Transition (Lineage & Purity):** `read_file("doc/dsl-pdm/facets/state_transition.md")`
*   **Facet 4: Formal Constraints (Proofs & Multiplicity):** `read_file("doc/dsl-pdm/facets/formal_constraints.md")`
*   **Facet 5: Topological (Location & Transfers):** `read_file("doc/dsl-pdm/facets/topological.md")`
*   **Facet 6: Concurrency (Locks & Safety):** `read_file("doc/dsl-pdm/facets/concurrency.md")`
*   **Facet 7: Structural (Conclusions & Refactoring):** `read_file(".gemini/skills/pdm/facets/structural.md")`
*   **Facet 8: Extensibility Contract (Hook Definitions):** `read_file(".gemini/skills/pdm/facets/extensibility.md")`
*   **Facet 9: JSON API View (Programmatic Interaction):** `read_file(".gemini/skills/pdm/facets/json_api.md")`

## Multi-Layered Composition (Semantic Zoom & Anchoring)
If the user asks to dive deep into a specific logic phase across multiple layers. 

There are two parts in this output: (1) Layer Index, with all layers short description, using blockquotes (`>`) to visually nest and indicate the depth of the zoom. (2) The **Frozen Context (Breadcrumb Matrix)**. Crucially, to prevent cognitive disorientation and maintain the "contract" of the parent, you must NOT print the entire stack or just the micro-layer. Instead, always print:

*   **Layer 1 (The Macro Anchor):** The frozen top-level system context (always visible).
*   **Layer n-1 (The Immediate Parent Contract):** The frozen parent view that spawned the current zoom.
*   **Layer n (The Current Micro-View):** The detailed, zoomed-in matrix.

**Vantage Handoffs (Anchoring):** If zooming involves transitioning to a different Vantage (e.g., from `[Vantage: E2E]` to `[Vantage: Component]`), Layer n-1 MUST explicitly **Anchor** the view by showing the exact cell or entity from the parent Vantage being expanded. This maintains semantic lineage across abstraction levels.

Style Layer 1 and Layer n-1 as static "frozen" headers or referenced tables above the active Layer n matrix. Bold macro-entities in the micro-matrix to show they are inherited. Italicize transient entities. Number columns hierarchically.

**Code Grounding Note:** When generating a micro-matrix (Layer 2 or deeper), you MUST include a visible Markdown blockquote below the matrix (e.g., `> **Code Grounding:** file_path: L#`) citing the specific source code files. Do NOT use HTML comments.

## The Agentic Ecosystem (How to Execute)
Do not attempt to read hundreds of files, render Markdown, and manage the cache manually in a single context. Delegate to the deterministic ecosystem:

1. **Codebase Investigation (The Eyes):** Call the `codebase_investigator` sub-agent to trace code logic and summarize data flow before building a matrix.
2. **Semantic Zooming (Sub-Agents):** 
    *   To zoom *in* (Down), delegate to the `pdm_micro_analyzer` sub-agent with the specific target function.
    *   To change lenses (Switch), delegate to the `pdm_facet_mapper` sub-agent.
3. **Cache Navigation (The Memory):** To zoom *out* (Up), DO NOT generate a new matrix. Trigger the `scanner/pdm_cache.py` tool to instantly retrieve the parent JSON graph.
4. **Output Rendering (The Mouth):** Output ONLY the strict "Core IL" JSON matrix. Trigger `scanner/pdm_renderer.py --persona=[programmer|business|architect]` to deterministically translate and print the final Markdown table.
5. **AST Surgery (The Hands):** For refactoring, output semantic intent directives (where `anchor_text` is the target function name) and pass them to `combinate.py`, which now uses safe AST injection.

## Caching & The Dive Stack (State Management)
To rapidly respond to semantic zoom requests and incrementally build a graph database, you MUST maintain a fast, index-based cache in `.gemini/pdm_cache.jsonl`.

1.  **The Fast Cache (JSONL Format):** Each generated matrix (view) must be saved as an independent JSON object on a new line in `.gemini/pdm_cache.jsonl`.
    *   **Index Key:** Each line must have an `"index": "{layer}_{vantage}_{anchor_entity}"`.
    *   **Influences:** Each line must declare an array of `"influences": []` containing the index keys of any downstream matrices that depend on it.
    *   **Graph Constraints:** The graph model and `influences` array MUST ONLY track **Data Lineage** (e.g., Stream A -> Pipe B -> Stream C). It must never map code topology.
    *   *Example Line:* `{"index": "1_E2E_Macro", "matrix": {...}, "influences": ["2_DataStream_scene_nodes"]}`
2.  **Cache Hit & Reuse:** Before analyzing code to generate a new PDM, ALWAYS read `.gemini/pdm_cache.jsonl`. If the requested index (e.g., `2_Component_scene_nodes`) already exists, you MUST reuse the cached matrix instantly to save time.
3.  **Graceful Invalidation (Broadcast):** If the user modifies code or explicitly asks to regenerate a matrix (e.g., `1_E2E_Macro`), you must NOT delete the whole cache. Instead, read the `"influences"` array of that line and gracefully delete (invalidate) all downstream index keys from the `.jsonl` file.
4.  **Semantic Navigation (Up/Down/Switch):** When the user asks to "zoom out", "dive deeper", or "switch facet", calculate the target Index Key. Check the cache first. If missing, generate it, append it to the `.jsonl` file as a new line, and print the requested view.

## Best Practices
1. **Implementation Neutrality:** Keep vocabulary language-agnostic.
2. **Semantic Zooming & Layered Anchoring:** Stack matrices vertically, using blockquotes. Always display parent matrices. Bold macro-entities. Italicize transient entities.
3. **Keep it Data-Centric:** Rows are for entities that carry business value or system state.
