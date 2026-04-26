from pydantic import BaseModel
from typing import List

class PredictionInput(BaseModel):
    ticker: str
    data: list[list[float]]

class AgentInput(BaseModel):
    query: str

class AgentResponse(BaseModel):
    answer: str
    contexts: List[str]
