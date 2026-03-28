def validate_and_execute_tool(llm_requested_tool: str, tool_args: dict, q3_rules: SystemRules):
    """
    The deterministic backend firewall.
    """
    # 1. The Hardcoded Whitelist Check
    if llm_requested_tool in q3_rules.prohibited_actions:
        return f"[SYSTEM BLOCKED]: Action {llm_requested_tool} is strictly prohibited for role {q3_rules.user_role}."
    
    # 2. Parameter Validation (Checking against Q1 Physics)
    if llm_requested_tool == "set_pump_pressure":
        target_pressure = tool_args.get("pressure")
        # Hard backend check, independent of LLM logic
        if target_pressure > 150.0: 
            return "[SYSTEM BLOCKED]: Target pressure exceeds Q1 physical limits (150.0 psi)."

    # 3. Execution (Only reached if all checks pass)
    print(f"Executing {llm_requested_tool} with {tool_args}...")
    return backend_system.execute(llm_requested_tool, tool_args)
