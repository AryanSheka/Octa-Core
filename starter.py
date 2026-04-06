import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import Model
from shared import ModelInput,ModelConfig

async def main():

    judge_model_name = 'gemini-3-flash-preview'
    base_model_name = 'qwen3.5:9b'
    base_model_prompt = """Answer the following questions 
    1: A 4x5 grid has the following cells filled: (1,2), (2,4), (3,1), (4,3), (5,2). 
Rotate 270° clockwise, then mirror vertically, then shift every cell 
right by 2 (wrapping around). List all final cell positions.
    2: Start with X=1. Apply these operations in order:
X = X*3+1, X = X//2, X = X*7-3, X = X//4, X = X*2+5, 
X = X//3, X = X*4-7, X = X//2, X = X*5+3, X = X//6
What is the final value of X?
3:I have 5 cards face down. I flip every 2nd card, then every 3rd card, 
then every 4th card. Which cards are face up?"""

    judge_prompt ="""System Role: You are a Logic Auditor. Your job is to verify the accuracy of ai model. 
     In case the ai model is wrong, you should give a feedback to the model outlining exactly where it went wrong and where it should fix itself. Do not give the answer.
    Just nudge it towards the correct method to get to the answer. Example you went wrong in step x, you should have done xyz.
 Output (JSON):
 Return a JSON object with:
 is_valid: (true/false)
 feedback: (A prompt for the generator to fix its specific error.Point out exactly why the ai is wrong and where it should rectify the answer. Should only be given when ai is wrong)
 
 Output to check : 
 """
    base_model=ModelConfig(model_name=base_model_name,model_prompt=base_model_prompt,model_group='ollama')
    judge_model=ModelConfig(model_name=judge_model_name,model_prompt=judge_prompt,model_group='gemini')
    Data = ModelInput(base_model=base_model,judge_model=judge_model,max_tries=5)

    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        Model.run,
        Data,
        id="ai-project-run-1",
        task_queue="valve queue",
    )
    print(f"Started workflow. ID: {handle.id}")

    result = await handle.result()
    print(f"{result}")


if __name__ == "__main__":
    asyncio.run(main())