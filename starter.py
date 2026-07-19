import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import JudgeValve
from shared import ModelConfig,JudgeInput

async def main():


    base_model_name = 'gpt-5.4-mini'
    base_model_prompt = """ Base Model Prompt """

    judge_model_1_name = 'gemini-2.5-flash-lite' 
    judge_model_1_prompt = """ Judge 1 Prompt"""
    
    judge_model_2_name = 'claude-sonnet-4-6'
    judge_model_2_prompt = """ Judge 2 Prompt"""

    judge_model_3_name = 'qwen3.5:9b' #examples. Can be filled with any other model id from any other model family
    judge_model_3_prompt= """ Judge 3 Prompt"""

    base_model=ModelConfig(model_name=base_model_name,model_prompt=base_model_prompt,model_group='openai')
    
    judge_models=[
        ModelConfig(model_name=judge_model_1_name,model_prompt=judge_model_1_prompt,model_group='gemini'),
        ModelConfig(model_name=judge_model_2_name,model_prompt=judge_model_2_prompt,model_group='anthropic'),
         ModelConfig(model_name=judge_model_3_name,model_prompt=judge_model_3_prompt,model_group='ollama')
        ]

    base_model=ModelConfig(model_name=base_model_name,model_prompt=base_model_prompt,model_group='openai')

    Data = JudgeInput(base_model=base_model,judge_panel=judge_models,max_tries=3,acceptability=0.75)

    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        JudgeValve.run,
        Data,
        id="ai-project-run-1",
        task_queue="valve queue",
    )
    print(f"Started workflow. ID: {handle.id}")

    result = await handle.result()
    print(f"{result}")


if __name__ == "__main__":
    asyncio.run(main())