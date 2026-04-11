import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import MultiJudgeValve
from shared import SingleJudgeInput,ModelConfig,MultiJudgeInput

async def main():


    judge_model_1_name = 'gemini-3-flash-preview'
    judge_model_2_name = 'qwen3.5:9b'
    judge_model_3_name = 'qwen3.5:9b' #examples. Can be filled with any other model id

    base_model_name = 'deepseek-r1:8b'
    base_model_prompt = """"""

    j_1 =""""""
    
    j_2 = """"""

    j_3=""""""
    base_model=ModelConfig(model_name=base_model_name,model_prompt=base_model_prompt,model_group='ollama')
    
    judge_models=[
        ModelConfig(model_name=judge_model_1_name,model_prompt=j_1,model_group='gemini'),
        ModelConfig(model_name=judge_model_2_name,model_prompt=j_2,model_group='ollama'),
        ModelConfig(model_name=judge_model_3_name,model_prompt=j_3,model_group='ollama')
        ]
    

    Data = MultiJudgeInput(base_model=base_model,judge_panel=judge_models,max_tries=5,acceptability=1)

    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        MultiJudgeValve.run,
        Data,
        id="ai-project-run-1",
        task_queue="valve queue",
    )
    print(f"Started workflow. ID: {handle.id}")

    result = await handle.result()
    print(f"{result}")


if __name__ == "__main__":
    asyncio.run(main())