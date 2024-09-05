#!/usr/bin/env python
"""示例 LangChain 服务器，展示如何为代理自定义流式传输。

示例使用 RunnableLambda 执行以下操作：

1) 使用代理的 astream 事件方法创建自定义流式 API 端点。
2) 根据用户请求实例化具有自定义工具的代理。

在这个例子中，我们保持了简单，并输出了代理的所有中间步骤的字符串给客户端。这只是为了演示目的，
通常您会希望以字典形式返回更结构化的输出。

要为代理添加历史记录，您可以使用 RunnableWithHistory。请参见 LangServe 中的其他示例，
了解如何使用 RunnableWithHistory 在服务器端存储历史记录。

或者，您可以在客户端跟踪历史记录，并在每个请求中将其发送到服务器。要使其工作，
您肯定希望修改流式输出以产生带有结构化输出的字典，这样在客户端就很容易确定代理的最终输出是什么。

根据用例自定义流式输出！

请注意，我们使用输入中的 `tools` 字段配置代理，而不是使用可配置字段。使用自定义可运行项和可配置字段
是另一种定制代理的选项。

请参见 configurable_agent_executor: https://github.com/langchain-ai/langserve/blob/main/examples/configurable_agent_executor/server.py 
了解使用具有可配置字段的自定义可运行项的示例。

相关 LangChain 文档：

* 创建自定义代理：https://python.langchain.com/docs/modules/agents/how_to/custom_agent 
* 使用代理进行流式传输：https://python.langchain.com/docs/modules/agents/how_to/streaming#custom-streaming-with-events 
* 通用流式文档：https://python.langchain.com/docs/expression_language/streaming 
* 消息历史记录：https://python.langchain.com/docs/expression_language/how_to/message_history 

**注意**
1. 此示例不会截断消息历史记录，因此如果您发送了太多消息（超过令牌长度），
   它将会崩溃。
2. 目前的游乐场无法很好地呈现代理输出！如果您想使用游乐场，您需要通过在另一个可运行项中包装 astream
   事件来自定义其服务器端输出。
3. 请参见客户端笔记本，了解 .stream() 的行为！
"""  # noqa: E501
from typing import Any, AsyncIterator, List, Literal

from fastapi import FastAPI
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad.openai_tools import (
    format_to_openai_tool_messages,
)
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langchain_core.utils.function_calling import format_tool_to_openai_tool
from langchain_openai import ChatOpenAI

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel

import os

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
        # 1. user - 用户的当前输入
        # 2. agent_scratchpad - 代理的工作空间，用于思考和
        #    调用工具以回应用户的输入。
        # 如果您更改了顺序，代理将无法正确工作，因为
        # 消息将按错误的顺序显示给底层 LLM。
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)


@tool
def word_length(word: str) -> int:
    """返回计数器单词"""
    return len(word)


@tool
def favorite_animal(name: str) -> str:
    """获取给定姓名的人最喜欢的动物"""
    if name.lower().strip() == "eugene":
        return "cat"
    return "dog"


# 我们需要在 LLM 上设置 streaming=True 以支持流式传输单个令牌。
# 当使用 stream_log / stream 事件端点时，令牌将可用，
# 但当使用 stream 端点时不会，因为代理的流实现是流式传输动作观察对，而不是单个令牌。
# 请参见客户端笔记本，了解如何使用 stream 事件端点。
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, streaming=True)
llm = ChatOpenAI(
    api_key="我的API密钥",
    base_url="https://我的基准URL/v1",      
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
)

TOOL_MAPPING = {
    "word_length": word_length,
    "favorite_animal": favorite_animal,
}
KnownTool = Literal["word_length", "favorite_animal"]


def _create_agent_with_tools(requested_tools: List[KnownTool]) -> AgentExecutor:
    """创建具有自定义工具的代理。"""
    tools = []

    for requested_tool in requested_tools:
        if requested_tool not in TOOL_MAPPING:
            raise ValueError(f"未知工具: {requested_tool}")
        tools.append(TOOL_MAPPING[requested_tool])

    if tools:
        llm_with_tools = llm.bind(
            tools=[format_tool_to_openai_tool(tool) for tool in tools]
        )
    else:
        llm_with_tools = llm

    agent = (
        {
            "input": lambda x: x["input"],
            "agent_scratchpad": lambda x: format_to_openai_tool_messages(
                x["intermediate_steps"]
            ),
        }
        | prompt
        | llm_with_tools
        | OpenAIToolsAgentOutputParser()
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True).with_config(
        {"run_name": "agent"}
    )
    return agent_executor


app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的 Runnable 接口启动一个简单的 API 服务器",
)


# 我们需要添加这些输入/输出模式，因为当前的 AgentExecutor
# 在模式方面有所欠缺。
class Input(BaseModel):
    input: str
    tools: List[KnownTool]


async def custom_stream(input: Input) -> AsyncIterator[str]:
    """一个可以流式传输内容的自定义可运行项。

    参数：
        input: 代理的输入。有关详细信息，请参见 Input 模型。

    产生：
        流式传输到客户端的字符串。

    为了简单起见，选择了字符串，但您可以自由地根据用例进行调整。

    您几乎肯定希望以字典形式返回更结构化的输出，这样可以很容易地确定代理在做什么，无需解析输出。

    在创建自定义流式 API 之前，您应该考虑是否可以使用现有的 astream 事件 API 并在客户端自定义输出
    （可能在服务器和客户端方面的总体工作较少）。
    """
    agent_executor = _create_agent_with_tools(input["tools"])
    async for event in agent_executor.astream_events(
        {
            "input": input["input"],
        },
        version="v1",
    ):
        kind = event["event"]
        if kind == "on_chain_start":
            if (
                event["name"] == "agent"
            ):  # 匹配 agent_executor 中的 `.with_config({"run_name": "Agent"})`
                yield "\n"
                yield (
                    f"启动代理: {event['name']} "
                    f"输入: {event['data'].get('input')}"
                )
                yield "\n"
        elif kind == "on_chain_end":
            if (
                event["name"] == "agent"
            ):  # 匹配 agent_executor 中的 `.with_config({"run_name": "Agent"})`
                yield "\n"
                yield (
                    f"完成代理: {event['name']} "
                    f"输出: {event['data'].get('output')['output']}"
                )
                yield "\n"
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                # 在 OpenAI 的上下文中，空内容意味着
                # 模型要求调用工具。
                # 所以我们只打印非空内容
                yield content
        elif kind == "on_tool_start":
            yield "\n"
            yield (
                f"启动工具: {event['name']} "
                f"输入: {event['data'].get('input')}"
            )
            yield "\n"
        elif kind == "on_tool_end":
            yield "\n"
            yield (
                f"完成工具: {event['name']} "
                f"输出: {event['data'].get('output')}"
            )
            yield "\n"


class Output(BaseModel):
    output: Any


# 为以下内容向应用程序添加路由：
# /invoke
# /batch
# /stream
# /stream_events
add_routes(
    app,
    RunnableLambda(custom_stream),
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
