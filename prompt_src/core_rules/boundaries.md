## System Boundaries
Adherence to these rules is validated by the Meta-QA suite.

1.  **Hermetic Workspaces:**
    *   No `sys.path` manipulation.
    *   No hardcoded absolute paths or `~/.` references.
    *   Use `DCOMP_USER_DOMAIN` for local extension discovery.
2.  **Engine Isolation:**
    *   `dcomplib/` must never import from `domains/`.
3.  **Verifiable Cognition:**
    *   All changes must be verified via `combinate domain test-skill`.
