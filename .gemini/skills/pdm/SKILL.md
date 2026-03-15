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

### Facet 1: The Workflow View (The "Who & When")

*   **Answers:** Who is interacting with the data, and when does it happen?
*   **Focus:** Human-in-the-loop interactions, business processes, and manual system gates.
*   **Use Case:** Designing User Experience (UX), writing user manuals, tracking manual interventions, and auditing safety gates.

**DSL Elements (Modifiers & Super-Headers):**
These are typically applied to the column headers (the application phases) to denote what role a human manager plays during that phase.
*   `[W-Cfg]` **Configure:** The human defines parameters or provides input to shape the upcoming pipeline. (e.g., The user manually editing `jobs.json` before running a scan).
*   `[W-Rev]` **Review:** The pipeline halts and surfaces data for human auditing. No state mutations occur during this step. (e.g., The user reading a `diff` output report in the terminal).
*   `[W-App]` **Approve / Actuate:** The human explicitly pulls the trigger on a destructive or high-risk execution step. (e.g., The user typing `yes` or running `sync execute`).
*   `[W-Bak]` **Checkpoint:** The human explicitly triggers or verifies a safety net before proceeding, securing a known-good state. (e.g., The user manually copying `cache.json` to a backup folder before a major system pruning).

### Facet 2: The Pipeline View (The "What")

*   **Answers:** What is the software doing to the data?
*   **Focus:** The internal machinery of the application, how data flows between memory and storage.
*   **Use Case:** Architecting the core application logic, defining the boundaries of microservices or internal functions, and isolating disk I/O from computation.

**DSL Elements (The ITVDE Operations):**
These are the foundational operations placed inside the matrix cells to represent the application's action upon a data entity during a specific phase.

*   `[I]` **Ingest:** Reading external state or a persisted cache into the application's working memory. (e.g., Parsing `cache.json` into a dictionary).
*   `[T]` **Transform:** Modifying the shape, structure, or semantic value of data using internal business logic. (e.g., Parsing a raw path `/Volumes/A` and converting it to `PATH01`).
*   `[V]` **Validate:** Checking data integrity, computing mathematical diffs between states, or enforcing business rules before proceeding. (e.g., Comparing `dir1` and `dir2` hashes).
*   `[D]` **Distribute:** Routing internal data back out to persistent disk caches, network boundaries, or standard output. (e.g., Calling `atomic_write_json(master_cache)`).
*   `[E]` **Execute:** The "Danger Zone". Mutating the physical external world based on logical decisions. (e.g., Calling `os.remove(file.mp4)` or executing network API commands).
*   `[B]` **Backup:** A composed safety operation (`[I] Ingest` + `[D] Distribute`) where the software preserves the current state of an entity before a destructive mutation occurs. (e.g., The system creating `cache.json.bak` automatically before pruning).

### Facet 3: The State Transition View (The "Which Version")

*   **Answers:** Is this data mutating in-place, or yielding a new immutable copy? Which exact version of a data entity is being read during a specific phase?
*   **Focus:** Strict data lineage, pure functions, and tracking historical state transitions.
*   **Use Case:** Debugging state-related bugs, designing functional or event-sourced architectures, tracking data lineage for auditing.

**DSL Elements (Entity Versioning & Directional Dependency):**
These elements replace or modify the standard rows and cell operations to explicitly track how a single entity evolves over time without destructive overwriting.

*   **Versioning (Row Splitting):** Split a single entity row into multiple rows to represent distinct, immutable versions of that data structure as it progresses through the pipeline.
    *   *Example:* Instead of a single `Raw Catalog` row, use `Raw Catalog (v1 - Persisted)` and `Raw Catalog (v2 - Pruned)`.
*   **Directional Dependency:** Append modifiers to the operations within cells to clearly indicate if the entity is acting as a source or destination for that operation.
    *   `(`**`src`**`)`: The immutable source data read by an operation.
    *   `(`**`dst`**`)`: The newly generated immutable destination resulting from an operation.
*   **Functional Operators (YRF):** These replace the generic `[T] Transform` to be mathematically precise about the mutation.
    *   `[Y]` **Yield:** Explicitly denotes generating a brand new, immutable data structure derived from prior inputs.
    *   `[R]` **Reduce:** Aggregating, folding, or summarizing a dataset into a smaller, synthesized form (e.g., tallying total bytes).
    *   `[F]` **Filter:** Processing an existing dataset into a smaller, immutable subset by removing items that do not meet a predicate (e.g., pruning missing files).


### Facet 4: The Relational & Constraint View (The "Proof")

*   **Answers:** What mathematical rules govern the existence or cardinality of this data? What logical facts must be true for a phase to be considered complete and safe?
*   **Focus:** Formal verification, invariants, relational logic, and test-driven development (TDD) prerequisites.
*   **Use Case:** Designing database schemas, defining constraints for multi-node operations, validating unit/integration tests mathematically.

**DSL Elements (Multiplicity & State Constraints):**
Inspired by structural modeling languages like Alloy, this facet bounds the state transitions defined in Petal 2 and Petal 3 with mathematical proofs.

*   **Relational Multiplicity (Cell Cardinality Modifiers):** Appended directly to operations, these define *how many* instances of a data entity are involved in a specific phase.
    *   `[1]` **Exactly one:** Represents a singular, definitive entity. (e.g., `[D] [1]` - Writes exactly one master `cache.json` file).
    *   `[?]` **Zero or one:** An optional entity that may not be produced. (e.g., `[Y] [?]` - A Diff phase may or may not yield a manifest depending on whether any changes were found).
    *   `[*]` **Zero or more:** Represents unbounded ingestion or processing. (e.g., `[I] [*]` - Ingests many remote cache shards during a massive sync).
    *   `[+]` **One or more:** Represents a guaranteed minimum batch of entities. (e.g., `[E] [+]` - A guaranteed batch deletion of multiple dead paths).

*   **State Constraints (Invariant Assertions):** Defines the mathematical or logical invariants that must hold true for a specific column's phase to be considered valid and structurally sound.
    *   **Implementation:** Add a `Constraint:` row to the absolute bottom of the matrix. Provide assertions using standard relational logic symbols (`⊆` subset, `==` equality, `>` greater than).
    *   *Example Assertions:* 
        *   `v2 ⊆ v1` (The new `cache (v2)` is a strict subset of `v1`, proving the system didn't magically invent new files during a prune operation).
        *   `Cache.Hashes == Valid` (Every file entry in the cache must have a successfully computed SHA-256 hash before proceeding).

### Facet 5: The Topological View (The "Where")

*   **Answers:** Where does this data physically rest, or over what network boundaries does it travel?
*   **Focus:** Physical infrastructure, network topology, storage tiers, and data gravity.
*   **Use Case:** Optimizing I/O bottlenecks, designing distributed systems, planning hardware infrastructure, and auditing data residency or security boundaries.

**DSL Elements (Location Annotations & Data Gravity Indicators):**
These annotations bind the logical data entities and their operations to physical hardware or network locations, making the cost of `[I] Ingest` and `[D] Distribute` operations explicitly clear.

*   **Location Annotations (`@Location`):** Appended either to the Data Entity (Row Header) to denote where the data rests, or directly to an Operation Cell to denote where the compute/transfer is happening.
    *   `@RAM` / `@Memory`: Data exists only in volatile memory.
    *   `@LocalDisk` / `@NVMe`: Data rests on fast, local block storage.
    *   `@NAS` / `@Network_SMB`: Data rests on remote, slow, or shared network storage.
    *   `@Cloud_S3` / `@AWS`: Data rests in a cloud object store.
*   **Data Gravity Indicators (`→` Transfers):** When an operation forces data to cross a topological boundary, you can denote the transfer explicitly.
    *   *Example:* `[D] → @NAS` (Distributing a local cache over the network to a NAS).
    *   *Example:* `[I] ← @Cloud_S3` (Ingesting a remote manifest down to local memory).

### Facet 6: The Concurrency View (The "How Safely")

*   **Answers:** Can multiple actors touch this data at the same time? Are these operations thread-safe, synchronous, or asynchronous?
*   **Focus:** Parallelism, distributed state locks, race conditions, atomic operations, and system safety nets.
*   **Use Case:** Designing multi-threaded architectures, distributed systems (like cross-network syncs), and database-level transactional guarantees.

**DSL Elements (Locking Mechanisms & Atomicity Guarantees):**
These annotations explicitly declare the thread-safety and read/write locking requirements for the operations defined in Petal 2.

*   **Lock Annotations (`[Lock-*]`):** Appended directly to operations, these define the type of lock the system must acquire before reading or mutating the data entity.
    *   `[Lock-R]` **Shared Read Lock:** Multiple processes can read this entity simultaneously (e.g., multiple worker nodes reading the same `jobs.json` file), but no process can write to it.
    *   `[Lock-W]` **Exclusive Write Lock:** Only one process can mutate this entity (e.g., the primary orchestrator updating `cache.json` after a prune). All other reads/writes are blocked.
*   **Atomicity Guarantees (`[Atomic]`):** Appended to operations that must succeed entirely or fail entirely without leaving the data in a corrupt intermediate state.
    *   *Example:* `[D] [Atomic]` (Writing the `sync_manifest.json` completely to disk or rolling back the transaction if the disk fills up halfway).
*   **Execution Markers (`[Async]` / `[Sync]`):** Appended to column headers (phases) or specific operations to denote whether the main application thread halts and waits, or fires and forgets.
    *   *Example:* Phase Header: `4. Actuation [Async]` (The system launches background workers to perform network transfers).

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
