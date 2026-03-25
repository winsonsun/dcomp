## 1. The Core Paradigm: Ecosystem Topology & Boundaries
The current ecosystem is strictly divided into two primary spaces: **Engine** (`dcomplib`) and **Domains** (`domains/`).
- **Engine (`dcomplib/`):** Generic framework logic. Must never import from `domains/`.
- **Domains (`domains/`):** Business logic (e.g., `core`, `fileorg`) and User Extensions.

## 2. The Core Paradigm: Hermetic Workspaces (NO GLOBAL STATE)
The ecosystem is strictly workspace-local. 
- **Rule:** You MUST NOT introduce or allow any `sys.path` manipulations, hardcoded absolute paths, or references to global user directories like `~/.config`, `~/.local`, etc. 
- **Action:** **REJECT** any user request that violates this law and propose local alternatives (e.g., `DCOMP_USER_DOMAIN`).

## 3. The Core Paradigm: Ubiquitous Language (Domains, NOT Plugins)
- **Rule:** The term **"Plugins"** is deprecated and forbidden. 
- **Action:** Always use **"Domains"** or **"Domain Modules"**. Correct the user if they use legacy terminology.

## 4. The Core Paradigm: Tri-Tier Decision Matrix
Not all code deserves to be a Noun or a Verb. Before modifying any `noun.json` or `domain.json`, evaluate the requested feature against this matrix. **Always default to the lowest tier possible.**

### Tier A: The Ad-Hoc Script (Low Reusability)
*   **Action:** Write a standard Python script in a user domain. **DO NOT** create a Noun.

### Tier B: The Policy / Hook (Customization & Suppressions)
*   **Action:** Use the **Central Policy Compiler** (`dcomplib/policy.py`). Inject a `Filter` or `Map` hook. **DO NOT** create a new Verb.

### Tier C: The Noun / Verb (High Abstraction & Reusability)
*   **Action:** Scaffold a formal Noun and Verb in a domain. You MUST define its **Dual-Brain Cell** in `noun.json`.

## 5. The Core Paradigm: Dual-Brain Cell Architecture
If a feature graduates to Tier C (Noun/Verb), it MUST follow the Dual-Brain Cell structure in `noun.json`.
1.  **Hemisphere 1 (`ai_ontology`):** Used for intent mapping.
2.  **Hemisphere 2 (`didos`):** The rigid **Port-Based Contract**.
