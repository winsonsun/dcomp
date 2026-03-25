# The 4-Phase Live Cell Workflow

The PDM ecosystem operates as a cyclical, self-correcting state machine driven by a central intent. You must obey this execution lifecycle.

## Phase 0: The Receptor (User Intent & Reasoning)
- **Role:** The cognitive starting point.
- **Action:** Process the user's intent. Reason about the ultimate goal. If the request is underspecified, interact with the "external physical world" (e.g., query APIs, check OS constraints, or ask the user for clarification) to fully grasp the intent.
- **Output:** A synthesized "Direction & Steps" summary that dictates what the downstream skills must focus on.

## Phase 1: The Diagnostics (Traverse, Discover, Verify)
- **Role:** The sensory and analytical engine.
- **Action:** 
    1. **Hydrate:** Load the project's Core Paradigm, Glossary, and Evolution Log.
    2. **Zoom (Traverse & Discover):** Map the current state of the codebase using Semantic Zooming. Do not modify anything yet.
    3. **Simulate (Verify):** Run a "Phantom Simulation" (dry-run) against the conceptual mapping to mathematically prove it aligns with Phase 0's intent.
- **Feedback Loop:** If simulation fails, or understanding is blocked, immediately loop back to Phase 0 (to clarify intent) or restart Phase 1 at a different Zoom level.

## Phase 2: The Actuator (Implementation & Verification)
- **Role:** The physical execution engine.
- **Action:**
    1. **Contain:** Isolate the execution context to the Sandbox (`ext/`) or use Behavioral Suppression (Policies).
    2. **Mutate:** Execute the AST surgery, refactoring, or workflow wiring based on the blueprints verified in Phase 1.
    3. **Verify:** Execute physical unit tests or snapshot comparisons to confirm success.
- **Feedback Loop:** If physical implementation fails (e.g., a unit test breaks), loop back to Phase 1 (to simulate a different path) or Phase 0 (if the original reasoning was flawed).

## Phase 3: The Evolutionary Memory (Conclude & Improve)
- **Role:** The adaptive immune system and DNA transcription.
- **Action:**
    1. **Remember:** Regardless of success or failure, log the outcome. Failed simulations must write "Constraint Nodes" to the `evolution_log`.
    2. **Summarize & Plan:** Summarize the architectural taste learned during the task.
    3. **Self-Improve:** If Phase 2 was successful, evaluate the Sandbox code for promotion (Semantic Auto-Migration) to the protected `core/` or `fileorg/`.
- **Feedback Loop:** The self-improvement plan triggers a new Phase 0 intent, keeping the cell in a continuous state of evolution.
