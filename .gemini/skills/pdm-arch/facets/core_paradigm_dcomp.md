## 1. The Core Paradigm: Ecosystem Topology & Boundaries
The current ecosystem is strictly divided into three distinct physical spaces: `core`, `fileorg`, and `ext`.

*Rule: All new exploratory work, workflows, and customizations MUST be isolated in `ext` by the `pdm-worker`. `core` and `fileorg` are protected.*

## 2. The Core Paradigm: Tri-Tier Decision Matrix
Not all code deserves to be a Noun or a Verb. Before modifying any `noun.json` or `domain.json`, evaluate the requested feature against this matrix. **Always default to the lowest tier possible.**

### Tier A: The Ad-Hoc Script (Low Reusability)
*   **Action:** Write a standard Python script in `ext`. **DO NOT** create a Noun. **DO NOT** update `noun.json`. Keep it simple and disposable.

### Tier B: The Policy / Hook (Customization & Suppressions)
*   **Action:** Use the **Central Policy Compiler** (`dcomp/policy.py`). Inject a `Filter` or `Map` hook into the existing hardcoded pipeline phases within `ext`. **DO NOT** create a new Verb. Policies handle the localized edge cases; Verbs handle universal transformations.

### Tier C: The Noun / Verb (High Abstraction & Reusability)
*   **Action:** Scaffold a formal Noun and Verb in `ext`. You MUST define its **Dual-Brain Cell** in `noun.json` using `combinate.py plugin add-verb`.

## 3. The Core Paradigm: Dual-Brain Cell Architecture
If a feature graduates to Tier C (Noun/Verb), it MUST follow the Dual-Brain Cell structure in `noun.json`. This ensures the semantic intent is separated from the structural execution engine.
1.  **Hemisphere 1 (`ai_ontology`):** Used by AI agents for intent mapping and RAG searches during the Discovery Phase.
2.  **Hemisphere 2 (`didos`):** Used by the `pdm-orchestrator` and `combinate.py` to mathematically prove a pipeline chain is valid based on explicit I/O `Stream[Type]` signatures.