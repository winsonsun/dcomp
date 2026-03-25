# Implementation Plan: State-Aware Agent Runtime (Dynamic Prompt Injection)

## Objective
Evolve the static "Layered Capability" system into a dynamic "State-Aware Runtime." This architecture will optimize context usage and focus by dynamically injecting only the necessary behavioral capabilities based on the current phase of the development lifecycle (PLAN vs. ACT).

## Background & Motivation
As the system grows, a single monolithic `SKILL.md` creates "Context Tax" (wasted tokens) and "Attention Dilution" (distracting the LLM with irrelevant rules). By switching to a phase-based injection model, we ensure the agent has "Super-Resolution" focus on the task at hand.

## Proposed Architecture

### 1. Lifecycle Phases
The runtime will recognize two primary operational states:
*   **PLAN Phase (Design & Orchestration):** Focused on research, contract verification, and Blueprint generation.
*   **ACT Phase (Implementation & Validation):** Focused on surgical code changes, combinator logic, and test execution.

### 2. The "Blueprint" Trigger
The existence and state of a file in `.gemini/blueprints/TASK_NAME.md` acts as the state transition mechanism:
*   **No Blueprint:** Default to **PLAN** phase.
*   **Blueprint Present:** Transition to **ACT** phase and inject the Blueprint's content directly into the system instructions.

## Implementation Strategy

### Phase 1: Configuration Schema Update
Update `prompt_src/config/skills.json` to map capabilities to lifecycle phases:
```json
"phases": {
  "PLAN": ["orchestration", "hygiene"],
  "ACT": ["implementation", "validation"]
}
```

### Phase 2: Dynamic Compiler (The "Injector")
Refactor `scripts/compile_skills.py` (or create a new `runtime/injector.py`) to:
1.  **Detect State:** Check for active blueprints in `.gemini/blueprints/`.
2.  **Resolve Capabilities:** Dynamically select the `capabilities` array based on the detected phase.
3.  **Context Assembly:** 
    *   Inject `foundational` layer (Always).
    *   Inject the `persona` (Always).
    *   Inject the Phase-specific `capabilities`.
    *   If in **ACT** phase, inject the **Blueprint content** as a "High-Priority Directive."

### Phase 3: Integration with Agent Wrapper
Integrate the injector into the main agent loop (or the tool-call sequence) to ensure the system prompt is re-evaluated and refreshed whenever a state transition occurs.

## Key Benefits
*   **Token Efficiency:** Reduces the system prompt size by ~30-50% per turn.
*   **Increased Reliability:** Prevents the "Coder" from being distracted by orchestration rules and vice versa.
*   **Deterministic Handoffs:** Formalizes the Architect -> Coder transition through a physical file trigger.

## Next Steps
*   This plan is currently **On-Hold** until the `prompt_src` context weight exceeds the efficiency threshold.
*   Implementation will require a "Runtime" script that can be called by the LLM or the orchestration tool to refresh the environment.
