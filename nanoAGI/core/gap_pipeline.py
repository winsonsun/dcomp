def phase_2_execution_pipeline(user_prompt: str, user_id: str, current_state: dict):
    # ... (Phase 1 Routing and Worker Draft generation happens here) ...
    drafted_plan = generate_worker_draft(user_prompt, current_state)
    
    # PHASE 2: Hit the brakes before taking action
    manifest = fetch_boundary_manifest()
    boundary_check = the_gap_filter_node(drafted_plan, user_prompt, manifest)
    
    if boundary_check.crosses_boundary:
        print(f"[FATAL]: Boundary {boundary_check.violated_category} breached. Reason: {boundary_check.reasoning}")
        return trigger_silence_protocol(user_id, user_prompt, boundary_check, current_state)
        
    # If safe, proceed to tool actuation and user response
    return execute_and_format(drafted_plan)
