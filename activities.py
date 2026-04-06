from dotenv import load_dotenv
load_dotenv()

from temporalio import activity
import os
from google import genai
from google.genai import types
from shared import JudgeOutput

@activity.defn
async def execute_base_model(model_name:str ,chat_history:list[dict]) -> str:
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY")
    )

    response = client.models.generate_content(
        model = model_name,
        contents = chat_history,
    )

    return response.text


@activity.defn
async def execute_judge_model(model_name:str,prompt:str)->JudgeOutput:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model = model_name,
        contents = prompt,
        config= {"response_mime_type":"application/json","response_schema":JudgeOutput}
    )
    return response.parsed
