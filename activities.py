from dotenv import load_dotenv
from temporalio import activity
import os
from google import genai
from shared import JudgeOutput, ModelConfig, LLMResponse
import ollama


class OrchestrationActivities:
    def __init__(self):
        load_dotenv()
        self.ollama_client = ollama.AsyncClient()
        self.gemini_client = None
        if(os.environ.get("GEMINI_API_KEY")):
            self.gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


    @activity.defn
    async def execute_base_model(self,model:ModelConfig ,chat_history:list[dict]) -> str:
        try:
            if(model.model_group=='gemini'):
                response = self.gemini_client.models.generate_content(
                    model = model.model_name,
                    contents = chat_history,
                )

                return response.text
            elif(model.model_group =='ollama'):
                ollama_messages=[]
                for msg in chat_history:
                    raw_text = msg["parts"][0]["text"]
                    ollama_messages.append({"role": msg["role"], "content": raw_text})
                response = await self.ollama_client.chat(
                model=model.model_name, 
                messages=ollama_messages)
                return response.message.content
            
        except Exception as e:
            raise ValueError(f"Base model has failed with error {str(e)}")
        


    @activity.defn
    async def execute_judge_model(self,model:ModelConfig,prompt:str)->JudgeOutput:
        try:
            if(model.model_group=='gemini'):
                response = self.gemini_client.models.generate_content(
                    model = model.model_name,
                    contents = prompt,
                    config= {"response_mime_type":"application/json","response_schema":LLMResponse}
                )
                judge_response = response.parsed
                final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
                return final_output

            elif(model.model_group == 'ollama'):
                ollama_messages = [{"role":"user","content":prompt}]
                response = await self.ollama_client.chat(
                    model=model.model_name,
                    messages=ollama_messages,
                    format=LLMResponse.model_json_schema()
                )
                judge_response = LLMResponse.model_validate_json(response.message.content)
                final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
                return final_output
            
        except Exception as e:
            raise ValueError(f"Judge has failed with error {str(e)}")
        
