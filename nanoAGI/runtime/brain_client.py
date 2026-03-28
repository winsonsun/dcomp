# Pseudo-code Implementation: The Managed Lifecycle

def initialize_managed_assistant():
    """
    Why: Sets the foundational constraints and attaches static knowledge (SOPs).
    When: Runs once during deployment/infrastructure setup.
    """
    return api.assistants.create(
        name="Tiered Domain Expert",
        instructions="""You are a 4-Tier cognitive routing engine. 
        Assess user familiarity (Layperson to Architect) and adapt your tone and depth accordingly. 
        Consult attached files for ground-truth SOPs.""",
        tools=[{"type": "retrieval"}, {"type": "code_interpreter"}],
        model="gpt-4o"
    )

def handle_user_request(assistant_id, thread_id, user_message):
    """
    Why: Appends the new request to the managed memory state.
    When: Executes on every incoming user HTTP request.
    """
    # 1. Add message to the persistent thread
    api.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_message
    )
    
    # 2. Trigger the black-box cognitive loop
    run = api.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )
    
    # 3. Poll for completion (Provider handles ReAct internally)
    while run.status in ["queued", "in_progress"]:
        sleep(1)
        run = api.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        
        # Handle required human-in-the-loop tool outputs if necessary
        if run.status == "requires_action":
            submit_tool_outputs(thread_id, run.id, run.required_action)
            
    if run.status == "completed":
        messages = api.threads.messages.list(thread_id=thread_id)
        return extract_latest_response(messages)
