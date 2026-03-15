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

**Machine-Readable Representation (Structural Matrix):**
When this facet is active, the PDM must be accompanied by a YAML block that `combinate.py` can parse.

```yaml
refactor_target: "function_name"
phases:
  - id: 1
    name: "Phase Name"
    operations:
      - entity: "Entity Name"
        op: "I/T/V/D/E"
        directive: "MOVE/WRAP/MERGE"
        target_noun: "noun_name"
```

**Architectural Bottleneck Indicators:**
*   **Tight Coupling:** Multiple entities with `[T]` (Transform) and `[D]` (Distribute) operations in the same phase without a clean handoff.
*   **Monolithic Phase:** A single phase (column) containing too many complex operations on different entities.
*   **IO Tangling:** `[I]` (Ingest) and `[D]` (Distribute) occurring in the middle of a transformation phase.
