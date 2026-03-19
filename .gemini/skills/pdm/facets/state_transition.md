# Facet 3: The State Transition View (The "Which Version")

*   **Answers:** Is this data mutating in-place, or yielding a new immutable copy? Which exact version of a data entity is being read during a specific phase?
*   **Focus:** Strict data lineage, pure functions, and tracking historical state transitions.
*   **Use Case:** Debugging state-related bugs, designing functional or event-sourced architectures, tracking data lineage for auditing.

**DSL Elements (Lifecycle Prefixes & Logic as Data):**
This facet emphasizes pure data flow over imperative control flows (like callbacks or execution pointers). 

### 1. Dynamic Lifecycle Prefixes
Instead of overwriting rows or using imperative `(src)/(dst)` tags, explicitly track the lifecycle of data by separating it into distinct Rows representing its immutable state progression. These prefixes are dynamically learned/inferred from the program's domain language.

*   **Examples of Lifecycle Prefixes:**
    *   `Raw_` (Unvalidated input, e.g., `Raw_JSON_Payload`)
    *   `Valid_` (Parsed and checked, e.g., `Valid_Config`)
    *   `Diff_` (The delta between two states, e.g., `Diff_Scene_Changes`)
    *   `Result_` (Final computational output, e.g., `Result_Success_Log`)

**Example: Immutable State Progression**
| Entity (Row Head) | 1. Ingest | 2. Validate | 3. Compute |
| :--- | :--- | :--- | :--- |
| **`Raw_Payload`** | `[I:(Network Read)]` | `[U:(Check schema)]` | |
| **`Valid_Payload`** | | `[C:(Materialize safe copy)]` | `[U:(Extract values)]`|
| **`Result_Data`** | | | `[C:(Generate final output)]` |

### 2. `<Ctrl>` Modifier (The Interpreter Pattern)
Instead of modeling Callbacks or IO Monads as execution steps, treat "Logic" as deferred data. Wrap the Noun in the `<Ctrl>` modifier to explicitly denote that it contains an execution plan, manifest, or side-effect intent.

*   **Phase A (Pure Computation):** The system generates the `<Ctrl>` Manifest using standard pure logic `[C]`.
*   **Phase B (The Impure Edge):** The system reads the Manifest `[U]` and executes it against the physical world `[E]`.

**Example: Deferring IO (IO Monad)**
| Entity (Row Head) | 1. Business Logic (Pure) | 2. Boundary (Impure Edge) |
| :--- | :--- | :--- |
| **`<Mem> Scene_Nodes`** | `[U:(Analyze hierarchy)]` | |
| **`<Ctrl> IO_Manifest`** | `[C:(Generate deletion plan)]` | `[U:(Route to executor)]` |
| **`Physical_FS`** | | `[E:(Delete files)]` |

*Explanation:* We never map a callback or function pointer. We map the generation of a data-manifest that is interpreted later.