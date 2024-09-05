#!/usr/bin/env python
"""一个简单的聊天机器人示例，它仅在服务器和客户端之间传递当前的对话状态。"""
from typing import List, Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用Langchain的Runnable接口启动一个简单的API服务器",
)


# 设置所有CORS启用的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# 声明一个链
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名为Cob的乐于助人的助手。"),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | ChatAnthropic(model="claude-2") | StrOutputParser()


class InputChat(BaseModel):
    """聊天端点的输入。"""

    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
        ...,
        description="代表当前对话的聊天消息。",
        extra={"widget": {"type": "chat", "input": "messages"}},
    )


add_routes(
    app,
    chain.with_types(input_type=InputChat),
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
