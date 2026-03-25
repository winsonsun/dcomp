# PDM Core Glossary (Type Definitions)

This facet serves as the single source of truth for the terminology and physical boundaries of the Dcomp ecosystem. **Do not redefine these terms in other facets. Enforce these terms strictly and reject deprecated terminology.**

## 1. Physical Namespaces (The Topology)
- **Engine / Framework:** Refers to the abstract primitives and libraries. **Canonical term:** `dcomplib`.
- **`domains` (Business Logic):** The application-specific functionality. Located at `domains/`.
    - **`domains/core` (The Kernel):** Low-level system interactions (AST, IO, CLI framework). Protected domain.
    - **`domains/fileorg` (The Standard Library):** Official business logic and approved domain nouns. Protected domain.
- **`domains/USER_DOMAIN` (Extensions):** The primary user workspace. Replaces the deprecated `ext` system. Isolated to prevent engine regression.

## 2. Ecosystem Entities
- **Noun:** A discrete module representing a domain concept (e.g., `file`, `scene`, `job`). Resides in a domain directory (e.g., `domains/fileorg/file/`).
- **Verb:** An actionable transformation or query attached to a Noun (e.g., `scan`, `prune`, `detect`). Usually an independent python file or function within a Noun's module.
- **Workflow:** An end-to-end data pipeline composing multiple Nouns and Verbs, usually configured in a `domain.json` file.
- **Policy:** A cross-cutting hook or override used to alter pipeline behavior without modifying core source code (e.g., skipping hidden files). Handled by `dcomplib/policy.py`.

## 3. The Dual-Brain Cell (Contracts)
Every Tier C (Highly Abstract) Noun must possess a `noun.json` file containing:
- **`ai_ontology` (The Semantic Brain):** Contains intent mapping during discovery.
- **`didos` (The Structural Engine):** The rigid **Port-Based Contract**.

## 4. Forbidden / Deprecated Terminology (REJECT THESE)
- **"Plugins":** **DEPRECATED.** Always use **"Domains"** or **"Domain Modules"**. If the user asks for a plugin, correct them and use the `combinate domain` tool.
- **Global Configs (`~/.config`, `~/.dcomplib`):** **FORBIDDEN.** The ecosystem must remain workspace-local (Hermetic). Reject any request to inject global path dependencies.
