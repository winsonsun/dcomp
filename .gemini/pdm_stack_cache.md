# PDM Dive Stack Cache

Layer Index:
**[Layer 1] Top-Level PDM (E2E Architecture)**
> **[Layer 2] Phase 4 PDM (Evaluation Orchestration)**
>> **[Layer 3] Phase 4.2 PDM (Subtraction Logic)**

Table Stack:

| Data Entities (Rows) | 1. Setup (`job`, `paths`) <br> *[W-Cfg]* | 2. Acquisition (`scan`) | 3. Enrichment (`scene`) | **4. Evaluation (`diff`, `query`)** <br> *[W-Rev]* | 5. Planning (`sync plan`) | 6. Actuation (`sync exec`) <br> *[W-App]* | 7. Maintenance (`prune`, `merge`) <br> *[W-Cfg]* |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Files (OS)** | **[I]** Read UUIDs | **[I]** Read Stats/Hash | | | | **[E]** Copy/Delete | **[I]** Check exists |
| **Configuration (Jobs/Paths)** | **[T]** Define targets, **[D]** Save | **[I]** Direct scanner | | **[I]** Resolve aliases | **[I]** Target for sync | **[I]** Resolve paths | **[V]** Check validity |
| **JSON Caches**| | **[T]** Build tree, **[D]** Save | **[T]** Group by regex, **[D]** Save | **[V]** Diff states, **[D]** Report | **[V]** Compare states | | **[V]** Prune/Merge, **[D]** Save |
| **Action Manifests** | | | | | **[T]** Generate plan, **[D]** Save | **[I]** Read plan | |

| Data Entities (Macro & Micro) | 4.1 Input Resolution | **4.2 Subtraction (`Difference`)** | 4.3 Intersection (`Intersect`) | 4.4 Property Analysis | 4.5 Output Generation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Configuration (Jobs/Paths)** | **[I]** Resolve URI (src) | | | | |
| **JSON Caches**| **[I]** Read target (src) | | | | |
| *State Dictionaries (L/R)* | **[Y]** Yield sub-tree (dst) | **[I]** Input streams (src) | **[I]** Input streams (src) | **[I]** Lookup properties (src) | |
| *Unique Keys (L/R)* | | **[F]** Extract disjoint (dst) | | | **[I]** Read (src) |
| *Common Keys* | | | **[F]** Extract joint (dst) | **[I]** Iterate (src) | |
| *Property Discrepancies* | | | | **[Y]** Compare vals (dst) | **[I]** Read (src) |
| *Formatted Report* | | | | | **[Y]** Format (dst), **[D]** Output |

| Data Entities (Macro & Micro) | 4.2.1 Target Resolution | 4.2.2 Optimization Matrix | 4.2.3 Mathematical Filter | 4.2.4 Collection Yield |
| :--- | :--- | :--- | :--- | :--- |
| *State Dictionaries (L/R)* | **[I]** Evaluate provider (src) | **[I]** Read B-keys (src) | **[I]** Iterate A-stream (src) | |
| *B-Key Hash Set* | | **[Y]** `set()` Conversion (dst) | **[I]** `O(1)` Lookups (src) | |
| *Disjoint Buffer* | | | **[F]** Append missing (dst) | **[I]** Read collection (src) |
| *Unique Keys (L/R)* | | | | **[Y]** Finalize Array/Dict (dst) |