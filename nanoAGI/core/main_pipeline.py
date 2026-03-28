def phase_1_execution_pipeline(user_prompt: str, user_id: str, reactor_id: str):
    """
    The full deterministic lifecycle of a Phase 1 request.
    """
    
    # Step 1: Lock in Reality (Fetch Q1 & Q3)
    q1_state = fetch_q1_state(reactor_id)
    q3_state = fetch_q3_state(user_id, task_context="standard_ops")
    
    # Step 2: Assemble the Skeleton Prompt
    system_prompt = build_deterministic_system_prompt(q1_state, q3_state)
    
    # Step 3: LLM Generation (Strict JSON output required)
    llm_response = strict_llm.generate(
        system=system_prompt,
        user=user_prompt,
        tools=["set_pump_pressure", "read_logs", "adjust_cooling_flow"]
    )
    
    # Step 4: Actuation Governance (If the LLM decides to use a tool)
    if llm_response.requires_tool_call:
        tool_name = llm_response.tool_call.name
        tool_args = llm_response.tool_call.arguments
        
        # Pass through the backend firewall
        execution_result = validate_and_execute_tool(tool_name, tool_args, q3_state)
        
        # Step 5: Final formatting
        return f"Action Result: {execution_result}"
    
    # If no tool is needed, return the strictly bounded text response
    return llm_response.text