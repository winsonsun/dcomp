## Core Glossary
Strict compliance with this terminology is mandatory.

### Physical Namespaces
*   **Engine:** The abstract framework and routing libraries (`dcomplib`).
*   **Domains:** Application-specific logic (`domains/`).
    *   `domains/core`: System interactions.
    *   `domains/fileorg`: Official business logic.
*   **User Domains:** Workspace-local extensions (`domains/USER_DOMAIN`). Replaces "Plugins".

### System Entities
*   **Resource:** A domain module (e.g., `file`, `scene`, `job`).
*   **Capability:** An actionable transformation or query attached to a Resource (e.g., `scan`, `prune`).
*   **Workflow:** A pipeline of capabilities defined in `domain.json`.
*   **Policy:** A cross-cutting hook in `dcomplib/policy.py`.

### Contract (contract.json)
Interface definitions for Resources:
*   `ai_ontology`: Intent and use-case metadata.
*   `capabilities`: Structural Port-Based Contract (`shape`, `Stream[Type]`).

### Forbidden Terms (REJECT THESE)
*   "Plugins" (Use "Domains").
*   Global Configs (No `~/.config` or `~/.dcomplib`).
*   Biological metaphors (No "Cell", "Receptor", "Hemisphere").
