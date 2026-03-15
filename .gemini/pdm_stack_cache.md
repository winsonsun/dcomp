# PDM Dive Stack Cache

Layer Index:
**[Layer 1] Top-Level PDM (E2E Architecture)**
> **[Layer 2] Phase 4 PDM (Evaluation Orchestration)**
>> **[Layer 3] Phase 4.3 PDM (Intersection Logic)**

Table Stack:

| Data Entities (Rows) | 1. Setup | 2. Acquisition | 3. Enrichment | **4. Evaluation** | 5. Planning | 6. Actuation | 7. Maintenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Physical Files (OS)** | **[I]** Read UUIDs | **[I]** Read Stats/Hash | | | | **[E]** Copy/Delete | **[I]** Check exists |
| **Configuration (Jobs/Paths)** | **[T]** Define, **[D]** Save | **[I]** Direct scanner | | **[I]** Resolve aliases | **[I]** Target for sync | **[I]** Resolve paths | **[V]** Check validity |
| **JSON Caches**| | **[T]** Build, **[D]** Save | **[T]** Group, **[D]** Save | **[V]** Diff states, **[D]** Report| **[V]** Compare states | | **[V]** Prune, **[D]** Save |
| **Action Manifests** | | | | | **[T]** Plan, **[D]** Save | **[I]** Read plan | |

| Data Entities (Macro & Micro) | 4.1 Input Resolution | 4.2 Subtraction | **4.3 Intersection** | 4.4 Property Analysis | 4.5 Output Generation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Configuration (Jobs/Paths)** | **[I]** Resolve URI | | | | |
| **JSON Caches**| **[I]** Read target | | | | |
| *State Dictionaries (L/R)* | **[Y]** Yield sub-tree | **[I]** Input streams | **[I]** Input streams | **[I]** Lookup | |
| *Common Keys* | | | **[V]** Extract joint (dst) | **[I]** Iterate | |

| Data Entities (Macro & Micro) | 4.3.1 Target Resolution | 4.3.2 Optimization Matrix | 4.3.3 Mathematical Filter | 4.3.4 Collection Yield |
| :--- | :--- | :--- | :--- | :--- |
| *State Dictionaries (L/R)* | **[I] [1]** Evaluate provider | **[I] [1]** Read B-keys | **[I] [1]** Iterate A-stream | |
| *B-Key Hash Set* | | **[T] [1]** `set()` Conversion | **[V] [1]** `O(1)` Lookups | |
| *Intersection Buffer* | | | **[V] [*]** Append matching | **[Y] [1]** Yield collection |
| **Common Keys** | | | | **[D] [1]** Finalize Array/Dict |
