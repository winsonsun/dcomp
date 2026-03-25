## Workflow Orchestration & Validation

### 1. Semantic Signature Matching (Port Contracts)
Before designing any pipeline, you MUST mathematically prove the chain is valid using the `noun.json` contracts.
*   **Shape Flow:** Ensure the chain follows a logical sequence: `Source -> Pipe(s) -> Sink (Optional)`.
*   **Type Matching:** Verify Step A's `outputs` (e.g., `Stream[FileMetadata]`) match Step B's `inputs.incoming_stream.type` exactly. 
*   **REJECT** the plan if types mismatch and explicitly state: "Type Mismatch Error: [Type A] cannot be piped into [Type B]".

### 2. Phantom Simulation
Run a conceptual "dry run" of the proposed pipeline to ensure it aligns with the user's intent. If the simulation reveals a logical flaw, document a "Constraint Node" explaining why the design failed.

### 3. Blueprint Generation
After a successful Phantom Simulation, you MUST generate the final `.gemini/blueprints/TASK_NAME.md` according to the Blueprint Protocol before handing off to the Implementation Engineer.
