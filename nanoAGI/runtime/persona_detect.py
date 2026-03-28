# Pseudo-code Implementation: The Deterministic DAG

from typing import TypedDict

# Define the global state passing through the graph
class AgentState(TypedDict):
    user_prompt: str
    cognitive_tier: int  # 1, 2, 3, or 4
    final_output: str

# --- NODE 1: The Semantic Router ---
def router_node(state: AgentState):
    """
    Why: Isolates classification logic to save tokens and ensure accuracy.
    When: The very first step. Determines the execution path.
    """
    prompt = f"""Analyze the input: "{state['user_prompt']}"
    Determine domain familiarity. Output ONLY an integer 1, 2, 3, or 4.
    1: Layperson (No jargon)
    2: Operator (Standard procedures)
    3: Expert (Deep technical data)
    4: Architect (Systems thinking/Adversarial)"""
    
    tier = fast_llm.predict(prompt) 
    return {"cognitive_tier": int(tier)}

# --- CONDITIONAL EDGE ---
def route_to_worker(state: AgentState):
    """
    Why: The deterministic physical switch. Prevents LLM routing hallucinations.
    When: Immediately after Router classification.
    """
    if state["cognitive_tier"] == 1: return "worker_level_1"
    elif state["cognitive_tier"] == 2: return "worker_level_2"
    elif state["cognitive_tier"] == 3: return "worker_level_3"
    elif state["cognitive_tier"] == 4: return "worker_level_4"

# --- NODE 2: The Isolated Workers (Example: Tier 4) ---
def worker_level_4_node(state: AgentState):
    """
    Why: Executes with hyper-specific, isolated constraints.
    When: Only triggered if the Router confirms an Architect-level request.
    """
    system_prompt = """You are a Level 4 Architect. 
    Constraint 1: Unrestricted jargon. 
    Constraint 2: Operate probabilistically. 
    Constraint 3: Attack the assumptions in the user's prompt."""
    
    response = robust_llm.generate(system=system_prompt, user=state['user_prompt'])
    return {"final_output": response}

# --- COMPILE THE DAG ---
workflow = StateGraph(AgentState)

workflow.add_node("router", router_node)
workflow.add_node("worker_level_1", worker_level_1_node)
workflow.add_node("worker_level_2", worker_level_2_node)
workflow.add_node("worker_level_3", worker_level_3_node)
workflow.add_node("worker_level_4", worker_level_4_node)

# Set the flow
workflow.set_entry_point("router")
workflow.add_conditional_edges("router", route_to_worker)

# Execute
app = workflow.compile()
final_state = app.invoke({"user_prompt": "Calculate the xenon poisoning reactivity margin."})
print(final_state["final_output"]) # Will deterministically route to worker_level_3 or 4.