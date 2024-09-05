#!/usr/bin/env python
"""示例聊天服务器，后端处理持久性。

为简化起见，我们这里使用文件存储——避免设置数据库的需要。这显然不适用于生产环境，
但有助于我们演示可运行的消息历史记录接口。

我们将使用cookies来识别用户。这将有助于说明如何从请求中获取配置。
"""
import re
from pathlib import Path
from typing import Any, Callable, Dict, Union

from fastapi import FastAPI, HTTPException, Request
from langchain_community.chat_message_histories import FileChatMessageHistory
from langchain_core import __version__
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import ConfigurableFieldSpec
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from typing_extensions import TypedDict

from langserve import add_routes

# 定义最小所需版本为 (0, 1, 0)
# 早期版本不允许在 RunnableWithMessageHistory 中指定自定义配置字段。
MIN_VERSION_LANGCHAIN_CORE = (0, 1, 0)

# 按 "." 分割版本字符串并转换为整数
LANGCHAIN_CORE_VERSION = tuple(map(int, __version__.split(".")))

if LANGCHAIN_CORE_VERSION < MIN_VERSION_LANGCHAIN_CORE:
    raise RuntimeError(
        f"langchain-core的最小所需版本为 {MIN_VERSION_LANGCHAIN_CORE}, "
        f"但找到的是 {LANGCHAIN_CORE_VERSION}"
    )


def _is_valid_identifier(value: str) -> bool:
    """检查值是否为有效标识符。"""
    # 使用正则表达式匹配允许的字符
    valid_characters = re.compile(r"^[a-zA-Z0-9-_]+$")
    return bool(valid_characters.match(value))


def create_session_factory(
    base_dir: Union[str, Path],
) -> Callable[[str], BaseChatMessageHistory]:
    """创建一个可以检索聊天历史的工厂。

    聊天历史按用户ID和对话ID键控。

    参数:
        base_dir: 用于存储聊天历史的基目录。

    返回:
        一个可以按用户ID和对话ID检索聊天历史的工厂。
    """
    base_dir_ = Path(base_dir) if isinstance(base_dir, str) else base_dir
    if not base_dir_.exists():
        base_dir_.mkdir(parents=True)

    def get_chat_history(user_id: str, conversation_id: str) -> FileChatMessageHistory:
        """根据用户ID和对话ID获取聊天历史。"""
        if not _is_valid_identifier(user_id):
            raise ValueError(
                f"用户ID {user_id} 格式不正确。"
                "用户ID只能包含字母数字字符、"
                "连字符和下划线。"
                "请在请求头中包含名为 'user-id' 的有效cookie。"
            )
        if not _is_valid_identifier(conversation_id):
            raise ValueError(
                f"对话ID {conversation_id} 格式不正确。"
                "对话ID只能包含字母数字字符、"
                "连字符和下划线。请通过配置提供有效的对话ID。例如, "
                "chain.invoke(.., {'configurable': {'conversation_id': '123'}})"
            )

        user_dir = base_dir_ / user_id
        if not user_dir.exists():
            user_dir.mkdir(parents=True)
        file_path = user_dir / f"{conversation_id}.json"
        return FileChatMessageHistory(str(file_path))

    return get_chat_history


app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用Langchain的Runnable接口启动一个简单的API服务器",
)


def _per_request_config_modifier(
    config: Dict[str, Any], request: Request
) -> Dict[str, Any]:
    """更新配置"""
    config = config.copy()
    configurable = config.get("configurable", {})
    # 查找名为 "user_id" 的cookie
    user_id = request.cookies.get("user_id", None)

    if user_id is None:
        raise HTTPException(
            status_code=400,
            detail="未找到用户ID。请设置名为 'user_id' 的cookie。",
        )

    configurable["user_id"] = user_id
    config["configurable"] = configurable
    return config


# 声明一个链
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名叫Bob的助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{human_input}"),
    ]
)

chain = prompt | ChatOpenAI()


class InputChat(TypedDict):
    """聊天端点的输入。"""

    human_input: str
    """人类输入"""


chain_with_history = RunnableWithMessageHistory(
    chain,
    create_session_factory("chat_histories"),
    input_messages_key="human_input",
    history_messages_key="history",
    history_factory_config=[
        ConfigurableFieldSpec(
            id="user_id",
            annotation=str,
            name="用户ID",
            description="用户的唯一标识符。",
            default="",
            is_shared=True,
        ),
        ConfigurableFieldSpec(
            id="conversation_id",
            annotation=str,
            name="对话ID",
            description="对话的唯一标识符。",
            default="",
            is_shared=True,
        ),
    ],
).with_types(input_type=InputChat)


add_routes(
    app,
    chain_with_history,
    per_req_config_modifier=_per_request_config_modifier,
    # 禁用游乐场和批量
    # 1) 游乐场我们通过头部传递信息，这在当前游乐场中不受支持。
    # 2) 禁用批量以避免用户混淆。只要用户适当地使用多个配置调用批量，
    #    批量将正常工作，但如果没有验证，用户可能会忘记这样做。
    #    此外，对于聊天机器人，支持批量可能没有太多意义。
    disabled_endpoints=["playground", "batch"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
