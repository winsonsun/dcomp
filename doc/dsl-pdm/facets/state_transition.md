# Facet 3: The State Transition View (The "Which Version")

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