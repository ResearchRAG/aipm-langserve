#!/usr/bin/env python
"""示例LangChain服务器，使用FastAPI路由器。

当应用程序增长时，使用FastAPI的路由器来组织路由变得非常有用。

更多文档请访问：

https://fastapi.tiangolo.com/tutorial/bigger-applications/ 
"""
from fastapi import APIRouter, FastAPI
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from langserve import add_routes

app = FastAPI()

router = APIRouter(prefix="/models")

# 调用此路由器将在跟踪日志中显示为 /models/openai
add_routes(
    router,
    ChatOpenAI(model="gpt-3.5-turbo-0125"),
    path="/openai",
)
# 调用此路由器将在跟踪日志中显示为 /models/anthropic
add_routes(
    router,
    ChatAnthropic(model="claude-3-haiku-20240307"),
    path="/anthropic",
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
