# Facet 5: The Topological View (The "Where")

*   **Answers:** Where does this data physically rest, or over what network boundaries does it travel?
*   **Focus:** Physical infrastructure, network topology, storage tiers, and data gravity.
*   **Use Case:** Optimizing I/O bottlenecks, designing distributed systems, planning hardware infrastructure, and auditing data residency or security boundaries.

**DSL Elements (Location Annotations & Data Gravity Indicators):**
These annotations bind the logical data entities and their operations to physical hardware or network locations, making the cost of `[I] Ingest` and `[D] Distribute` operations explicitly clear.

*   **Location Annotations (`@Location`):** Appended either to the Data Entity (Row Header) to denote where the data rests, or directly to an Operation Cell to denote where the compute/transfer is happening.
    *   `@RAM` / `@Memory`: Data exists only in volatile memory.
    *   `@LocalDisk` / `@NVMe`: Data rests on fast, local block storage.
    *   `@NAS` / `@Network_SMB`: Data rests on remote, slow, or shared network storage.
    *   `@Cloud_S3` / `@AWS`: Data rests in a cloud object store.
*   **Data Gravity Indicators (`→` Transfers):** When an operation forces data to cross a topological boundary, you can denote the transfer explicitly.
    *   *Example:* `[D] → @NAS` (Distributing a local cache over the network to a NAS).
    *   *Example:* `[I] ← @Cloud_S3` (Ingesting a remote manifest down to local memory).