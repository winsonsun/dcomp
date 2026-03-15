# System Nouns Architecture PRD

## Context
The Dcomp scanner currently employs a "Noun-First" CLI architecture where components like `scenes`, `jobs`, `files`, and `paths` manage their own data spaces. With the introduction of the **Central Policy Compiler**, there is a question of whether these core system/internal nouns should be progressively updated to leverage dynamic policy injection, or whether the entire engine should be rewritten as a pure microkernel where *everything* (even core scanning logic) is a plugin.

This document outlines two architectural approaches to managing system-level nouns:

---

## Approach A: The Progressive (Opt-In) Hybrid Model (Current Direction)

**Philosophy**: The core execution path (`scan`, `diff`, `sync`) is sacred, explicit, and hardcoded. System nouns (`files`, `paths`) only participate in dynamic injection when they need to provide cross-cutting, optional features.

### Description
In this model, `scanner/modes.py` explicitly defines the crucial steps of the pipeline (e.g., `FS_Scan -> Map(tokenize) -> BuildTree`). The dynamic Policy Compiler (`scanner.policy.get_rules`) is used as an *extension slot* between these fixed steps. 

Internal nouns are primarily used for their schema definitions, validation logic, and CLI handlers. If an internal noun (e.g., `files`) needs to add a feature like "reject temporary files," it implements the `get_rules(phase='pre_scan')` method to inject a Combinator into the fixed pipeline.

### Pros
* **Performance**: The critical path executes with zero reflection or dynamic registry lookups.
* **Debuggability**: If a path fails to tokenize, developers know exactly where to look (`modes.py`), rather than tracing through a dozen dynamically registered plugins.
* **Safety**: Critical system functions cannot accidentally be unloaded, ordered incorrectly, or overridden by a conflicting plugin.

### Cons
* **Inconsistency**: Developers must learn the distinction between "Core Engine Logic" and "Plugin Logic." 

### Implementation Guide
1. Keep the core pipeline steps (`FS_Scan`, `Map(tokenize)`, `BuildTree`) hardcoded in `modes.py`.
2. Provide explicit extension points (e.g., `pre_scan`, `post_tokenize`) where `policy.get_rules` is queried.
3. System nouns only implement `get_rules()` if they are contributing an optional, cross-cutting feature (like a global file filter or auto-tagger).

---

## Approach B: The Complete Rewrite (Microkernel Model)

**Philosophy**: *Everything* is a plugin. The core `dcomp.py` program is nothing more than an empty message bus and a CLI router.

### Description
In this model, there is no hardcoded pipeline in `modes.py`. The `scan` mode simply queries the Policy Engine: "Give me all steps for the `scan` phase."

System nouns like `fs` (filesystem), `paths` (tokenization), and `database` would all implement `get_rules()`. 
* `fs.py` would inject the `FS_Scan` combinator at priority `0`.
* `filters.py` would inject its `Filter` combinator at priority `10`.
* `paths.py` would inject the `Map(tokenize)` combinator at priority `20`.

### Pros
* **Absolute Purity**: 100% consistent architecture. There is no difference between an internal system noun and a user-provided plugin.
* **Infinite Extensibility**: A user could completely replace the `FS_Scan` combinator with a `Cloud_S3_Scan` combinator simply by unloading the `fs` noun and loading an `s3` noun.

### Cons
* **Complexity & Boilerplate**: You must introduce a robust dependency injection framework and priority sorting mechanism (e.g., "Tokenization MUST happen after Filtering but before Tree Building"). 
* **Fragility**: It becomes much easier to break the core system by accidentally misconfiguring the load order of internal plugins.
* **Overhead**: The system spends significant startup time compiling, sorting, and validating the pipeline.

### Implementation Guide
1. Delete `scanner/modes.py` execution logic.
2. Upgrade `scanner/policy.py` to support strict priority ordering (e.g., `get_rules(phase='scan_pipeline') -> List[Tuple[int, Rule]]`).
3. Rewrite all foundational logic (`FS_Scan`, `BuildTree`) as rules provided by the core internal nouns.
4. Implement a robust topological sort in the Policy Engine to handle dependencies between noun operations.

---

## Conclusion & Recommendation

**Approach A (Progressive/Hybrid)** is strongly recommended for the Dcomp architecture. 

The system relies on high-performance data transformation over large JSON files. Introducing the overhead and fragility of a pure Microkernel (Approach B) to handle simple, predictable operations like `FS_Scan` and `BuildTree` violates the pragmatism of the FP-style/Lisp-style design. 

The Progressive approach maintains the speed and clarity of explicitly composed functional pipelines while still offering seamless, data-driven extensibility via the Central Policy Compiler.
