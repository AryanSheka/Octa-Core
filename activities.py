from dotenv import load_dotenv
from temporalio import activity
import os
from google import genai
from shared import JudgeOutput, ModelConfig, LLMResponse
from temporalio.exceptions import ApplicationError
from google.genai import errors
import ollama


class OrchestrationActivities:
    def __init__(self):
        self.ollama_client = None
        self.gemini_client = None


    @activity.defn
    async def execute_base_model(self,model:ModelConfig ,chat_history:list[dict]) -> str:
        try:
            if(model.model_group=='gemini'):
                if(self.gemini_client is None):
                    self.initiate_client("gemini")

                try:
                    response = await self.gemini_client.aio.models.generate_content(
                        model = model.model_name,
                        contents = chat_history,
                    )

                    return response.text
                except errors.APIError as e:
                    if e.code in (400,401,403):
                        raise ApplicationError(f"The provided Gemini Api Key is invalid or you lack permissions. Details: {str(e)}", non_retryable=True)
                    
                    raise e

            elif(model.model_group =='ollama'):
                if(self.ollama_client is None):
                    self.initiate_client("ollama")
                ollama_messages=[]
                for msg in chat_history:
                    raw_text = msg["parts"][0]["text"]
                    ollama_messages.append({"role": msg["role"], "content": raw_text})
                response = await self.ollama_client.chat(
                model=model.model_name, 
                messages=ollama_messages)
                return response.message.content
            else:
                raise ApplicationError(f"Unsupported model group: {model.model_group}", non_retryable=True)
        except ApplicationError:
            raise
        except Exception as e:
            raise ValueError(f"Base model has failed with error {str(e)}")
        


    @activity.defn
    async def execute_judge_model(self,model:ModelConfig,prompt:str)->JudgeOutput:
        try:
            if(model.model_group=='gemini'):
                if(self.gemini_client is None):
                    self.initiate_client("gemini")
                try:
                    response = self.gemini_client.models.generate_content(
                        model = model.model_name,
                        contents = prompt,
                        config= {"response_mime_type":"application/json","response_schema":LLMResponse}
                    )
                    judge_response = response.parsed
                    final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
                    return final_output
                except errors.APIError as e:
                    if e.code in (400,401,403):
                        raise ApplicationError(f"The provided Gemini Api Key is invalid or you lack permissions. Details: {str(e)}", non_retryable=True)
                    
                    raise e

            elif(model.model_group == 'ollama'):
                if(self.ollama_client is None):
                    self.initiate_client("ollama")
                ollama_messages = [{"role":"user","content":prompt}]
                response = await self.ollama_client.chat(
                    model=model.model_name,
                    messages=ollama_messages,
                    format=LLMResponse.model_json_schema()
                )
                judge_response = LLMResponse.model_validate_json(response.message.content)
                final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
                return final_output
            
            else:
                raise ApplicationError(f"Unsupported Model group : {model.model_group}",non_retryable=True)
        
        except ApplicationError:
            raise
            
        except Exception as e:
            raise ValueError(f"Judge has failed with error {str(e)}")
        
    def initiate_client(self,model_group:str):
        load_dotenv()
        if(model_group=='gemini'):
            api_key =os.environ.get("GEMINI_API_KEY")
            if(api_key):
                self.gemini_client = genai.Client(api_key=api_key)
            else:
                raise ApplicationError(f"GEMINI_API_KEY Missing from environment",non_retryable=True)
        elif(model_group=='ollama'):
            self.ollama_client = ollama.AsyncClient()