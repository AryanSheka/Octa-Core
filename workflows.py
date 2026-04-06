from temporalio import workflow
from datetime import timedelta
import asyncio
import time

from shared import ModelInput, JudgeOutput

with workflow.unsafe.imports_passed_through():
    from activities import execute_base_model
    from activities import execute_judge_model

@workflow.defn
class Model:
    @workflow.run
    async def run(self,data:ModelInput)->str:
        max_try = data.max_tries
        current_try = 1
        chat_history = [{"role":"user","parts":[{"text":data.base_model_prompt}]}]
        response=""
        while(current_try<=max_try):
            workflow.logger.info(f"Try Number {current_try}")
            response = await workflow.execute_activity(execute_base_model,args=[data.base_model,chat_history],start_to_close_timeout=timedelta(seconds=180))
            
            formatted_judge_input = f"{data.judge_model_prompt}\n\n AI Output to Grade:\n{response}"
            result = await workflow.execute_activity(execute_judge_model,args=[data.judge_model,formatted_judge_input],start_to_close_timeout=timedelta(seconds=180))
            
            if(result.is_valid):
                workflow.logger.info(f"Valve Opened at try {current_try}")
                return response
            
            else:
                current_try+=1
                chat_history.append({"role":"model","parts":[{"text":response}]})
                chat_history.append({"role":"user","parts":[{"text":result.feedback}]})
                await asyncio.sleep(30)

        return f"Maximum tries crossed. Valve closed. Final output : \n\n {response}"
        