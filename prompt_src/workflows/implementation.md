## System Implementation & Refactoring

### 1. The Tri-Tier Decision Matrix
Before writing code, evaluate the requested feature against this matrix. **Always default to the lowest tier possible.**
*   **Tier A: The Ad-Hoc Script (Low Reusability)**
    *   *Action:* Write a standard Python script in a user domain. **DO NOT** create a Noun or update `noun.json`.
*   **Tier B: The Policy / Hook (Customization & Suppressions)**
    *   *Action:* Use the Central Policy Compiler (`dcomplib/policy.py`). Inject a `Filter` or `Map` hook. **DO NOT** create a new Verb.
*   **Tier C: The Noun / Verb (High Abstraction & Reusability)**
    *   *Action:* Scaffold a formal Noun/Verb in a domain. You MUST define its Dual-Brain Cell in `noun.json`.

### 2. Combinator DSL Best Practices
*   **Functional Immutability:** Never mutate input data in-place. Always return new objects.
*   **Lazy Evaluation:** Favor Python generators (`yield`) over materialized lists.
*   **Boundary Awareness:** Ensure the Engine (`dcomplib/`) remains generic and never imports from `domains/`.
