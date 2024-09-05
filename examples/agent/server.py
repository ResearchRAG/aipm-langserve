#!/usr/bin/env python
"""
示例 LangChain 服务器公开了一个会话检索代理。

相关 LangChain 文档：

* 创建自定义代理：https://python.langchain.com/docs/modules/agents/how_to/custom_agent 
* 使用代理进行流式传输：https://python.langchain.com/docs/modules/agents/how_to/streaming#custom-streaming-with-events 
* 通用流式传输文档：https://python.langchain.com/docs/expression_language/streaming 

其它参考文档：

https://docs.together.ai/docs/openai-api-compatibility

**注意**
1. 要支持流式传输单个标记，你需要使用 astream events 端点而不是流式传输端点。
2. 此示例不会截断消息历史记录，因此如果你发送了太多消息（超过标记长度），它将会崩溃。
3. 目前游乐场无法很好地呈现代理输出！如果你想使用游乐场，你需要使用 astream events 通过在另一个可运行的包装中自定义其服务器端输出。
4. 请参阅客户端笔记本，其中有如何使用 stream_events 客户端端的例子！
"""
from typing import Any

from fastapi import FastAPI
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.pydantic_v1 import BaseModel
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.utils.function_calling import format_tool_to_openai_function
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from langserve import add_routes

vectorstore = FAISS.from_texts(
    ["猫喜欢鱼", "狗喜欢棍子"], embedding=OllamaEmbeddings(model="llama3.1")
)
retriever = vectorstore.as_retriever()


@tool
def get_eugene_thoughts(query: str) -> list:
    """返回 Eugene 对某个话题的看法。"""
    return retriever.get_relevant_documents(query)


tools = [get_eugene_thoughts]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个有用的助手。"),
        # 请注意用户输入与 agent_scratchpad 的顺序很重要。
        # agent_scratchpad 是代理的工作空间，用于思考，
        # 调用工具，查看工具输出，以回应给定的
        # 用户输入。它必须在用户输入之后。
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)

# 我们需要在 LLM 上设置 streaming=True 以支持流式传输单个标记。
# 当使用 stream_log / stream events 端点时，标记将可用，
# 但是当使用 stream 端点时不会，因为代理的流实现是流式传输动作观察对，而不是单个标记。
# 请参阅显示如何使用 stream events 端点的客户端笔记本。
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=True)
llm = ChatOpenAI(
    api_key="我的API密钥",
    base_url="https://我的基准URL/v1",
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
)

llm_with_tools = llm.bind(functions=[format_tool_to_openai_function(t) for t in tools])

agent = (
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

agent_executor = AgentExecutor(agent=agent, tools=tools)

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的可运行接口快速搭建一个简单的 API 服务器",
)


# 我们需要添加这些输入/输出模式，因为当前的 AgentExecutor
# 在模式方面有所欠缺。
class Input(BaseModel):
    input: str


class Output(BaseModel):
    output: Any


# 为应用程序添加路由，以便在以下路径下使用链：
# /invoke
# /batch
# /stream
# /stream_events
add_routes(
    app,
    agent_executor.with_types(input_type=Input, output_type=Output).with_config(
        {"run_name": "agent"}
    ),
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
