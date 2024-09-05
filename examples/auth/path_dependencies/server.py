#!/usr/bin/env python
"""一个示例，展示了如何使用路径依赖进行认证。

路径依赖应用于 `add_routes` 添加的所有路由。

为了简洁起见，我们提供了一个占位符 verify_token 函数，展示了如何使用路径依赖。

要实现适当的认证，请参见 FastAPI 文档：

* https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/ 
* https://fastapi.tiangolo.com/tutorial/dependencies/ 
* https://fastapi.tiangolo.com/tutorial/security/ 
"""  # noqa: E501

from fastapi import Depends, FastAPI, Header, HTTPException
from langchain_core.runnables import RunnableLambda
from typing_extensions import Annotated

from langserve import add_routes


async def verify_token(x_token: Annotated[str, Header()]) -> None:
    """验证令牌是否有效。"""
    # 用你实际的认证逻辑替换这个
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


app = FastAPI()


def add_one(x: int) -> int:
    """给一个整数加一。"""
    return x + 1


chain = RunnableLambda(add_one)


add_routes(
    app,
    chain,
    dependencies=[Depends(verify_token)],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
