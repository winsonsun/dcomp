# Dcomp/PDM Architecture Guidelines

Welcome to the architectural guidelines for the `sceneLib` Dcomp ecosystem. This document codifies the core design principles and industry best practices that govern how we build, structure, and name components within this project.

By following these conventions, we ensure our codebase remains scalable, predictable, and aligned with modern software engineering standards.

---

## 1. The Noun-Verb CLI Design Pattern

The Dcomp CLI (`dcomp_cli.py`) strictly adheres to the **Noun-Verb (Resource-Oriented) Pattern**. This is the industry standard for complex CLI tools like `git`, `kubectl`, `docker`, and `gcloud`. 

Rather than focusing on the action being performed (e.g., `npm install`), we group actions by the **Resource (Noun)** they affect.

### The Structure: `[app] [noun] [verb] [arguments]`
*   **Example:** `dcomp_cli.py scene detect --scene-size-limit 300`
*   **Example:** `dcomp_cli.py job manage --name backup`

### Naming Best Practices for the CLI
1.  **Nouns are Resources (Topics):**
    *   A Noun should represent a specific domain entity (e.g., `scene`, `job`, `file`, `path`). 
    *   *Plural vs. Singular:* Stick to singular nouns for resources where possible (e.g., `scene detect`, not `scenes detect`) to read more like natural language ("detect this scene").
2.  **Verbs are Actions:**
    *   Use a consistent set of standardized verbs across all nouns (e.g., `query`, `detect`, `manage`, `list`, `prune`).
    *   *Kebab-Case:* If a verb requires multiple words, use kebab-case (e.g., `add-verb`, `compile-workflows`). Never use underscores or CamelCase in CLI commands.
3.  **The "Sentence" Rule:** 
    *   A command should read like a natural language sentence: 
        *   **Subject:** `scene`
        *   **Action:** `detect`
        *   **Adjectives (Flags):** `--override-owner`

---

## 2. Domain-Driven Folder Structure (Microkernel & Onion Architecture)

The project separates the underlying engine from the business logic using a hybrid of **Microkernel (Plugin) Architecture** and **Domain-Driven Design (Onion Architecture)**.

### The Engine (`dcomplib/`)
This folder contains the **Framework**. It is completely abstract and unaware of specific business use cases. 
*   **Responsibilities:** CLI routing (`registry.py`), pure functional combinators (`combinators.py`), I/O utilities, and abstract base classes (`contracts.py`).
*   **Rule (Dependency Inversion):** Files in `dcomplib/` must **never** import from the `domains/` folder. The engine must remain a generic foundation.

### The Business Logic (`domains/`)
This folder contains the actual application functionality grouped by **Bounded Contexts** (e.g., `core`, `fileorg`). These contexts are loaded dynamically as "domain plugins."
*   **Responsibilities:** Defining specific Nouns (like `scenes` or `jobs`), their associated Verbs (like `detect` or `sync`), and domain-specific rules.

### Folder Structure for a Domain Noun
Inside a domain (e.g., `domains/fileorg/scene/`), you should follow the Ports & Adapters pattern:
*   `noun.py`: The **Presentation Layer** (Port). This file should *only* handle `argparse` definitions, CLI flags, output formatting (`print`), and delegating to the application layer.
*   `analyzer.py` / `logic.py`: The **Application/Domain Layer** (Adapter). This file contains pure business logic and Combinator classes. It should return data structures, not print them.
*   `noun.json`: The **Semantic Contract**. Defines the DIDO (Data In, Data Out) schema and expected behavior for the AOT compiler.

---

## 3. Strict Workspace Isolation (Hermetic Execution)

A core tenet of this architecture is **Hermetic Workspaces**. The project must be fully deterministic and self-contained. 

### The Anti-Pattern to Avoid: Global State
We actively ban the dynamic injection of global paths (e.g., `sys.path.insert(0, "~/.config/...")`). A project should never rely on hidden files on a specific developer's machine to run correctly.

### The Best Practice: Local Domains & `DCOMP_USER_DOMAIN`
All domain extensions are managed locally. 
1.  **Built-in Domains:** The engine automatically scans and loads `domains/core` and `domains/fileorg` from the repository root.
2.  **Custom / Temporary Domains:** If you need to scaffold a new domain or load a private extension, put it inside the workspace `domains/` folder (e.g., `domains/my_custom_domain`). 
3.  **Environment Activation:** To load custom domains, use the explicit environment variable:
    ```bash
    DCOMP_USER_DOMAIN="my_custom_domain;another_domain" python3 dcomp_cli.py --help
    ```
    This explicitly declares external dependencies at runtime, ensuring complete reproducibility across different machines and CI/CD pipelines.

---

## 4. Ruthless Pruning and Signal-to-Noise Ratio

*   **The Boy Scout Rule:** Code is read far more often than it is written. If you see deprecated artifacts, empty folders (like legacy `nouns/` or `ext/` folders), or unused binary files (`*.skill`), **delete them**.
*   **No Ghost Artifacts:** Do not leave commented-out blocks of old architecture "just in case." Rely on Git history for that. A clean repository reduces cognitive load for new developers.

*Follow these guidelines when adding new features, running the `combinate.py` meta-programmer, or reviewing pull requests.*