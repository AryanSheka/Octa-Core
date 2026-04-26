from dotenv import load_dotenv
load_dotenv()

from temporalio import activity
import os
from google import genai
from shared import JudgeOutput, ModelConfig, LLMResponse
import ollama

@activity.defn
async def execute_base_model(model:ModelConfig ,chat_history:list[dict]) -> str:
    try:
        if(model.model_group=='gemini'):
            client = genai.Client(
                api_key=os.environ.get("GEMINI_API_KEY")
            )

            response = client.models.generate_content(
                model = model.model_name,
                contents = chat_history,
            )

            return response.text
        elif(model.model_group =='ollama'):
            ollama_client = ollama.AsyncClient()
            ollama_messages=[]
            for msg in chat_history:
                raw_text = msg["parts"][0]["text"]
                ollama_messages.append({"role": msg["role"], "content": raw_text})
            response = await ollama_client.chat(
            model=model.model_name, 
            messages=ollama_messages)
            return response.message.content
        
    except Exception as e:
        raise ValueError(f"Base model has failed with error {str(e)}")
    


@activity.defn
async def execute_judge_model(model:ModelConfig,prompt:str)->JudgeOutput:
    try:
        if(model.model_group=='gemini'):
            gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
            response = gemini_client.models.generate_content(
                model = model.model_name,
                contents = prompt,
                config= {"response_mime_type":"application/json","response_schema":LLMResponse}
            )
            judge_response = response.parsed
            final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
            return final_output

        elif(model.model_group == 'ollama'):
            ollama_messages = [{"role":"user","content":prompt}]
            ollama_client = ollama.AsyncClient()
            response = await ollama_client.chat(
                model=model.model_name,
                messages=ollama_messages,
                format=LLMResponse.model_json_schema()
            )
            judge_response = LLMResponse.model_validate_json(response.message.content)
            final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
            return final_output
        
    except Exception as e:
        raise ValueError(f"Judge has failed with error {str(e)}")
        
