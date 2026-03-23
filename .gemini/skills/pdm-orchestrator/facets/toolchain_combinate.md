### 3. Materialization Phase (The Automation CLI)
- **Rule:** Do NOT manually write Python glue code or use AST surgery.
- **Action:** Use the `wire-workflow` tool in `combinate.py` to automate the implementation.
- **Command Template:**
    `python3 combinate.py plugin wire-workflow <name> --chain "@namespace.noun.verb | @namespace.noun.verb" --domain ext`
- **Default Namespace:** Always target the `ext` domain for new workflows.

## Core Rules
- **No IL Trap:** Do not write logic in JSON. JSON is for contracts; Python is for execution.
- **Non-Invasive:** Do not modify the pure Dido code in `core/` or `fileorg/`. Use the `ext/` workspace for all compositions.
- **Context Efficiency:** Load only the `ai_ontology` section during the initial discovery phase to prevent context rot.