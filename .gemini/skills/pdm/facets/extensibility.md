# Facet 8: The Extensibility Contract View (The "Where to Inject")

*   **Answers:** Where are the safe injection points (hooks), and what are the data contracts for plugins?
*   **Focus:** API boundaries, hook discovery, data validation, and idempotency.
*   **Use Case:** Providing `combinate.py` and developers with the exact technical requirements for implementing new policies.

**DSL Elements (Extension Annotations):**
These annotations define the "sockets" where Approach A dynamic rule injection happens.

*   **Extension Hook (`[H]`):** Placed in a phase cell to denote a named extension point.
    *   *Example:* `[H:pre_scan]`
*   **Data Contract (`<Type>`):** Appended to a hook or entity to denote the expected data shape.
    *   *Example:* `[H:post_tokenize] <Dict[str, Props]>`
*   **Constraint Flags:**
    *   `!PURE`: Injected rule MUST be a pure function (no side effects).
    *   `!ASYNC`: Hook supports asynchronous execution.
    *   `!STOP`: Injected rule can halt the entire pipeline (e.g., a security rejector).

**Extensibility Matrix Structure:**
When this facet is active, the PDM highlights the flow between macro-phases and the micro-hooks that connect them.

| Macro Phase | Hook Name `[H]` | Input Contract | Output Contract | Side-Effect Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Acquisition** | `pre_scan` | `PathString` | `FilteredPath` | `!PURE` |
| **Tokenization** | `post_scan` | `RawItems` | `TokenizedItems` | `!STOP` |

**Conflict Resolution Strategy:**
Define how multiple rules for the same hook are handled:
*   **Pipeline (Default):** Rules run sequentially `Rule1 → Rule2 → Rule3`.
*   **Parallel:** Rules run independently, results are merged.
*   **FirstMatch:** First rule to return a result wins.
