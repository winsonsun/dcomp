# PDM Core Glossary (Type Definitions)

This facet serves as the single source of truth for the terminology and physical boundaries of the Dcomp ecosystem. **Do not redefine these terms in other facets.**

## 1. Physical Namespaces (The Topology)
- **`core` (The Kernel):** Low-level system interactions (AST, IO, CLI framework). Protected domain. Only modified to change the fundamental laws of physics. Located at `dcomp/core/`.
- **`fileorg` (The Standard Library):** Highly stable, official business logic and approved domain nouns. Protected domain. Located at `dcomp/fileorg/`.
- **`ext` (The Sandbox):** The primary user workspace. The default entry point for 99% of all new development, feature prototyping, and workflow composition. Isolated to prevent core regression. Located at `dcomp/ext/`.

## 2. Ecosystem Entities
- **Noun:** A discrete module representing a domain concept (e.g., `file`, `scene`, `job`). Resides in a namespace directory (e.g., `dcomp/fileorg/file/`).
- **Verb:** An actionable transformation or query attached to a Noun (e.g., `scan`, `prune`, `detect`). Usually an independent python file or function within a Noun's module.
- **Workflow:** An end-to-end data pipeline composing multiple Nouns and Verbs, usually configured in a `domain.json` file.
- **Policy:** A cross-cutting hook or override used to alter pipeline behavior without modifying core source code (e.g., skipping hidden files). Handled by `dcomp/policy.py`.

## 3. The Dual-Brain Cell (Contracts)
Every Tier C (Highly Abstract) Noun must possess a `noun.json` file containing two hemispheres:
- **`ai_ontology` (The Semantic Brain):** Contains the `domain_intent`, `primary_use_case`, `anti_patterns`, and `edge_case_guidance`. Used for intent mapping during discovery.
- **`didos` (The Structural Engine):** The rigid **Port-Based Contract**. It defines the `shape` (Source, Pipe, Sink) and explicit I/O `Stream[Type]` signatures. Used to mathematically prove a pipeline chain is valid.
