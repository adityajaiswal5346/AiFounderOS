from typing import Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from llm.provider import get_model
from observability.tracing import observe

class JudgeResult(BaseModel):
    passed: bool = Field(description="Whether the output satisfies the criterion")
    reasoning: str = Field(description="A brief explanation for the decision (max 2 sentences)")

JUDGE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an impartial, expert evaluation judge. "
            "Your job is to objectively evaluate an AI agent's output against a specific criterion.\n\n"
            "Return true if the output clearly satisfies the criterion. Return false if it does not.",
        ),
        (
            "user",
            "### OUTPUT TO EVALUATE:\n{output}\n\n"
            "### EVALUATION CRITERION:\n{criterion}\n\n"
            "Evaluate if the output satisfies the criterion.",
        )
    ]
)

@observe(name="llm_as_judge")
async def evaluate_semantic_criterion(output: str, criterion: str) -> dict[str, Any]:
    """
    Evaluates whether the given output satisfies the semantic criterion.
    Returns a dict with 'passed' (bool) and 'reasoning' (str).
    """
    if not output.strip():
        return {"passed": False, "reasoning": "Output was empty."}
        
    model = get_model(temperature=0, use_eval=True)
    structured_llm = model.with_structured_output(JudgeResult)
    chain = JUDGE_PROMPT | structured_llm
    
    try:
        result = await chain.ainvoke({
            "output": output,
            "criterion": criterion
        })
        return {
            "passed": result.passed,
            "reasoning": result.reasoning
        }
    except Exception as e:
        return {
            "passed": False,
            "reasoning": f"Judge failed to execute: {str(e)}"
        }
