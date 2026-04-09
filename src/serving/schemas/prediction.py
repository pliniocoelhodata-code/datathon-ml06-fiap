from pydantic import BaseModel

class PredictionInput(BaseModel):
    ticker: str
    data: list[list[float]]