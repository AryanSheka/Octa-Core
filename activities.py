from dotenv import load_dotenv
from temporalio import activity
import os
from google import genai
from shared import JudgeOutput, ModelConfig, LLMResponse
from temporalio.exceptions import ApplicationError
from google.genai import errors
import ollama
import anthropic
import openai
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from abc import ABC,abstractmethod


class ModelProvider(ABC):
    @abstractmethod
    async def base_model(self,model:ModelConfig ,chat_history:list[dict]) -> str:
        pass

    @abstractmethod
    async def judge_model(self,model:ModelConfig,prompt:str)->JudgeOutput:
        pass


class GeminiProvider(ModelProvider):
    def __init__(self):
        load_dotenv()
        api_key =os.environ.get("GEMINI_API_KEY")
        if(api_key):
            self._gemini_client = genai.Client(api_key=api_key)
        else:
            raise ApplicationError(f"GEMINI_API_KEY Missing from environment",non_retryable=True)

    async def base_model(self, model:ModelConfig, chat_history:list[dict])->str:
        try:
            response = await self._gemini_client.aio.models.generate_content(
                            model = model.model_name,
                            contents = chat_history,
                        )

            return response.text
        
        except errors.APIError as e:
            self._raise_if_fatal(e)

    async def judge_model(self, model:ModelConfig, prompt:str)->JudgeOutput:
        try:
            response = await self._gemini_client.aio.models.generate_content(
                        model = model.model_name,
                        contents = prompt,
                        config= {"response_mime_type":"application/json","response_schema":LLMResponse}
                    )
            judge_response = response.parsed
            final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
            return final_output
        
        except errors.APIError as e:
            self._raise_if_fatal(e)


    @staticmethod
    def _raise_if_fatal(e:errors.APIError):
        if e.code in (400,401,403,404,429):
            raise ApplicationError(f"The Gemini Client has failed with error. Details: {str(e)}", non_retryable=True)
        
        raise e


class OllamaProvider(ModelProvider):
    def __init__(self):
        self._ollama_client = ollama.AsyncClient()

    async def base_model(self, model:ModelConfig, chat_history:list[dict])->str:
        ollama_messages=[]
        for msg in chat_history:
            raw_text = msg["parts"][0]["text"]
            ollama_messages.append({"role": msg["role"], "content": raw_text})
        try:
            response = await self._ollama_client.chat(
            model=model.model_name, 
            messages=ollama_messages)
            return response.message.content
        
        except ollama.ResponseError as e:
            self._raise_if_fatal(e)

    async def judge_model(self, model:ModelConfig, prompt:str)->JudgeOutput:
        try:
            ollama_messages = [{"role":"user","content":prompt}]
            response = await self._ollama_client.chat(
                        model=model.model_name,
                        messages=ollama_messages,
                        format=LLMResponse.model_json_schema()
                    )
            judge_response = LLMResponse.model_validate_json(response.message.content)
            final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=judge_response.is_valid,feedback=judge_response.feedback)
            return final_output
        
        except ollama.ResponseError as e:
            self._raise_if_fatal(e)


    @staticmethod
    def _raise_if_fatal(e:ollama.ResponseError):
        if e.status_code == 404:
            raise ApplicationError(f"Ollama client has failed with error {e}",non_retryable=True)
        raise e
    

class AnthropicProvider(ModelProvider):
    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ApplicationError("ANTHROPIC_API_KEY missing from environment", non_retryable=True)
        else:
            self._anthropic_client = AsyncAnthropic(api_key=api_key)

    async def base_model(self, model:ModelConfig, chat_history:list[dict])->str:
        anthropic_messages = []
        for msg in chat_history:
            raw_text=msg["parts"][0]["text"]
            role = ""
            if msg["role"]=="model":
                role = "assistant"
            else:
                role = msg["role"]
            
            anthropic_messages.append({"role":role,"content":raw_text})

        try:
            response = await self._anthropic_client.messages.create(
                model=model.model_name,
                max_tokens=4096,
                messages=anthropic_messages
            )
            return response.content[0].text
        
        except anthropic.APIStatusError as e:
            self._raise_if_fatal(e)

        
    async def judge_model(self, model:ModelConfig, prompt:str)->JudgeOutput:
        anthropic_messages=[{"role":"user","content":prompt}]
        try:
            response = await self._anthropic_client.messages.parse(
                model=model.model_name,
                max_tokens=4096,
                messages=anthropic_messages,
                output_format=LLMResponse
            )
            parsed_response = response.parsed_output
            final_output= JudgeOutput(weight = model.weight,llm_name=model.model_name,is_valid=parsed_response.is_valid,feedback=parsed_response.feedback)
            return final_output
        
        except anthropic.APIStatusError as e:
            self._raise_if_fatal(e)
        
    @staticmethod
    def _raise_if_fatal(e:anthropic.APIStatusError):
        if e.status_code in (400,401,402,403,404):
            raise ApplicationError(f"Anthropic client failed with error: {e}",non_retryable=True)
        raise e

        
class OpenaiProvider(ModelProvider):
    def __init__(self):
        load_dotenv()
        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key:
            raise ApplicationError("OPEN_AI_API_KEY is missing from environment",non_retryable=True)
        else:
            self._openai_client = AsyncOpenAI(api_key=api_key)
            
    async def base_model(self, model:ModelConfig, chat_history:list[dict])->str:
        openai_messages = []
        for msg in chat_history:
            raw_text=msg["parts"][0]["text"]
            role = ""
            if msg["role"]=="model":
                role = "assistant"
            else:
                role = msg["role"]
            openai_messages.append({"role":role,"content":raw_text})
        
        try:
            response = await self._openai_client.responses.create(
                model = model.model_name,
                input=openai_messages)
            return response.output_text

        except openai.APIError as e:
            self._raise_if_fatal(e)

    async def judge_model(self, model:ModelConfig, prompt:str)->JudgeOutput:
        openai_messages =[{"role":"user","content":prompt}]
        try:
            responses = await self._openai_client.responses.parse(
                model=model.model_name,
                input=openai_messages,
                text_format=LLMResponse
            )
            parsed_response = responses.output_parsed
            final_output = JudgeOutput(weight=model.weight,llm_name=model.model_name,is_valid=parsed_response.is_valid,feedback=parsed_response.feedback)
            return final_output
        
        except openai.APIError as e:
            self._raise_if_fatal(e)




    @staticmethod
    def _raise_if_fatal(e: openai.APIError):
        if e.status_code in (401, 403, 429):
            raise ApplicationError(f"OpenAI client failed with error: {e}", non_retryable=True)
        raise e


Providers: dict[str, type[ModelProvider]] = {
    "gemini" : GeminiProvider,
    "ollama" : OllamaProvider,
    "anthropic":AnthropicProvider,
    "openai":OpenaiProvider
}


class OrchestrationActivities:
    def __init__(self):
        self._providers = {}

    def _get_provider(self,model:ModelConfig):
        if model.model_group not in self._providers:
            cls = Providers.get(model.model_group)
            if cls is None:
                raise ApplicationError(f"Unsupported Model Group {model.model_group}",non_retryable = True)
    
            self._providers[model.model_group] = cls()
        return self._providers[model.model_group]

    @activity.defn
    async def execute_base_model(self,model:ModelConfig ,chat_history:list[dict]) -> str:
        provider = self._get_provider(model)

        return await provider.base_model(model=model,chat_history=chat_history)

    @activity.defn
    async def execute_judge_model(self,model:ModelConfig,prompt:str)->JudgeOutput:
       provider = self._get_provider(model=model)

       return await provider.judge_model(model=model,prompt = prompt)