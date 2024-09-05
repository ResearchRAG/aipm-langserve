#!/usr/bin/env python
"""一个使用 FastAPI 全局依赖的示例。

如果应用程序的所有端点都可以使用相同的认证逻辑，那么这种方法是可行的。

对于简单的应用程序来说，这可能是一个合理的解决方案。

参见：

* https://fastapi.tiangolo.com/tutorial/dependencies/global-dependencies/ 
* https://fastapi.tiangolo.com/tutorial/dependencies/ 
* https://fastapi.tiangolo.com/tutorial/security/ 
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from langchain_core.runnables import RunnableLambda
from typing_extensions import Annotated

from langserve import add_routes


async def verify_token(x_token: Annotated[str, Header()]) -> None:
    """验证令牌是否有效。"""
    # 用你实际的认证逻辑替换这里
    if x_token != "secret-token":
        raise HTTPException(status_code=400, detail="X-Token header invalid")


app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    dependencies=[Depends(verify_token)],
)


def add_one(x: int) -> int:
    """给一个整数加一。"""
    return x + 1


chain = RunnableLambda(add_one)


add_routes(
    app,
    chain,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
