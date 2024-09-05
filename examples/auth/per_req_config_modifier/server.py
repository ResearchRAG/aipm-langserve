#!/usr/bin/env python
"""示例展示了如何使用 `per_req_config_modifier`。

这个简单示例展示了如何使用可配置的可运行实例与每个请求的配置修改来实现根据用户不同而变化的行为。

你可以基于这些概念构建一个更复杂的应用程序：
* 添加允许用户管理他们的文档的端点。
* 制作一个更复杂的可运行实例，它可以使用检索到的文档执行某些操作；例如，
  一个会话代理，它使用检索到的文档（特定于用户的文档）响应用户的输入。

对于认证，我们使用一个与用户名相同的假令牌，从 FastAPI 文档中调整以下示例：

https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/ 

**注意**

这个示例实际上并不安全，不应该用于生产环境。

一旦你了解了如何使用 `per_req_config_modifier`，请阅读 FastAPI 文档并实现适当的认证：
https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/ 


**注意**

这个示例没有将认证与 OpenAPI 集成，因此 OpenAPI 文档将无法帮助进行认证。这目前是使用 `add_routes` 的一个限制。
如果你需要这个功能，你可以直接使用底层的 `APIHandler` 类，它提供了最大的灵活性。
"""
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.runnables import (
    ConfigurableField,
    RunnableConfig,
    RunnableSerializable,
)
from langchain_core.vectorstores import VectorStore

# from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from typing_extensions import Annotated

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel


class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None


class UserInDB(User):
    hashed_password: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

FAKE_USERS_DB = {
    "alice": {
        "username": "alice",
        "full_name": "Alice Wonderson",
        "email": "alice@example.com",
        "hashed_password": "fakehashedsecret1",
        "disabled": False,
    },
    "john": {
        "username": "john",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret2",
        "disabled": False,
    },
    "bob": {
        "username": "bob",
        "full_name": "Bob Builder",
        "email": "bob@example.com",
        "hashed_password": "fakehashedsecret3",
        "disabled": True,
    },
}


def _fake_hash_password(password: str) -> str:
    """伪造一个哈希密码。"""
    return "fakehashed" + password


def _get_user(db: dict, username: str) -> Union[UserInDB, None]:
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)


def _fake_decode_token(token: str) -> Union[User, None]:
    # 这并不提供任何安全保障
    # 请查看下一版本
    user = _get_user(FAKE_USERS_DB, token)
    return user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = FAKE_USERS_DB.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="错误的用户名或密码")
    user = UserInDB(**user_dict)
    hashed_password = _fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="错误的用户名或密码")

    return {"access_token": user.username, "token_type": "bearer"}


async def get_current_active_user_from_request(request: Request) -> User:
    """从请求中获取当前活跃用户。"""
    token = await oauth2_scheme(request)
    user = _fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(status_code=400, detail="非活跃用户")
    return user


class PerUserVectorstore(RunnableSerializable):
    """一个自定义可运行实例，它为给定用户返回文档列表。

    该可运行实例可以通过用户进行配置，并且搜索结果会根据用户 ID 进行过滤。
    """

    user_id: Optional[str]
    vectorstore: VectorStore

    class Config:
        # 允许任意类型，因为 VectorStore 是一个抽象接口
        # 并不是一个 pydantic 模型
        arbitrary_types_allowed = True

    def _invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> List[Document]:
        """调用检索器。"""
        # 警告：验证底层 vectorstore 文档以确保它实际上使用了过滤器。
        # 强烈建议使用单元测试来验证这种行为，因为不同的底层 vectorstore 实现可能会有所不同。
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"filter": {"owner_id": self.user_id}}
        )
        return retriever.invoke(input, config=config)

    def invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> List[Document]:
        """调用检索器。"""
        return self._call_with_config(self._invoke, input, config, **kwargs)


async def per_req_config_modifier(config: Dict, request: Request) -> Dict:
    """为每个请求修改配置。"""
    user = await get_current_active_user_from_request(request)
    config["configurable"] = {}
    # 注意：确保每个请求都覆盖了用户 ID。
    # 在这种情况下，我们不应该接受用户提供的用户 ID！
    config["configurable"]["user_id"] = user.username
    return config


vectorstore = Chroma(
    collection_name="some_collection",
    # embedding_function=OpenAIEmbeddings(),
    embedding_function=OllamaEmbeddings(model="llama3.1"),
)

vectorstore.add_documents(
    [
        Document(
            page_content="猫喜欢奶酪",
            metadata={"owner_id": "alice"},
        ),
        Document(
            page_content="猫喜欢老鼠",
            metadata={"owner_id": "alice"},
        ),
        Document(
            page_content="狗喜欢棍子",
            metadata={"owner_id": "john"},
        ),
        Document(
            page_content="我最喜欢的食物是奶酪",
            metadata={"owner_id": "john"},
        ),
        Document(
            page_content="我喜欢海边散步",
            metadata={"owner_id": "john"},
        ),
        Document(
            page_content="狗喜欢草地",
            metadata={"owner_id": "bob"},
        ),
    ]
)

per_user_retriever = PerUserVectorstore(
    user_id=None,  # 占位符 ID，将由 per_req_config_modifier 替换
    vectorstore=vectorstore,
).configurable_fields(
    # 注意：确保在 per_req_config_modifier 中为每个请求覆盖用户 ID。
    # 这不应该由客户端配置。
    user_id=ConfigurableField(
        id="user_id",
        name="用户 ID",
        description="用于检索器的用户 ID。",
    )
)

add_routes(
    app,
    per_user_retriever,
    per_req_config_modifier=per_req_config_modifier,
    enabled_endpoints=["invoke"],
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
