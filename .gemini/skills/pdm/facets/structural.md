# Facet 7: The Structural View (The "Conclusion & Refactor")

*   **Answers:** How should this procedural logic be decomposed into functional Combinators?
*   **Focus:** Decoupling, reusability, modularity, and automated code surgery.
*   **Use Case:** Generating machine-readable refactoring plans for `combinate.py` to execute.

**DSL Elements (Refactoring Directives):**
These directives indicate specific code transformations that are required to align the target procedural logic with the Combinator DSL architecture.

*   **Refactoring Directives:**
    *   `[MOVE]`: Extract logic from a procedural function and move it into a standalone `Combinator` or `Noun` method.
    *   `[WRAP]`: Wrap raw data or a primitive callable in a `Rule` object.
    *   `[MERGE]`: Combine redundant data transformations into a single `Map` or `FlatMap` step.
    *   `[PIPELINE]`: Orchestrate the new components using the `Stream` fluent API.

**Machine-Readable Representation (Structural Directives Stream):**
When this facet is active, the PDM must be accompanied by a JSONL block that `combinate.py` can execute sequentially. Each line represents a deterministic text mutation.

```jsonl
{"op": "scaffold_noun", "target": "filters", "description": "Global file filtering policies"}
{"op": "scaffold_verb", "noun": "filters", "verb": "reject_tmp", "description": "Reject .tmp files during pre_scan"}
{"op": "inject_code", "file": "dcomp/modes.py", "anchor_text": "scan_steps = [FS_Scan(base_path, do_hash=args.hash)]", "position": "after", "content": "                \n                # [INJECTED BY PDM] Apply global pre_scan filters\n                pre_scan_rules = policy.get_rules('pre_scan', context)\n                for r in pre_scan_rules:\n                    scan_steps.append(Filter(r))\n"}
{"op": "snapshot", "label": "pre_refactor_baseline"}
{"op": "verify", "against": "pre_refactor_baseline", "on_fail": "rollback"}
```

**JSONL Schema `op` Codes:**
*   `scaffold_noun`: Creates a new noun module. Requires `target`.
*   `scaffold_verb`: Injects a new verb into a noun. Requires `noun`, `verb`.
*   `inject_code`: Modifies code. Requires `file`, `anchor_text` (exact literal text match), `position` (`before`, `after`, `replace`), and `content`.
*   `snapshot`: Captures the `ScanContext` state to a file. Requires `label`.
*   `verify`: Compares the current `ScanContext` state to a snapshot. Requires `against`.

**Architectural Bottleneck Indicators:**
*   **Tight Coupling:** Multiple entities with `[T]` (Transform) and `[D]` (Distribute) operations in the same phase without a clean handoff.
*   **Monolithic Phase:** A single phase (column) containing too many complex operations on different entities.
*   **IO Tangling:** `[I]` (Ingest) and `[D]` (Distribute) occurring in the middle of a transformation phase.
