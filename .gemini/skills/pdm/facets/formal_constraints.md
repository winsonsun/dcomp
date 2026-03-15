# Facet 4: The Relational & Constraint View (The "Proof")

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