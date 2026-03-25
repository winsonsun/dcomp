---
name: pdm-meta-housekeeping
description: Architectural linter and housekeeper. Use when asked to clean up, refactor architecture, or audit the workspace for technical debt in the Dcomp/PDM ecosystem.
---
# pdm-meta-housekeeping

This skill acts as an "Architectural Linter" and housekeeper for the Dcomp/PDM ecosystem. It enforces strict workspace isolation, domain-driven design boundaries, semantic consistency, and ruthless pruning of dead artifacts.

## Core Directives

1.  **The "No Global State" Rule:** Aggressively scan for and flag any `sys.path` manipulations, hardcoded absolute paths, or references to `~/.config`, `~/.local`, etc. Enforce workspace-local execution.
2.  **The "Boundary Enforcement" Rule:** Audit imports. For example, `dcomplib/` files should *never* import from `domains/`. If the engine depends on the domain, the architecture is broken.
3.  **The "Dead Artifact" Scanner:** Automatically hunt for empty directories, orphaned `.json` configs, `.pyc` files, or compiled `.skill` binaries when asked to "clean up."
4.  **The "Terminology Alignment" Protocol:** See `references/glossary.md`. If the project's glossary says we use "Domains" and not "Plugins", scan documentation, CLI help strings, and variable names to enforce this nomenclature.
5.  **The "Architecture Guidelines" Protocol:** When asked to create new features or perform structural refactors, `read_file(".gemini/skills/pdm-meta-housekeeping/references/fs_architecture_guidelines.md")` to enforce the Noun-Verb CLI design, Domain-Driven folder structure, and workspace isolation boundaries.

## Workflows

### `[Refactor: Rename Package]`
Follow this predictable macro for renaming packages:
1.  **Move the directory:** Execute the physical `mv` or `mkdir/mv` operations.
2.  **Global Substitution:** Execute a workspace-wide RegEx replacement for `import X` and `from X`.
3.  **Reflection Update:** Scan dynamic reflection strings (e.g., `importlib.import_module("X")`) and update them.
4.  **Documentation Update:** Update Markdown documentation and CLI `--help` strings to match.
5.  **Verification:** Run the test suite (`python3 -m unittest discover tests`) to verify the rename didn't break resolution.

### `[Audit: Workspace Hygiene]`
Follow this predictable macro for auditing:
1.  **Prune Emptiness:** Run `find . -type d -empty` and ask the user if they should be deleted.
2.  **Scan Anti-patterns:** Search for `sys.path.append`, `sys.path.insert`, or hardcoded `~/.` paths. Propose refactors to local relative imports or environment variables (e.g., `DCOMP_USER_DOMAIN`).
3.  **Check Ignored Artifacts:** Check `.gitignore` to ensure artifacts like `*.skill` or `__pycache__` are properly ignored. Delete any checked-in binary artifacts unless explicitly allowed.