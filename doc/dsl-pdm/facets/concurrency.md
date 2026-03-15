# Facet 6: The Concurrency View (The "How Safely")

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