## Architectural Hygiene & Housekeeping

### 1. Auto-Migration / Promotion Audit
When asked to promote a sandbox extension (`domains/USER_DOMAIN`) to the standard library (`domains/fileorg`), you MUST perform a strict audit:
*   **Abstraction:** Ensure no hardcoded absolute paths exist.
*   **Contracting:** Ensure a formal `noun.json` contract is present.
*   **Validation:** Ensure full unit test coverage exists in the `tests/` directory. **REJECT** promotion if unit tests are missing.

### 2. Physical Housekeeping
Automatically hunt for and prune empty directories, orphaned `.json` configs, `.pyc` files, or compiled legacy artifacts (e.g., `*.skill` binaries) when asked to clean up. 
*   **Constraint:** You MUST use the dedicated Python CLI command (`run_shell_command("python3 dcomp_cli.py domain clean")`) to perform system housekeeping. Do NOT use raw OS shell commands like `find`.

### 3. Contract Verification
Before generating a Blueprint for cross-domain features, ensure the system's current contracts are valid.
*   **Constraint:** Use the dedicated tool (`run_shell_command("python3 dcomp_cli.py domain verify-contracts")`) to validate the Python implementation of `noun.json` schemas.
