from pydantic import BaseModel
from typing import Optional, Literal


class ModelConfig(BaseModel):
    model_name : str
    model_prompt : str
    model_group : Literal["gemini","ollama"]

class ModelInput(BaseModel):
    base_model : ModelConfig
    judge_model : ModelConfig
    max_tries : Optional[int]=5

class JudgeOutput(BaseModel):
    is_valid : bool
    feedback : Optional[str]= ""