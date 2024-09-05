#!/usr/bin/env python
"""展示如何创建一个像Runnable这样的自定义代理执行器的例子。

在编写时，当前的AgentExecutor存在一个错误，
它无法正确传递底层runnable的配置。虽然这个错误应该会被修复，
但这个例子展示了如何创建一个更复杂的自定义runnable。

请参考这里关于自定义代理流的文档：

https://python.langchain.com/docs/modules/agents/how_to/streaming#stream-tokens 

**注意**
为了支持流式传输单个token，你需要手动在LLM上设置streaming=True
并使用stream_log端点而不是stream端点。
"""
from typing import Any, AsyncIterator, Dict, List, Optional, cast

from fastapi import FastAPI
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.pydantic_v1 import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import (
    ConfigurableField,
    ConfigurableFieldSpec,
    Runnable,
    RunnableConfig,
)
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import tool
from langchain_core.utils.function_calling import format_tool_to_openai_function
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from langserve import add_routes

vectorstore = FAISS.from_texts(
    ["猫咪喜欢鱼", "狗狗喜欢棍子"], embedding=OllamaEmbeddings(model="llama3.1")
)
retriever = vectorstore.as_retriever()


@tool
def get_eugene_thoughts(query: str) -> list:
    """返回Xuyan对一个话题的看法。"""
    return retriever.get_relevant_documents(query)


tools = [get_eugene_thoughts]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个有用的助手。"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# 我们需要在LLM上设置streaming=True以支持流式传输单个token。
# 当使用stream_log端点时。
# .stream对于代理流式传输动作观察对，而不是单个token。
llm = ChatOpenAI(
    api_key="我的API密钥",
    base_url="https://我的基准URL/v1",      
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
    temperature=0,
    streaming=True).configurable_fields(
        temperature=ConfigurableField(
            id="llm_temperature",
            name="LLM温度",
            description="LLM的温度",
            )
        )

llm_with_tools = llm.bind(
    functions=[format_tool_to_openai_function(t) for t in tools]
).with_config({"run_name": "LLM"})

class CustomAgentExecutor(Runnable):
    """将由代理执行器使用的自定义runnable。"""

    def __init__(self, **kwargs):
        """初始化runnable。"""
        super().__init__(**kwargs)
        self.agent = (
            {
                "input": lambda x: x["input"],
                "agent_scratchpad": lambda x: format_to_openai_functions(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )

    def invoke(self, input: Input, config: Optional[RunnableConfig] = None) -> Output:
        """将不会被使用。"""
        raise NotImplementedError()

    @property
    def config_specs(self) -> List[ConfigurableFieldSpec]:
        return self.agent.config_specs

    async def astream(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> AsyncIterator[Output]:
        """流式传输代理的输出。"""
        configurable = cast(Dict[str, Any], config.pop("configurable", {}))

        if configurable:
            configured_agent = self.agent.with_config(
                {
                    "configurable": configurable,
                }
            )
        else:
            configured_agent = self.agent

        executor = AgentExecutor(
            agent=configured_agent,
            tools=tools,
        ).with_config({"run_name": "executor"})

        async for output in executor.astream(input, config=config, **kwargs):
            yield output


app = FastAPI()

# 我们需要添加这些输入/输出模式，因为当前的AgentExecutor
# 在模式方面有所欠缺。
class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: Any


runnable = CustomAgentExecutor()

# 为使用自定义代理执行器向应用程序添加路由。
add_routes(
    app,
    runnable.with_types(input_type=Input, output_type=Output),
    disabled_endpoints=["invoke", "batch"],  # 未实现
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
