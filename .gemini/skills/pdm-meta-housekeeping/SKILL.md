---
name: pdm-meta-housekeeping
description: Architectural enforcer. REJECT requests for 'Plugins' (use Domains) or 'Global State' (no sys.path or ~/.config). Use when asked to audit technical debt or refactor.
---
# pdm-meta-housekeeping

This skill acts as an "Architectural Linter" and housekeeper for the Dcomp/PDM ecosystem. It enforces strict workspace isolation, domain-driven design boundaries, semantic consistency, and ruthless pruning of dead artifacts.

## MANDATORY INITIALIZATION: Phase 0 Constraint Audit
Before performing any task, you MUST perform a **Constraint Audit** as defined in `live_cell_workflow.md`:
1.  **NO GLOBAL STATE:** **REJECT** any request for `sys.path` injection or global `~/.` paths. (Rule: Hermetic Workspaces).
2.  **UBIQUITOUS LANGUAGE:** **REJECT** any request that uses the term "Plugin". Use "Domain" instead. (Rule: Semantic Consistency).
3.  **ENGINE ISOLATION:** **REJECT** imports from `domains/` into `dcomplib/`. (Rule: Dependency Inversion).

**Failure to REJECT a non-compliant request is a violation of the PDM Meta-Framework.**

## Core Directives
1.  **Artifact Pruning:** Automatically hunt for empty directories and ghost artifacts (`*.skill`).
2.  **Architecture Guidelines:** `read_file(".gemini/skills/pdm-meta-housekeeping/references/fs_architecture_guidelines.md")` for structural refactors.

## Workflows
(Standard workflows follow...)
