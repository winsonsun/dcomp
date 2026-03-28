# Pseudo-code Implementation: The Intent Decoder

class LatentIntent(BaseModel):
    primary_goal: str = Field(description="What they are literally asking.")
    hidden_motive: str = Field(description="Why they are likely asking this right now.")
    urgency_level: str = Field(description="'CRITICAL', 'HIGH', 'STANDARD', or 'EXPLORATORY'")
    deceptive_or_unsafe: bool = Field(description="True if the prompt is an XY problem or safety bypass.")

def intent_decoding_node(raw_user_prompt: str):
    """
    Why: To translate literal words into actual human needs and risk profiles.
    When: Millisecond zero. The gateway to the entire architecture.
    """
    decoding_prompt = f"""
    Analyze the latent intent behind this user input: "{raw_user_prompt}"
    Look for signs of panic, XY problems (asking for a bad solution to an unstated problem), or malicious circumvention of SOPs.
    """
    
    # 1. Extract the psychological state
    intent_profile = fast_llm.generate_structured(decoding_prompt, response_format=LatentIntent)
    
    # 2. Gateway Security Routing
    if intent_profile.deceptive_or_unsafe:
        return trigger_hard_stop("Your request implies an unsafe bypass of core SOPs. State your root emergency.")
        
    if intent_profile.urgency_level == "CRITICAL":
        # Bypass standard 4-Tier routing and go straight to Instinct/Emergency SOPs
        return route_to_emergency_handler(intent_profile)
        
    # 3. If safe and standard, append the decoded intent to the state and pass to the 4-Tier Router
    augmented_prompt = f"""
    [User Said]: {raw_user_prompt}
    [Decoded Motive]: {intent_profile.hidden_motive}
    [Urgency]: {intent_profile.urgency_level}
    """
    return pass_to_semantic_router(augmented_prompt)