# Pseudo-code Implementation: The Self-Doubt Filter

from pydantic import BaseModel, Field

class MetacognitiveScore(BaseModel):
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    logical_flaws: list[str] = Field(description="List of assumptions made without data.")
    needs_clarification: bool = Field(description="True if the user's prompt is too ambiguous to answer safely.")
    internal_critique: str

def metacognitive_evaluator_node(state: AgentState):
    """
    Why: To force the AI to audit its own draft before the user sees it.
    When: Runs immediately after a 'Worker' node generates a draft.
    """
    draft_response = state["draft_output"]
    original_prompt = state["user_prompt"]
    
    evaluation_prompt = f"""
    You are an adversarial cognitive auditor. Review this draft response against the user prompt.
    Prompt: {original_prompt}
    Draft: {draft_response}
    
    Scoring Rules:
    - If the draft hallucinates facts or violates physical/system constraints, score < 0.5.
    - If the draft assumes missing variables, list them in 'logical_flaws' and score < 0.7.
    - If the draft is logically sound and strictly factual, score > 0.8.
    """
    
    # 1. Generate the critique using a structured output parser
    critique = strict_llm.generate_structured(evaluation_prompt, response_format=MetacognitiveScore)
    
    # 2. The Decision Matrix (The "Doubt" Trigger)
    if critique.needs_clarification or critique.confidence_score < 0.7:
        # Route to a fallback: Ask the user for the missing variables
        fallback_msg = f"Before I proceed, I need to verify: {', '.join(critique.logical_flaws)}."
        return {"final_output": fallback_msg, "status": "clarification_needed"}
    
    # If confidence is high, pass the draft through
    return {"final_output": draft_response, "status": "approved"}
