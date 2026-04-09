import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import Model
from shared import ModelInput,ModelConfig

async def main():

    judge_model_name = ''
    base_model_name = ''
    base_model_prompt = """"""

    judge_prompt ="""System Role: You are a Logic Auditor. Your job is to verify the accuracy of ai model. 
     In case the ai model is wrong, you should give a feedback to the model outlining exactly where it went wrong and where it should fix itself. Do not give the answer.
    Just nudge it towards the correct method to get to the answer. Example you went wrong in step x, you should have done xyz.
 Output (JSON):
 Return a JSON object with:
 is_valid: (true/false)
 feedback: (A prompt for the generator to fix its specific error.Point out exactly why the ai is wrong and where it should rectify the answer. Should only be given when ai is wrong)
 """
    base_model=ModelConfig(model_name=base_model_name,model_prompt=base_model_prompt,model_group='')
    judge_model=ModelConfig(model_name=judge_model_name,model_prompt=judge_prompt,model_group='')
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