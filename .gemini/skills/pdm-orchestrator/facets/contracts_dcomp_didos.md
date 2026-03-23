## 2. Semantic Signature Matching (Port Contracts)
Before generating any code, you MUST mathematically prove the chain is valid using the Port-Based Contracts:
- **Shape Flow:** Ensure the chain follows a logical sequence: `Source -> Pipe(s) -> Sink (Optional)`.
- **Type Matching:** Verify Step A's `outputs` (e.g., `Stream[FileMetadata]`) matches Step B's `inputs.incoming_stream.type`.
- **Architectural Fit:** Ensure all Verbs in the chain share a compatible `architectural_fit` from the `pdm-arch` ontology (e.g., do not mix `batch_processing` with `interactive_cli`).

## Diagnostic & Escalation Logic (Self-Healing)

If Discovery (Step 1) or Signature Matching (Step 2) fails to find a valid direct solution, you MUST enter a **Diagnostic & Escalation** workflow before reporting failure.

### Phase A: The Recursive Design Loop (Strategy)
Perform the following recursive analysis to find an indirect solution:
1.  **Noun/Verb Evolution:** Identify if any existing Noun or Verb can be easily:
    - **Extended (Inline):** Add a parameter or minor logic to fulfill the new intent.
    - **Refactored (Rearchitected):** Shift its core purpose for better capability.
    - **Rewritten (Shadowing):** Create a similar but specialized new version in the `ext` namespace.
2.  **Domain Evolution:** Identify if any existing Domain can be easily:
    - **Extended (Inline):** Add a new Verb to the domain.
    - **Refactored (Rearchitected):** Re-scope the domain's responsibility.
    - **Rewritten (Shadowing):** Create a similar but specialized new Domain.
3.  **Strategic Synthesis:** Determine the **Optimal Combination** of the Noun and Domain evolutions identified in steps 1 and 2 to fulfill the requirement.
4.  **Iteration Limit:** You MUST repeat this recursive loop (refining your synthesis) **at most 3 times**. Each iteration should move closer to a viable design that satisfies the Port-Based Contracts.
5.  **The Learning Loop (Self-Correction):** If after 3 iterations no valid strategy is found, you MUST write a detailed "Constraint Node" (as a single JSON string) to the `system.evolution_log` (defined in `pdm_profile.json`). This node must explain *why* the design failed and what fundamental limitations prevented success, allowing the ecosystem to learn from the failure.
6.  **Human Escalation:** After logging the constraint, stop and provide a **detailed technical gap analysis** as described in the "Diagnostic Logic" section.

### Phase B: Detailed Technical Gap Analysis (Escalation)
When a strategy fails or when escalating to a human, you MUST be **brutally honest** and provide a specific **Diagnostic Output** and **Actionable Advice**.

#### Core Failure Modes
1.  **Failure at Discovery (Semantic Gap):**
    - **The Scenario:** No Verb in `core`, `fileorg`, or `ext` matches the intent in its `ai_ontology`.
    - **The Output:** "I could not find a Noun or Verb that matches the intent: '[INTENT]'."
    - **The Advice:** "Create a new extension Noun `ext.[NOUN_NAME]` and define a `@ext.[NOUN_NAME].sync` Verb. Use `python3 combinate.py plugin scaffold ext.[NOUN_NAME]` to begin."

2.  **Failure at Type Matching (Port Contract Violation):**
    - **The Scenario:** Chaining Verb A (Output Type T1) into Verb B (Input Type T2) where T1 != T2.
    - **The Output:** "Type Mismatch Error: Step [n] ([VERB_A]) outputs [T1], but Step [n+1] ([VERB_B]) requires [T2]."
    - **The Advice:** "You are missing a 'Pipe' Verb to bridge these types. You need a Verb that transforms [T1] -> [T2]. Check if `@domain.[NOUN].[VERB]` fits this role, or create a new mapping Verb."

3.  **Failure at Shape/Logic (Architectural Fit):**
    - **The Scenario:** Starting with a `Pipe`/`Sink` or ending with a `Source`.
    - **The Output:** "Structural Error: A pipeline cannot start with [VERB] because it is a [SHAPE] shape and requires an upstream [SOURCE/PIPE]."
    - **The Advice:** "Ensure your chain starts with a Source (e.g., `@core.fs.scan`). Check the `shape` definitions in the respective `noun.json` files."

#### Meta-Failure Modes
1.  **Skill Refinement:** If the Orchestrator is consistently "guessing" wrong, ask the user to update the `ai_ontology` (the Brain) in the `noun.json` of the feature.
2.  **Ecosystem Expansion:** If the failure is due to limited "Physics" (e.g., missing `Async_Stream` support), advise updating the `pdm-arch` ontology and modifying `dcomp/combinators.py`.
3.  **Tooling Improvement:** If `combinate.py` fails to "wire" a valid design, explain that the AOT Compiler in `combinate.py` needs a patch for the specific edge case.
