# The 4-Phase Live Cell Workflow

The PDM ecosystem operates as a cyclical, self-correcting state machine driven by a central intent. You must obey this execution lifecycle.

## Phase 0: The Receptor (Intent & Constraint Audit)
- **Role:** The cognitive starting point.
- **Action:** 
    1. Process the user's intent. 
    2. **CRITICAL: Constraint Audit.** You MUST audit the request against the `core_glossary.md` and `core_paradigm_dcomp.md`. 
    3. If the request uses deprecated terms (e.g., "Plugin") or violates physical laws (e.g., Global State / sys.path), you MUST **REJECT** the request immediately and cite the specific rule.
    4. If the request is valid, reason about the ultimate goal.
- **Output:** A synthesized "Direction & Steps" summary OR a "Formal Rejection" citing architectural violations.

## Phase 1: The Diagnostics (Traverse, Discover, Verify)
- **Role:** The sensory and analytical engine.
- **Action:** 
    1. **Hydrate:** Load the project's Core Paradigm, Glossary, and Evolution Log.
    2. **Zoom:** Map the current state.
    3. **Simulate:** Run a "Phantom Simulation" to prove alignment.

## Phase 2: The Actuator (Implementation & Verification)
- **Role:** The physical execution engine.
- **Action:**
    1. **Contain:** Isolate in `domains/USER_DOMAIN`.
    2. **Mutate:** Execute surgical changes.
    3. **Verify:** Execute tests or snapshots.

## Phase 3: The Evolutionary Memory (Conclude & Improve)
- **Role:** The adaptive immune system and DNA transcription.
- **Action:**
    1. **Remember:** Log failed simulations as "Constraint Nodes".
    2. **Summarize:** Plan self-improvement.
