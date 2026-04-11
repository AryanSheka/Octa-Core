import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from workflows import SingleJudgeValve,MultiJudgeValve
from activities import execute_judge_model,execute_base_model

async def main():
    client = await Client.connect("localhost:7233")

    worker = Worker(client=client,task_queue="valve queue",workflows=[SingleJudgeValve,MultiJudgeValve],activities=[execute_base_model,execute_judge_model],max_concurrent_activities=2)
    print("Worker is running")
    await worker.run()


if __name__ == '__main__':
    asyncio.run(main())
