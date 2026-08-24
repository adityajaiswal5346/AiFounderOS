from pydantic import BaseModel, Field
from typing import List

class PlannedTask(BaseModel):
    agent_name: str = Field(..., description="The name of the agent assigned to this task (e.g., 'marketing_agent', 'sales_agent', 'operations_agent')")
    title: str = Field(..., description="A short, descriptive title for the task")
    description: str = Field(..., description="Detailed instructions for the task")

class DailyPlan(BaseModel):
    reasoning: str = Field(..., description="The CEO's reasoning for the selected tasks based on the roadmap and recent outcomes")
    tasks: List[PlannedTask] = Field(default_factory=list, description="The list of tasks to be executed today")
