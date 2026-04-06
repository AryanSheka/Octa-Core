import asyncio
from temporalio.client import Client
from temporalio.worker import Worker
from workflows import Model
from shared import ModelInput

async def main():

    judge_model = 'gemini-3-flash-preview'
    base_model = 'gemini-2.5-flash'
    base_model_prompt = "Imagine a 3x3 grid. In the first row, the cells are [Red, Blue, Red]. In the second row, the cells are [Blue, Red, Blue]. Now, apply a 90-degree clockwise rotation to the grid, then flip it horizontally. Finally, replace every Red cell with its 'complementary' color (Green) and every Blue cell with its 'complementary' color (Orange). What is the final color of the cell in the middle-left position (Row 2, Column 1)?"

    judge_prompt ="""System Role: You are a Spatial Logic Auditor. Your job is to verify the accuracy of 3x3 grid transformations.

 Task: Analyze the provided response for the following specific logic chain:
 1. Initial Grid:     
    [R, B, R]
    [B, R, B]
    [R, B, R]
 2. 90° Clockwise Rotation: Does the model correctly map the new coordinates? 
 3. Horizontal Flip: Does the model correctly mirror the grid across the Y-axis?
 4. Color Swap: Does it correctly swap Red -> Green and Blue -> Orange?

 Constraint: Specifically check the cell at Row 2, Column 1. 
 * After rotation, it should be the original (1,1) cell.
 * After the horizontal flip, it should be the original (1,3) cell.
 * If the final color at (2,1) is not green, the logic is flawed.

 
 Output (JSON):
 Return a JSON object with:
 is_valid: (true/false)
 feedback: (A prompt for the generator to fix its specific error.Point out exactly why the ai is wrong and where it should rectify the answer)
 
 Output to check : 
 """

    Data = ModelInput(base_model=base_model,base_model_prompt=base_model_prompt,judge_model_prompt=judge_prompt,judge_model=judge_model,max_tries=5)

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