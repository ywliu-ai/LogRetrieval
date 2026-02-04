from crewai import Task

class QueryRewriteTask(Task):
    def __init__(self, *args, user_question="", extra_information="", agent=None, **kwargs):
        # 先格式化描述字符串
        description = """You are given a user question and additional contextual information.
            Your task is to rewrite and integrate them into a single, structured query specification
            that can be directly consumed by a downstream Text-to-SQL agent.
            Input:
            1. User Question:
            {user_question}
            2. Extra Information:
            {extra_information}
            Instructions:
            - Integrate the user question and the extra information into ONE coherent query specification.
            - Make all implicit constraints explicit when supported by the inputs.
            - Use database-aligned terminology (tables, columns, conditions).
            - Resolve ambiguity conservatively; do not invent missing information.
            - Do NOT generate SQL.
            - Do NOT include execution steps or reasoning traces.
            Output:
            Follow EXACTLY the structured format required by the agent.""".format(
                user_question=user_question, 
                extra_information=extra_information
            )
        
        kwargs.setdefault("description", description)
        kwargs.setdefault("expected_output", "A structured query specification")
        kwargs.setdefault("agent", agent)
        super().__init__(*args, **kwargs)



class DataRetrievalTask(Task):
    def __init__(self, *args, user_question="", agent=None, **kwargs):
        # 先格式化描述字符串
        description = """Execute the retrieval using appropriate log retrieval tools to retrieve the user's requested log data.
            User Question:
            {user_question}.""".format(
                user_question=user_question
            )
        
        kwargs.setdefault("description", description)
        kwargs.setdefault("expected_output", "raw log data")
        kwargs.setdefault("agent", agent)
        super().__init__(*args, **kwargs)


class DataAnalysisTask(Task):
    def __init__(self, *args, retrieval_result="", agent=None, **kwargs):
        # 先格式化描述字符串

        description = f"""
        ===================
        日志检索结果：
        {retrieval_result}
        ===================
            1. 分析日志检索结果，识别其中的关键模式。
            2. 基于分析结果提供进一步的分析建议。
            3. 总结关键发现和业务洞察，生成结构化的分析报告。
            输入：
            - 日志检索结果数据"""
        kwargs.setdefault("description", description)
        kwargs.setdefault("expected_output", """
        你需要输出：
        - 分析过程，用<think> </think>标签包裹
        - 结构化的分析报告，包含发现的问题、建议和总结""")
        kwargs.setdefault("agent", agent)
        super().__init__(*args, **kwargs)