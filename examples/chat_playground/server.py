#!/usr/bin/env python
"""一个简单的聊天机器人示例，它在服务器和客户端之间传递当前的对话状态。"""
from typing import List, Union

from fastapi import FastAPI
from langchain_anthropic.chat_models import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 Langchain 的 Runnable 接口启动一个简单的 API 服务器",
)


# 声明一个链
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名为 Cob 的乐于助人、专业的助理。"),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | ChatAnthropic(model_name="claude-3-sonnet-20240229")


class InputChat(BaseModel):
    """聊天端点的输入。"""

    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
        ...,
        description="代表当前对话的聊天消息。",
    )


add_routes(
    app,
    chain.with_types(input_type=InputChat),
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
    playground_type="chat",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
