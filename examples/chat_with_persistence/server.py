#!/usr/bin/env python
"""带有持久化处理的聊天服务器示例。

为了简化，我们在这里使用文件存储——避免设置数据库的需要。这显然不是生产环境中的好主意，
但将帮助我们演示RunnableWithMessageHistory接口。

我们将使用cookies来识别用户和/或会话。这将有助于说明如何从请求中获取配置。
"""
import re
from pathlib import Path
from typing import Callable, Union

from fastapi import FastAPI, HTTPException
from langchain_anthropic import ChatAnthropic

# from langchain_ollama import ChatOllama
# from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field


def _is_valid_identifier(value: str) -> bool:
    """检查会话ID是否为有效格式。"""
    # 使用正则表达式匹配允许的字符
    valid_characters = re.compile(r"^[a-zA-Z0-9-_]+$")
    return bool(valid_characters.match(value))


def create_session_factory(
    base_dir: Union[str, Path],
) -> Callable[[str], BaseChatMessageHistory]:
    """创建一个会话ID工厂，从基础目录创建会话ID。

    参数：
        base_dir: 用于存储聊天记录的基础目录。

    返回：
        一个会话ID工厂，从基础路径创建会话ID。
    """
    base_dir_ = Path(base_dir) if isinstance(base_dir, str) else base_dir
    if not base_dir_.exists():
        base_dir_.mkdir(parents=True)

    def get_chat_history(session_id: str) -> FileChatMessageHistory:
        """从会话ID获取聊天记录。"""
        if not _is_valid_identifier(session_id):
            raise HTTPException(
                status_code=400,
                detail=f"会话ID `{session_id}` 格式无效。"
                "会话ID只能包含字母数字字符、"
                "连字符和下划线。",
            )
        file_path = base_dir_ / f"{session_id}.json"
        return FileChatMessageHistory(str(file_path))

    return get_chat_history


app = FastAPI(
    title="LangChain服务器",
    version="1.0",
    description="使用Langchain的Runnable接口快速搭建一个简单的API服务器",
)


# 声明一个链
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名叫Bob的助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

chain = prompt | ChatAnthropic(model="claude-2")


class InputChat(BaseModel):
    """聊天端点的输入。"""

    # 字段extra定义了一个聊天小部件。
    # 截至2024-02-05，这个聊天小部件尚未完全支持。
    # 它被包含在文档中以展示应该如何指定，但在后端完全支持历史持久化
    # 之前将无法工作。
    human_input: str = Field(
        ...,
        description="人类输入到聊天系统的文本。",
        extra={"widget": {"type": "chat", "input": "human_input"}},
    )


chain_with_history = RunnableWithMessageHistory(
    chain,
    create_session_factory("chat_histories"),
    input_messages_key="human_input",
    history_messages_key="history",
).with_types(input_type=InputChat)


add_routes(
    app,
    chain_with_history,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
