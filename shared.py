from pydantic import BaseModel
from typing import Optional

class ModelInput(BaseModel):
    base_model : str
    base_model_prompt : str
    judge_model : str
    judge_model_prompt  : str
    max_tries : Optional[int]=5

class JudgeOutput(BaseModel):
    is_valid : bool
    feedback : Optional[str]= ""

