from pydantic import BaseModel, Field
from typing import Optional, Literal


class ModelConfig(BaseModel):
    model_name : str = Field(description="The specific id of the model to be used. Example 'gemini-2.5-flash' ")
    model_prompt : str = Field(description="The prompt for the model")
    model_group : Literal["gemini","ollama"] = Field(description="The provider group of the model. Example gemini, ollama ")
    weight : float = Field(description="Relative weight of the model when computing. Only valid when the model is a judge model. Higher value increases its influence when computing acceptance",default=1,ge=0)

class SingleJudgeInput(BaseModel):
    base_model : ModelConfig = Field(description="The base model which will generate the answer")
    judge_model : ModelConfig = Field(description="The judge model which will judge the answer")
    max_tries : int= Field(description="The maximum number of retries before the valve opens",default=5,ge=1)

class MultiJudgeInput(BaseModel):
    base_model : ModelConfig = Field(description="The base model which will generate the answer")
    judge_panel : list[ModelConfig] = Field(description="A list of judge models that will generate an output",min_length=1)
    max_tries : int= Field(description="The maximum number of retries before the valve opens",default=5,ge=1)
    acceptability : float = Field(description="A number between 0 and 1 that represents the ratio of (number of accepting/ Total number of judges), for which the valve will open",ge=0,le=1,default=0.75)


class JudgeOutput(BaseModel):
    is_valid : bool
    feedback : Optional[str]= "" 
    weight : float
    llm_name : str

class LLMResponse(BaseModel):
    is_valid : bool
    feedback : Optional[str]= ""
