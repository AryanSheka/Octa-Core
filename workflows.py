from temporalio import workflow
from datetime import timedelta
import asyncio

from shared import SingleJudgeInput, MultiJudgeInput, JudgeOutput

with workflow.unsafe.imports_passed_through():
    from activities import execute_base_model
    from activities import execute_judge_model

@workflow.defn
class SingleJudgeValve:
    @workflow.run
    async def run(self,data:SingleJudgeInput)->str:
        max_try = data.max_tries
        current_try = 1
        chat_history = [{"role":"user","parts":[{"text":data.base_model.model_prompt}]}]
        response=""
        while(current_try<=max_try):
            workflow.logger.info(f"Try Number {current_try}")
            response = await workflow.execute_activity(execute_base_model,args=[data.base_model,chat_history],start_to_close_timeout=timedelta(seconds=600))
            
            formatted_judge_input = f"{data.judge_model.model_prompt}\n\n Original Prompt given to AI :\n {data.base_model.model_prompt}\n\n AI Output to Grade:\n{response}"
            result = await workflow.execute_activity(execute_judge_model,args=[data.judge_model,formatted_judge_input],start_to_close_timeout=timedelta(seconds=600))
            
            if(result.is_valid):
                workflow.logger.info(f"Valve Opened at try {current_try}")
                return response
            
            else:
                current_try+=1
                chat_history.append({"role":"model","parts":[{"text":response}]})
                chat_history.append({"role":"user","parts":[{"text":result.feedback}]})
                if(data.base_model.model_group!= 'ollama' or data.judge_model.model_group != 'ollama'):
                    await workflow.sleep(30) #sleep to avoid crossing token limit in free tier

        return f"Maximum tries crossed. Valve closed. Final output : \n\n {response}"
        
    
@workflow.defn
class MultiJudgeValve:
    @workflow.run
    async def run(self,data:MultiJudgeInput)->str:
        max_try = data.max_tries
        current_try = 1
        chat_history = [{"role":"user","parts":[{"text":data.base_model.model_prompt}]}]
        response=""
        while(current_try<=max_try):
            workflow.logger.info(f"Try Number {current_try}")
            response = await workflow.execute_activity(execute_base_model,args=[data.base_model,chat_history],start_to_close_timeout=timedelta(seconds=600))
            

            judge_set = []

            for judge in data.judge_panel:
                formatted_judge_input = f"{judge.model_prompt}\n\n Original Prompt given to AI :\n {data.base_model.model_prompt}\n\n AI Output to Grade:\n{response}"
                judge_set.append(workflow.execute_activity(execute_judge_model,args=[judge,formatted_judge_input],start_to_close_timeout=timedelta(seconds=600)))

            
            workflow.logger.info("Executing Judge Panel parallely")
            results: list[JudgeOutput] = await asyncio.gather(*judge_set)
            
            total_number_of_judges = len(data.judge_panel)
            number_of_accepted_judges = 0
            consolidated_feedback = ""

            for result in results:
                if(result.is_valid):
                    number_of_accepted_judges+=1
                else:
                    consolidated_feedback += f"\n\n {result.feedback}"

            if number_of_accepted_judges/total_number_of_judges >= data.acceptability:
                workflow.logger.info(f"Valve opened at try number {current_try}")
                return response    
            
            else:
                current_try+=1
                chat_history.append({"role":"model","parts":[{"text":response}]})
                chat_history.append({"role":"user","parts":[{"text":consolidated_feedback}]})
                await workflow.sleep(30) #sleep to avoid crossing token limit in free tier

        return f"Maximum tries crossed. Valve closed. Final output : \n\n {response}" # open valve after crossing max tries