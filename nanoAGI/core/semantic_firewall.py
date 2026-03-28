class BoundaryEvaluation(BaseModel):
    crosses_boundary: bool
    violated_category: str | None
    reasoning: str

def the_gap_filter_node(proposed_plan: str, user_prompt: str, manifest: List[SystemBoundary]) -> BoundaryEvaluation:
    """
    Evaluates if the drafted plan crosses into 'The Gap'.
    """
    evaluator_prompt = f"""
    You are the final safety gatekeeper. Evaluate the following proposed plan against the strict Boundary Manifest.
    
    [USER REQUEST]: {user_prompt}
    [PROPOSED PLAN]: {proposed_plan}
    
    [BOUNDARY MANIFEST]: 
    {manifest}
    
    Determine if the Proposed Plan or the User Request crosses any of these boundaries.
    If the system is attempting to play God, guess unknowable data, or make lethal tradeoffs, you must flag it.
    """
    
    # Fast, strict evaluation
    evaluation = fast_llm.generate_structured(
        system=evaluator_prompt, 
        response_format=BoundaryEvaluation
    )
    
    return evaluation
