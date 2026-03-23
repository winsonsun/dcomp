### Phantom Workflow Simulation (AOT Validation)
Before moving to the Materialization Phase, you MUST perform a **Phantom Simulation** of the proposed PDM pipeline.
- **Simulation**: Map a small "slice" of sample data or mock data through the conceptual PDM chain.
- **Logic Validation**: Verify if the data transformations and output match the user's ultimate business goal and the `ai_ontology` intent.
- **Self-Correction**: If the phantom simulation reveals a logical flaw (e.g., incorrect filter or missing metadata step), do NOT proceed to materialization. You MUST log a "Constraint Node" documenting this logical flaw to the `system.evolution_log`. Then, return to the Recursive Design Loop and use the simulation failure as a design iteration to refine the chain.

### Verification Phase
- Confirm the AOT compiler successfully generated the intended code (if applicable to the toolchain).
- Trigger the `pdm` skill to draw the matrix of the newly created workflow to verify its structural integrity to the user.