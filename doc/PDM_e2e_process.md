### Background
To build the most effective Process-Data Matrix for understanding the end-to-end (e2e) procedure of your scanner, you need a combination that perfectly bridges what the software is trying to accomplish (The Flow) with how the data actually changes (The Operations).

Based on our discussion separating the Database Layer, the Application Layer, and the User/Manager Layer, the absolute best combination for an e2e engineering blueprint is:

Columns (The Business/System Flow): The Application Phases
Rows (The Entities): The JSON Stores & Physical Assets
Cell Values (The Data Operations): The Application Pipeline (ITVDE)

Here is why this is the best combination and what it looks like:

Why this is the Best Combination for E2E Understanding
It tracks the "Brain" of the system. Using the Application Pipeline operations (Ingest, Transform, Validate, Distribute, Execute) shows you exactly where and when the software is applying business logic vs. just moving bytes around.
It separates logical state from physical state. By having both JSON files (logical) and Physical Files (physical) as rows, you can see how an action in the logical realm eventually triggers an action in the physical realm.
It highlights the system boundaries. You can instantly see where the system touches the outside world (Ingest/Execute) versus where it is operating safely entirely within its own memory/cache.
The Ultimate E2E Process-Data Matrix
Legend (Data Operations - The Application Pipeline):

[I] Ingest (Read external state into memory)
[T] Transform (Enrich, structure, or morph data)
[V] Validate (Check integrity, diffs, or enforce rules)
[D] Distribute (Route data to disk caches, other nodes, or output)
[E] Execute (Mutate the physical external world)

### The E2E Process-Data Matrix

**Legend (Data Operations - The Application Pipeline):**
*   **[I] Ingest** (Read external state into memory)
*   **[T] Transform** (Enrich, structure, or morph data)
*   **[V] Validate** (Check integrity, diffs, or enforce rules)
*   **[D] Distribute** (Route data to disk caches, other nodes, or output)
*   **[E] Execute** (Mutate the physical external world)

| Data Entities (Rows) | 1. Configuration (job, paths) | 2. Acquisition (scan) | 3. Enrichment (scene) | 4. Evaluation (diff, query) | 5. Planning (sync plan) | 6. Actuation (sync exec) | 7. Maintenance (prune, merge) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Files (OS)** | **[I]** Read UUIDs | **[I]** Read stats/hash | | | | **[E]** Copy/Delete | **[I]** Check exists |
| **Job Definitions** | **[T]** Define targets | **[I]** Direct scanner | | **[I]** Aliases for diff | **[I]** Target for sync | | |
| **Path Tokens** | **[T]** Tokenize mount | **[I]** Resolve paths | | **[I]** Resolve paths | **[I]** Resolve paths | **[I]** Resolve paths | **[V]** Check validity |
| **Raw Catalog Cache** | | **[T]** Build tree, **[D]** Save | **[I]** Source data | **[V]** Diff states, **[D]** Report | **[V]** Compare states | | **[V]** Find orphans, **[D]** Save |
| **Scene Metadata** | | | **[T]** Group by regex, **[D]** Save | **[I]** Source data, **[D]** Report | | | **[V]** Drop empty, **[D]** Save |
| **Action Manifests** | | | | | **[T]** Generate plan, **[D]** Save | **[I]** Read plan | |

---

### How this visualizes the E2E Architecture:

1.  **Phases 1 & 2 (The Interface):** The system reaches out to the **Physical Files** `[I]` to gather UUIDs and hashes, **Transforms** `[T]` them into logical tokens and a structured JSON cache, and **Distributes** `[D]` them down to disk.
2.  **Phase 3 (The Brain):** The system stops touching physical files. It **Ingests** `[I]` the raw catalog it just built, **Transforms** `[T]` those strings into semantic scenes, and **Distributes** `[D]` the result to metadata.
3.  **Phases 4 & 5 (The Math):** Entirely logical. It **Validates** `[V]` states against each other to find differences. If a sync is requested, it **Transforms** `[T]` those differences into an action manifest.
4.  **Phase 6 (The Danger Zone):** This is the only place where **[E] Execute** appears. It reads the manifest and safely mutates the **Physical Files**.
5.  **Phase 7 (The Janitor):** It validates internal logical states against the physical truth and rewrites the caches to stay healthy.
