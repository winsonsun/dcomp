# Pseudo-code Implementation: The ReAct State Machine

def react_loop(user_prompt, tools, max_iterations=5):
    """
    Why: Forces the model to evaluate reality before speaking.
    When: Triggers when a user requires data/actions outside the LLM's parametric memory.
    """
    system_prompt = f"""
    You are an autonomous diagnostic agent. You have access to the following tools: {tools}.
    You MUST format your execution strictly as follows:
    Thought: Evaluate the situation and decide what to do next.
    Action: The exact tool name to use.
    Action Input: The JSON arguments for the tool.
    ... (Wait for Observation) ...
    Final Answer: Your concluding response to the user.
    """
    
    history = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    
    for i in range(max_iterations):
        # 1. Generate Thought & Action
        response = llm.generate(history, stop_sequence=["Observation:"])
        history.append({"role": "assistant", "content": response})
        
        # 2. Parse out the Final Answer (Exit Condition)
        if "Final Answer:" in response:
            return extract_final_answer(response)
            
        # 3. Parse and Execute the Tool
        action_name, action_input = parse_action(response)
        
        try:
            observation = execute_tool(action_name, action_input)
        except Exception as e:
            # Handle chaotic inputs (Instinct Level)
            observation = f"Tool failed with error: {e}. Adjust your approach."
            
        # 4. Inject Observation back into context
        history.append({"role": "user", "content": f"Observation: {observation}"})
        
    return "Error: Reached maximum cognitive iterations without a resolution."
