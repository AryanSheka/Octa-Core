from temporalio import workflow
from datetime import timedelta
import asyncio

from shared import JudgeInput, JudgeOutput

with workflow.unsafe.imports_passed_through():
    from activities import OrchestrationActivities
    
@workflow.defn
class JudgeValve:
    @workflow.run
    async def run(self,data:JudgeInput)->str:
        max_try = data.max_tries
        current_try = 1
        chat_history = [{"role":"user","parts":[{"text":data.base_model.model_prompt}]}]
        response=""
        while(current_try<=max_try):
            workflow.logger.info(f"Try Number {current_try}")
            response = await workflow.execute_activity(OrchestrationActivities.execute_base_model,args=[data.base_model,chat_history],start_to_close_timeout=timedelta(seconds=600))
            

            judge_set = []

            for judge in data.judge_panel:
                formatted_judge_input = f"{judge.model_prompt}\n\n Original Prompt given to AI :\n {data.base_model.model_prompt}\n\n AI Output to Grade:\n{response}"
                judge_set.append(workflow.execute_activity(OrchestrationActivities.execute_judge_model,args=[judge,formatted_judge_input],start_to_close_timeout=timedelta(seconds=600)))

            
            workflow.logger.info("Executing Judge Panel parallely")
            results: list[JudgeOutput] = await asyncio.gather(*judge_set)
            
            total_weight_of_accepted_judges = 0
            total_judge_weight = sum(judge.weight for judge in data.judge_panel)

            consolidated_feedback = ""

            for result in results:
                if(result.is_valid):
                    total_weight_of_accepted_judges+=result.weight
                else:
                    consolidated_feedback += f"\n\n {result.llm_name} rejected your output with the result {result.feedback}"

            if total_weight_of_accepted_judges/total_judge_weight >= data.acceptability:
                workflow.logger.info(f"Valve opened at try number {current_try}")
                return response    
            
            else:
                current_try+=1
                chat_history.append({"role":"model","parts":[{"text":response}]})
                chat_history.append({"role":"user","parts":[{"text":consolidated_feedback}]})

        return f"Maximum tries crossed. Valve Opened. Final output : \n\n {response}" # open valve after crossing max tries