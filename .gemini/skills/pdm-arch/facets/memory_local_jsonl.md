## 4. The State/Memory Interface: Centralized Architectural Ontology

To prevent "Verb-Drift" and "Environmental Mismatches", you MUST NOT invent ad-hoc strings for the `architectural_fit` array in a Noun's Dual-Brain cell.

### The Project Cache (The Truth Source)
*   **The Single Source of Truth:** All styles discovered or used in this specific project are stored in the project-local cache: `.gemini/pdm_arch_ontology.jsonl`.
*   **Discovery:** If you are unsure which tag to use, first read or grep `.gemini/pdm_arch_ontology.jsonl`. If a foundational style is used but missing from the cache, you MUST "materialize" it into the `.jsonl` file as a new node.
*   **Custom Styles:** If a project-specific constraint arises that isn't covered by the foundation, you may create a new style node in the local `.jsonl` after explaining the architectural reasoning.