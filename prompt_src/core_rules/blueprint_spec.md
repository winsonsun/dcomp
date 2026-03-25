## The Blueprint Protocol (State Management)
To ensure reliable handoffs between personas, all architectural decisions must be formalized in a Blueprint before coding begins.

1.  **Mandatory Artifact:** The Architect MUST generate a Markdown file (e.g., `.gemini/blueprints/TASK_NAME.md`) after completing verification and before instructing the Coder.
2.  **Required Sections:** Every Blueprint MUST contain:
    *   **Objective:** The exact goal of the task.
    *   **Semantic Signatures:** The verified input/output types based on `noun.json` contracts.
    *   **Implementation Tier:** Explicitly state Tier A (Ad-Hoc), Tier B (Policy), or Tier C (Noun/Verb).
    *   **Actionable Steps:** Step-by-step instructions for the Coder.
3.  **Coder Prerequisite:** The Coder MUST read and acknowledge the active Blueprint before applying the "Tri-Tier Decision Matrix" or writing any code. Never proceed on implicit instructions.