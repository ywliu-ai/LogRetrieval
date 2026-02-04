import agent
from rag import Analyzer
from crewai import Crew, Process, Task
from crewai.flow.flow import Flow, listen, start, router
from agent import QueryRewriterAgent, DataRetrievalEngineerAgent, DataRetrievalExecutorAgent, DataRetrievalAnalyzer
from task import QueryRewriteTask, DataRetrievalTask, DataAnalysisTask
from model import CustomLLM
import os

from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

#TEST_QUERY_1 = "张三2025年10月1日登录了几次邮件？"
#TEST_QUERY_2 = "IP是203.96.238.136在哪些账号上使用过？"
#TEST_QUERY_3 = "IP是203.96.238.136的子网IP在哪些账号上使用过？"

api_key = os.environ.get("OPENAI_API_KEY", "")
model_name = os.environ.get("OPENAI_MODEL_NAME", "")
endpoint = os.environ.get("OPENAI_ENDPOINT", "")
llm = CustomLLM(api_key=api_key, model=model_name, endpoint=endpoint)

class MainFlowState(BaseModel):
    userInput: str = Field("", description="The user input for the flow")


class MainFlow(Flow[MainFlowState]):
    def __init__(self):
        super().__init__(tracing=True)

    @start()
    def QueryRewrite(self):
        analyzer = Analyzer()
        self.extra_information = analyzer.analyze(self.state.userInput)
        self.extra_information = {"所需要的日志可能包含在index_name中": "email_user_action_2026*"}
        agent = QueryRewriterAgent(llm=llm)
        rewrite_task = QueryRewriteTask(
            user_question=self.state.userInput,
            extra_information=self.extra_information,
            agent=agent  # Writer leads, but can delegate research to researcher
        )
        crew = Crew(
            agents=[agent],
            tasks=[rewrite_task],
            process=Process.sequential,
            verbose=True
        )
        result = crew.kickoff()
        return result.raw
    
    @listen("QueryRewrite")
    def DataRetrieval(self, RewriteQuery):
        Executor = DataRetrievalExecutorAgent(llm=llm) 
        result = Executor.kickoff(RewriteQuery)
        return result

    @listen("DataRetrieval")
    def DataRetrievalEngineer(self, ExecutorResult):
        Analyzer = DataRetrievalAnalyzer(llm=llm)
        retrieval_task = DataAnalysisTask(
            retrieval_result=ExecutorResult,
            agent=Analyzer  # Writer leads, but can delegate research to researcher
        )
        crew = Crew(
            agents=[Analyzer],
            tasks=[retrieval_task],
            process=Process.sequential,
            verbose=True
        )
        result = crew.kickoff()
        return result.raw
        result = Engineer.kickoff(ExecutorResult)
        return result



def main():
    state = {
        "userInput": "提取114.232.203.231在2026年1月27日在邮件系统中的行为日志"
    }
    flow = MainFlow()
    result = flow.kickoff(state)
    print(result)

if __name__ == "__main__":
    main()