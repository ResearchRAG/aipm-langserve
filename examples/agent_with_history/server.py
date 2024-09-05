#!/usr/bin/env python
"""示例 LangChain 服务器展示了一个具有对话历史的代理。

在这个例子中，历史完全存储在客户端。

请查看 LangServe 中的其他示例，了解如何使用 RunnableWithHistory
在服务器端存储历史记录。

相关 LangChain 文档：

* 创建自定义代理：https://python.langchain.com/docs/modules/agents/how_to/custom_agent 
* 使用代理进行流式传输：https://python.langchain.com/docs/modules/agents/how_to/streaming#custom-streaming-with-events 
* 通用流式文档：https://python.langchain.com/docs/expression_language/streaming 
* 消息历史记录：https://python.langchain.com/docs/expression_language/how_to/message_history 

**注意**
1. 要支持流式传输单个令牌，您需要使用 astream 事件端点
   而不是流式传输端点。
2. 此示例不截断消息历史记录，因此如果您发送了太多消息（超过令牌长度），
   它会崩溃。
3. 目前游乐场无法很好地呈现代理输出！如果您想使用游乐场，您需要使用 astream
   事件通过在另一个可运行项中包装它来自定义其服务器端输出。
4. 请参阅客户端笔记本，它有一个如何在客户端使用 stream_events 的示例！
"""  # noqa: E501
from typing import Any, List, Union

from fastapi import FastAPI
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.messages import AIMessage, FunctionMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_core.utils.function_calling import format_tool_to_openai_tool
from langchain_openai import ChatOpenAI

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "你是一个非常强大的助手，但不擅长计算单词的长度。 "
            "像平常一样与用户交谈。 "
            "如果他们要求你计算单词的长度，请使用工具",
        ),
        # 请注意提示中字段的顺序！
        # 正确的顺序是：
        # 1. history - 用户和代理之间的过去消息
        # 2. user - 用户的当前输入
        # 3. agent_scratchpad - 代理的工作空间，用于思考和
        #    调用工具以回应用户的输入。
        # 如果您更改了顺序，代理将无法正确工作，因为
        # 消息将按错误的顺序显示给底层 LLM。
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


@tool
def word_length(word: str) -> int:
    """返回计数器单词"""
    return len(word)


# 我们需要在 LLM 上设置 streaming=True 以支持流式传输单个令牌。
# 当使用 stream_log / stream 事件端点时，令牌将可用，
# 但当使用 stream 端点时不会，因为代理的流实现是流式传输动作观察对，而不是单个令牌。
# 请参见客户端笔记本，了解如何使用 stream 事件端点。
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=True)
llm = ChatOpenAI(
    api_key="我的API密钥",
    base_url="https://我的基准URL/v1",
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
)

tools = [word_length]


llm_with_tools = llm.bind(tools=[format_tool_to_openai_tool(tool) for tool in tools])

# 注意：对于生产用例，修剪提示以避免
# 超出模型使用的上下文窗口长度是个好主意。
#
# 要解决这个问题，简单地调整链路，以适当方式修剪提示
# 适合您的用例。
# 例如，您可能希望保留系统消息和最后 10 条消息。
# 或者，您可能希望根据令牌数量进行修剪。
# 或者，您可能希望对消息进行总结，以保留有关用户的信息。
#
# def prompt_trimmer(messages: List[Union[HumanMessage, AIMessage, FunctionMessage]]):
#     '''修剪提示以合理长度。'''
#     # 请注意，修剪时，您可能希望保留系统消息！
#     return messages[-10:] # 保留最后 10 条消息。

agent = (
    {
        "input": lambda x: x["input"],
        "agent_scratchpad": lambda x: format_to_openai_tool_messages(
            x["intermediate_steps"]
        ),
        "chat_history": lambda x: x["chat_history"],
    }
    | prompt
    # | prompt_trimmer # 参见上面的注释。
    | llm_with_tools
    | OpenAIToolsAgentOutputParser()
)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)


app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的 Runnable 接口启动一个简单的 API 服务器",
)


# 我们需要添加这些输入/输出模式，因为当前的 AgentExecutor
# 在模式方面有所欠缺。
class Input(BaseModel):
    input: str
    # 额外定义的字段表示聊天小部件。
    # 请参见主 README 中关于小部件的文档。
    # 小部件在游乐场中使用。
    # 请注意，目前游乐场对代理的支持不是很好。
    # 要获得更好的体验，您现在需要自定义流式输出
    chat_history: List[Union[HumanMessage, AIMessage, FunctionMessage]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "input", "output": "output"}},
    )


class Output(BaseModel):
    output: Any


# 为应用程序添加路由，以便在以下情况下使用链路：
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
