from dotenv import load_dotenv
load_dotenv()

from temporalio import activity
import os
from google import genai
from shared import JudgeOutput, ModelConfig
import ollama

@activity.defn
async def execute_base_model(model:ModelConfig ,chat_history:list[dict]) -> str:
    if(model.model_group=='gemini'):
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY")
        )

        response = client.models.generate_content(
            model = model.model_name,
            contents = chat_history,
        )

        return response.text
    if(model.model_group =='ollama'):
        ollama_client = ollama.AsyncClient()
        ollama_messages=[]
        for msg in chat_history:
            raw_text = msg["parts"][0]["text"]
            ollama_messages.append({"role": msg["role"], "content": raw_text})
        response = await ollama_client.chat(
        model=model.model_name, 
        messages=ollama_messages,
        think = False)
        return response.message.content
    


@activity.defn
async def execute_judge_model(model:ModelConfig,prompt:str)->JudgeOutput:
    if(model.model_group=='gemini'):
        gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        response = gemini_client.models.generate_content(
            model = model.model_name,
            contents = prompt,
            config= {"response_mime_type":"application/json","response_schema":JudgeOutput}
        )
        return response.parsed
    
