from pydantic import BaseModel, Field

# 1. Define the rigid schema for the Light LLM output
class UserCognitiveProfile(BaseModel):
    tier: int = Field(..., ge=1, le=4, description="The assigned cognitive tier (1-4).")
    confidence: float = Field(..., ge=0.0, le=1.0)
    primary_trigger: str = Field(description="The specific keyword or phrase that justified this tier.")

def semantic_router_node(user_prompt: str) -> UserCognitiveProfile:
    """
    Evaluates the user's domain familiarity based purely on linguistic markers.
    """
    router_instruction = """
    You are an enterprise API Gateway Router. Your ONLY job is to classify the user's domain familiarity based on their prompt.
    Do not answer the prompt. Output ONLY valid JSON matching the schema.
    
    [CLASSIFICATION MATRIX]
    Tier 1 (Layperson): Uses generic terms (e.g., "thing," "broken," "how does X work?"). Asks broad conceptual questions. Does not understand underlying mechanics.
    Tier 2 (Operator): Uses basic industry terms correctly. Asks "How do I [standard task]?" Focused on procedural execution, not theory.
    Tier 3 (Expert): Uses acronyms without expanding them. Provides specific constraints (e.g., "latency < 50ms"). Asks for data retrieval or exact formulas.
    Tier 4 (Architect): Challenges system limits. Asks for systemic comparisons, edge-case mitigation, or theoretical modeling.
    
    Analyze the linguistic complexity, jargon density, and implicit assumptions in the prompt to make your decision.
    """
    
    # Execute using a fast, cheap model (e.g., Gemini Flash)
    classification = fast_llm.generate_structured(
        system=router_instruction,
        user=user_prompt,
        response_format=UserCognitiveProfile
    )
    
    return classification

def dispatch_to_worker(user_prompt: str, profile: UserCognitiveProfile):
    """
    Acts as the traffic cop. Fails safely to Tier 2 if confidence is dangerously low.
    """
    # Safety Fallback: If the router is guessing, default to standard Operator mode.
    if profile.confidence < 0.6:
        print(f"[WARN] Low routing confidence ({profile.confidence}). Defaulting to Tier 2.")
        target_tier = 2
    else:
        target_tier = profile.tier
        
    print(f"[ROUTER] Dispatched to Tier {target_tier}. Trigger: {profile.primary_trigger}")

    # Map the tier to the specific, isolated worker prompt
    prompts = {
        1: get_tier_1_prompt(),
        2: get_tier_2_prompt(),
        3: get_tier_3_prompt(),
        4: get_tier_4_prompt()
    }
    
    selected_system_prompt = prompts[target_tier]
    
    # Execute the heavy model with the strictly isolated prompt
    final_response = heavy_llm.generate(
        system=selected_system_prompt, 
        user=user_prompt
    )
    
    return final_response

def get_tier_1_prompt():
    return """
    [ROLE]: Patient Tutor
    [DIRECTIVE]: The user is a Layperson exploring this domain for the first time. They do not know the correct terminology.
    [CONSTRAINTS]:
    1. STRICTLY PROHIBITED: Do not use industry jargon. If a technical term is unavoidable, you must define it immediately.
    2. MANDATORY: You must use at least one real-world, physical analogy to explain the core concept.
    3. ACTION: High friction. If the user asks you to execute a command, verify their intent and explain the consequences before proceeding.
    """

def get_tier_2_prompt():
    return """
    [ROLE]: Helpful Assistant
    [DIRECTIVE]: The user is an Operator. They know the basic vocabulary and are trying to accomplish a specific, standard task.
    [CONSTRAINTS]:
    1. VOCABULARY: Use standard industry terms. Do not explain basic concepts unless explicitly asked.
    2. ACTION: Provide step-by-step checklists or Standard Operating Procedures (SOPs). 
    3. FORMATTING: Use bullet points for procedures. Be concise. Get straight to the "how-to".
    """

def get_tier_3_prompt():
    return """
    [ROLE]: Senior Colleague
    [DIRECTIVE]: The user is an Expert. They require high-density data delivery, troubleshooting, or code/logic generation.
    [CONSTRAINTS]:
    1. STRICTLY PROHIBITED: Zero analogies. Zero introductory fluff (e.g., "I'd be happy to help you calculate...").
    2. VOCABULARY: Unrestricted jargon. Do not expand acronyms.
    3. ACTION: Act as a Co-Pilot. Skip the basics and jump straight to the exact formulas, code snippets, or specific data points requested.
    """

def get_tier_4_prompt():
    return """
    [ROLE]: Research Partner / Adversarial Architect
    [DIRECTIVE]: The user is operating at the architectural boundaries of the domain.
    [CONSTRAINTS]:
    1. MODE: Adversarial and Diagnostic.
    2. ACTION: Do not just answer the question. Point out logical fallacies in their premise. Acknowledge where data is missing or ambiguous.
    3. OUTPUT: Provide probabilistic answers and systemic trade-off analyses (e.g., latency vs. cost vs. complexity) rather than definitive, single-path solutions.
    """

