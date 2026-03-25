# Dcomp/PDM Ecosystem Glossary

This document outlines the acceptable terminology for the ecosystem. When auditing documentation or code, enforce these semantics.

## Acceptable Terms
- **Engine / Framework:** Refers to the abstract primitives and libraries. **Canonical term:** `dcomplib`
- **Business Logic / Application Logic:** Refers to the concrete implementations built on top of the engine. **Canonical term:** `domains` (e.g., `domains/fileorg`, `domains/core`).
- **Extensions:** Refers to workspace-local dynamic additions. **Canonical term:** `domains` (or User Domains via `DCOMP_USER_DOMAIN`).
- **CLI Commands:** The action words executed by the CLI. **Canonical term:** `verbs` (e.g., `detect`, `sync`).
- **CLI Entities:** The entities acted upon by the CLI. **Canonical term:** `nouns` (e.g., `scene`, `job`).

## Unacceptable Terms
- **Plugins:** *Deprecated.* Use `domains` instead. The command `combinate plugin` has been renamed to `combinate domain`.
- **Global Configs:** *Deprecated.* The ecosystem should not rely on `~/.config` or `~/.dcomplib`. Instead, configuration is workspace-local or injected via the environment.