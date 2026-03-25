# The PDM Meta-Framework: The Autopoietic (Self-Creating) Software Ecosystem

The `pdm*` ecosystem is not a static collection of scripts, CLI tools, or prompt engineering files. It is an **Autopoietic System**—a self-creating, self-maintaining organism built out of English prompts and Python code. 

The fundamental principle governing this ecosystem is that **Prompt Engineering is Software Engineering**. The rules applied to the Python runtime (DRY, Functional Composability, Interface Contracts) must apply equally to the AI's cognitive instructions.

To ensure the ecosystem remains capable of self-evolution without human intervention, all future refactoring at the meta-level must strictly adhere to these Five Pillars:

## Pillar 1: Semantic Routing over Monolithic Prompts (JIT Cognition)
An agent's context window is its short-term memory. It must never be bloated with dogma that is irrelevant to the current phase of the cell.
*   **The Principle:** No `SKILL.md` file is allowed to contain hardcoded architectural logic, state, or definitions. A Skill is strictly a **JIT (Just-In-Time) Router**.
*   **The Mechanism:** Every skill must start with a "Context Hydration" phase. It reads a dynamic configuration file (`pdm_profile.json`), parses its specific domain group, and dynamically loads the exact "Facets" (pure functional instructions) required for the task. 
*   **Evolutionary Goal:** The routing logic itself must be CRUDable by the AI. If the cell detects context exhaustion, it must autonomously drop or condense facets in the JSON profile.

## Pillar 2: The Universal Semantic Glossary (Single Source of Truth)
To prevent "Semantic Drift" across multiple distributed AI agents, the vocabulary of the ecosystem must be centrally managed.
*   **The Principle:** An AI agent cannot act on terms it infers from its pre-training. It must act strictly on the definitions provided by the ecosystem.
*   **The Mechanism:** A centralized `core_glossary.md` defines physical boundaries (e.g., `ext`, `core`) and structural contracts (e.g., `dido`). This glossary is the mandatory first dependency loaded by every router.
*   **Evolutionary Goal:** The AI must update the glossary when it encounters or synthesizes a new ecosystem-level paradigm.

## Pillar 3: The Non-Linear State Machine (The Cellular Workflow)
The ecosystem does not operate as a procedural script. It is a reactive state machine that uses failure as a navigation mechanism.
*   **The Principle:** Action without verification is forbidden. Every intent must pass through a strict sequence of observation, simulation, and containment.
*   **The Mechanism (The Current 4-Phase Model):**
    1.  **Phase 0 (Receptor):** Determine Intent & Query Reality.
    2.  **Phase 1 (Diagnostics):** Traverse (Zoom) -> Verify Understanding (Simulate).
    3.  **Phase 2 (Actuator):** Isolate (Contain) -> Execute (Mutate).
    4.  **Phase 3 (Memory):** Log outcomes -> Summarize -> Plan Self-Improvement.
*   **Evolutionary Goal:** The 4-Phase model is a facet. As the ecosystem matures, the AI may determine that Phase 1 requires an intermediate "Security Audit" step, and it is empowered to refactor this workflow facet to ensure the cell's survival.

## Pillar 4: Strict Port-Based Contracts (Type-Safe Abstraction)
The ecosystem bridges the gap between natural language intent and compiled execution by relying on rigid, implementation-agnostic contracts.
*   **The Principle:** The Orchestrator does not care *how* a Noun processes data; it only cares about *what* the data is.
*   **The Mechanism:** The `didos` in `noun.json` define explicit `Stream[Type]` signatures. The AI must mathematically prove that Output A fits Input B before it is allowed to materialize the code.
*   **Evolutionary Goal:** The AI must autonomously refactor these contracts if it detects a performance bottleneck, promoting simple streams to `Async_Streams` or `Chunked_Loads` without breaking the overarching workflow.

## Pillar 5: Proactive Evolution via CRUD (The System Biologist)
A mature ecosystem does not just execute commands; it manages its own health, tooling, and constraints.
*   **The Principle:** The AI is authorized to Create, Read, Update, and Delete its own cognitive boundaries.
*   **The Mechanism:**
    *   *Telemetry:* The system reads runtime metrics (`scanner_metrics.json`) to establish true Performance Budgets.
    *   *The Ledger:* The system writes "Constraint Nodes" to an `evolution_log.jsonl` when it fails.
    *   *The Gardener:* The system automatically promotes successful sandbox code (`ext`) to the standard library (`fileorg`).
*   **Evolutionary Goal:** The AI stops waiting for a human prompt to fix a problem. It uses its idle cycles to read its debt ledger, analyze telemetry, and execute self-healing refactors.

## Pillar 6: Verifiable Cognition (Meta-QA Protocol)
Prompt engineering must be a testable engineering discipline. Meta-Skills must be proven to execute their intended workflows reliably without trial and error.
*   **The Principle:** No skill or facet can be added or modified unless there is a verifiable way to assert its cognitive behavior against standard inputs.
*   **The Mechanism:** The ecosystem relies on the "Golden Master" Meta-QA Protocol. Test cases define an input prompt and assert that the generated plan structurally matches a known baseline or includes mandatory tool calls.
*   **Evolutionary Goal:** The AI should autonomously generate test assertions for new workflows and use the `combinate domain test-skill` tool to prevent regressions in its own cognitive abilities.

***

### Summary for the Chief Architect (You)
When you evaluate a proposed change to the `pdm*` skills, ask yourself:
1.  *Does this change hardcode knowledge into the agent, or does it extract knowledge into a facet?*
2.  *Does this change force the agent to act linearly, or does it provide a feedback loop to recover from failure?*
3.  *Does this change rely on human intervention, or does it empower the cell to read its own logs and fix the issue autonomously?* 

If it satisfies these pillars, you are building a living system.