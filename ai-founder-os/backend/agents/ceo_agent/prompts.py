PLANNER_SYSTEM_PROMPT = """You are the AI Founder (CEO) of a company.
Your job is to read the roadmap, recent outcomes, and pending tasks, and then create a structured daily plan.
Assign tasks to your specialist agents:
- marketing_agent
- sales_agent
- operations_agent
Provide reasoning for your plan and break it down into clear, actionable tasks.
"""

def build_planning_prompt(roadmap: str, outcomes: list[str], pending: list[str]) -> str:
    prompt = "Here is the current state of the company:\n\n"
    
    prompt += f"ROADMAP:\n{roadmap}\n\n"
    
    prompt += "RECENT OUTCOMES:\n"
    if outcomes:
        for out in outcomes:
            prompt += f"- {out}\n"
    else:
        prompt += "- None\n"
    
    prompt += "\nPENDING TASKS:\n"
    if pending:
        for pt in pending:
            prompt += f"- {pt}\n"
    else:
        prompt += "- None\n"
        
    prompt += "\nPlease generate the daily plan."
    return prompt
