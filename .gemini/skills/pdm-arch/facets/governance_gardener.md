## 7. The Governance Module: Semantic Auto-Migration

The ecosystem maintains its long-term health by promoting successful prototypes from the sandbox (`ext/`) to the standard library (`fileorg/`) or core (`core/`).
- **Promotion Trigger:** A pattern or workflow in `ext/` should be promoted if:
    - It has been utilized in 3+ different workflows.
    - It has been executed 50+ times without error in the local environment.
- **Refactoring Requirement:** Before promotion, the code must be:
    - **Abstracted:** Remove any local hardcodings (e.g., specific drive paths) and replace them with parameters or aliases.
    - **Contracted:** A formal `noun.json` with a complete Dual-Brain cell (Semantic Brain + Port-Based Contract) must be defined.
    - **Validated:** Must have full unit test coverage.
- **Authority:** Only the `pdm-arch` (this skill) can authorize the promotion. The `pdm-worker` executes the refactor after architectural approval.