#!/usr/bin/env python
"""端点展示了可用的游乐场小部件。"""
import base64
from json import dumps
from typing import Any, Dict, List, Tuple

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.pydantic_v1 import BaseModel, Field
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_core.document_loaders import Blob
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    FunctionMessage,
    HumanMessage,
)
from langchain_core.runnables import RunnableLambda, RunnableParallel
from langchain_openai import ChatOpenAI

from langserve import CustomUserType
from langserve.server import add_routes

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

# 示例 1：聊天小部件
# 这展示了如何创建一个聊天小部件。


class ChatHistory(CustomUserType):
    chat_history: List[Tuple[str, str]] = Field(
        ...,
        examples=[[("a", "aa")]],
        extra={"widget": {"type": "chat", "input": "问题", "output": "答案"}},
    )
    question: str


def _format_to_messages(input: ChatHistory) -> List[BaseMessage]:
    """将输入格式化为消息列表。"""
    history = input.chat_history
    user_input = input.question

    messages = []

    for human, ai in history:
        messages.append(HumanMessage(content=human))
        messages.append(AIMessage(content=ai))
    messages.append(HumanMessage(content=user_input))
    return messages


model = ChatOpenAI()
chat_model = RunnableParallel({"answer": (RunnableLambda(_format_to_messages) | model)})
add_routes(
    app,
    chat_model.with_types(input_type=ChatHistory),
    config_keys=["configurable"],
    path="/chat",
)


# 示例 2：带历史记录的聊天小部件
# 这个没有连接到模型。它只是展示了FunctionMessages也可以在游乐场中显示。


class ChatHistoryMessage(BaseModel):
    chat_history: List[BaseMessage] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "位置"}},
    )
    location: str


def chat_message_bot(input: Dict[str, Any]) -> List[BaseMessage]:
    """重复问题两次的机器人。"""
    return [
        AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "get_weather",
                    "arguments": dumps({"location": input["location"]}),
                }
            },
        ),
        FunctionMessage(name="get_weather", content='{"value": 32}'),
        AIMessage(content=f"{input['location']}的天气：32"),
    ]


add_routes(
    app,
    RunnableLambda(chat_message_bot).with_types(input_type=ChatHistoryMessage),
    config_keys=["configurable"],
    path="/chat_message",
)

# 示例 3：文件处理小部件


class FileProcessingRequest(BaseModel):
    file: bytes = Field(..., extra={"widget": {"type": "base64file"}})
    num_chars: int = 100


def process_file(input: Dict[str, Any]) -> str:
    """从PDF的第一页提取文本。"""
    content = base64.decodebytes(input["file"])
    blob = Blob(data=content)
    documents = list(PDFMinerParser().lazy_parse(blob))
    content = documents[0].page_content
    return content[: input["num_chars"]]


add_routes(
    app,
    RunnableLambda(process_file).with_types(input_type=FileProcessingRequest),
    config_keys=["configurable"],
    path="/pdf",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
