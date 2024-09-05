#!/usr/bin/env python
"""示例展示了如何直接使用底层的APIHandler类结合认证。

这个示例展示了如何根据用户身份应用逻辑。

你可以基于这些概念构建更复杂的应用：
* 添加允许用户管理他们的文档的端点。
* 制作一个更复杂的可运行程序，对检索到的文档进行操作；例如，
  一个会话代理，用检索到的文档（这些文档是特定于用户的文档）
  回应用户的输入。

对于认证，我们使用与用户名相同的假令牌，适应
FastAPI文档中的以下示例：

https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/     

**注意**

这个示例实际上并不安全，不应该用于生产环境。

一旦你了解了如何使用`per_req_config_modifier`，请阅读
FastAPI文档并实现适当的认证：
https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/     

**注意**

这个示例没有将认证与OpenAPI集成，因此OpenAPI文档将无法
帮助进行认证。如果使用`add_routes`，这目前是一个限制。
如果你需要这个功能，你可以直接使用底层的`APIHandler`类，
它提供了最大的灵活性。
"""
from importlib import metadata
from typing import Any, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from langchain_community.vectorstores.chroma import Chroma
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

from langserve import APIHandler
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
        "username": "john",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
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
    # 这并不提供任何安全性
    # 检查下一个版本
    user = _get_user(FAKE_USERS_DB, token)
    return user


@app.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user_dict = FAKE_USERS_DB.get(form_data.username)
    if not user_dict:
        raise HTTPException(status_code=400, detail="用户名或密码不正确")
    user = UserInDB(**user_dict)
    hashed_password = _fake_hash_password(form_data.password)
    if not hashed_password == user.hashed_password:
        raise HTTPException(status_code=400, detail="用户名或密码不正确")

    return {"access_token": user.username, "token_type": "bearer"}


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = _fake_decode_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="用户未激活")
    return current_user


class PerUserVectorstore(RunnableSerializable):
    """一个自定义的可运行程序，返回给定用户的相关文档列表。

    该可运行程序可以通过用户配置，并且搜索结果会
    通过用户ID进行过滤。
    """

    user_id: Optional[str]
    vectorstore: VectorStore

    class Config:
        # 允许任意类型，因为VectorStore是一个抽象接口
        # 而不是pydantic模型
        arbitrary_types_allowed = True

    def _invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs: Any
    ) -> List[Document]:
        """调用检索器。"""
        # 警告：验证底层向量存储的文档以确保它确实使用了过滤器。
        # 强烈建议使用单元测试来验证这种行为，因为
        # 实现可能会因为底层向量存储的不同而有所不同。
        retriever = self.vectorstore.as_retriever(
            search_kwargs={"filter": {"owner_id": self.user_id}}
        )
        return retriever.invoke(input, config=config)

    def invoke(
        self, input: str, config: Optional[RunnableConfig] = None, **kwargs
    ) -> List[Document]:
        """为整数加一。"""
        return self._call_with_config(self._invoke, input, config, **kwargs)


vectorstore = Chroma(
    collection_name="some_collection",
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
    user_id=None,  # 占位符ID，将被per_req_config_modifier替换
    vectorstore=vectorstore,
).configurable_fields(
    # 注意：确保在per_req_config_modifier中为每个请求覆盖用户ID
    # 这不应该由客户端配置。
    user_id=ConfigurableField(
        id="user_id",
        name="用户ID",
        description="用于检索器的用户ID。",
    )
)


# 定义API处理器
api_handler = APIHandler(
    per_user_retriever,
    # 可运行程序的命名空间。
    # 像批量/调用这样的端点应该在/my_runnable/invoke
    # 和/my_runnable/batch等下面。
    path="/my_runnable",
)


PYDANTIC_VERSION = metadata.version("pydantic")
_PYDANTIC_MAJOR_VERSION: int = int(PYDANTIC_VERSION.split(".")[0])


# **注意** 你的代码不需要包含两个版本。
# 根据你使用的pydantic版本使用适当的版本。
# 两个版本都包含在这里是为了演示目的。
#
# 如果使用pydantic <2，一切如预期工作。
# 然而，当安装pydantic >=2时，事情就有点
# 更复杂了，因为LangChain使用了pydantic.v1命名空间
# 但pydantic.v1命名空间不受FastAPI支持。
# 参见这个问题：https://github.com/tiangolo/fastapi/issues/10360     
# 所以当使用pydantic >=2时，我们需要使用普通的starlette请求
# 和响应，我们将没有文档。
# 或者我们可以为请求和响应创建自定义模型。
# 底层的API处理器仍然会正确验证请求
# 即使使用了普通请求也会如此。
if _PYDANTIC_MAJOR_VERSION == 1:

    @app.post("/my_runnable/invoke")
    async def invoke_with_auth(
        # 包含在内是为了文档目的
        invoke_request: api_handler.InvokeRequest,
        request: Request,
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> Response:
        """处理请求。"""
        # API处理器验证请求中被可运行程序使用的部分
        # （例如，输入，配置字段）
        config = {"configurable": {"user_id": current_user.username}}
        return await api_handler.invoke(request, server_config=config)
else:

    @app.post("/my_runnable/invoke")
    async def invoke_with_auth(
        request: Request,
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> Response:
        """处理请求。"""
        # API处理器验证请求中被可运行程序使用的部分
        # （例如，输入，配置字段）
        config = {"configurable": {"user_id": current_user.username}}
        return await api_handler.invoke(request, server_config=config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
