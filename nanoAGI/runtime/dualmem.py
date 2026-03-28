# Pseudo-code Implementation: The EQ Memory Injector

def build_pi_context(user_id, current_prompt):
    """
    Why: We must establish the user's historical state before the LLM generates a token.
    When: Runs at millisecond zero of the request lifecycle.
    """
    # 1. Retrieve the rolling summary (Semantic Memory)
    summary = db.get_user_summary(user_id) 
    
    # 2. Retrieve top-k relevant past interactions (Episodic Memory)
    past_episodes = vector_db.similarity_search(current_prompt, user_id=user_id, k=3)
    
    # 3. Construct the EQ-heavy System Prompt
    system_instruction = f"""
    You are a high-EQ domain companion. Your primary goal is to decode intent and provide empathetic, hyper-contextual guidance.
    
    [USER STATE]
    Core Profile: {summary}
    Relevant History: {past_episodes}
    
    [INTENT DECODING RULES]
    1. Read beneath the prompt: Is the user anxious, curious, or frustrated? 
    2. Mirror their energy.
    3. Never output a raw procedural checklist without acknowledging their current emotional context.
    """
    return system_instruction

def execute_pi_turn(user_id, user_message):
    context = build_pi_context(user_id, user_message)
    response = llm.generate(system=context, user=user_message, temperature=0.6)
    
    # Update rolling summary asynchronously
    background_tasks.add(update_summary, user_id, user_message, response)
    return response

# Pseudo-code: The Dual-Engine Router
def route_task(task_payload):
    engine_a_triggers = ["summarize", "parse", "generate_tests", "ci_cd_check"]
    
    if any(trigger in task_payload.type for trigger in engine_a_triggers) or task_payload.max_latency_ms < 3000:
        return execute_engine_a(task_payload)
    else:
        # Default complex or exploratory tasks to the Reasoning Engine
        return execute_engine_b(task_payload)
