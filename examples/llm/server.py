#!/usr/bin/env python
"""示例 LangChain 服务器公开了多个可运行项（在这种情况下是 LLM）。"""

from fastapi import FastAPI
# from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama


from langserve import add_routes

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的 Runnable 接口启动一个简单的 API 服务器",
)

# add_routes(
#     app,
#     ChatOpenAI(model="gpt-3.5-turbo-0125"),
#     path="/openai",
# )
# add_routes(
#     app,
#     ChatAnthropic(model="claude-3-haiku-20240307"),
#     path="/anthropic",
# )

add_routes(
    app,
    ChatOpenAI(
        api_key="我的API密钥",
        base_url="https://我的基准URL/v1",      
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        ),
    path="/groq",
)
add_routes(
    app,
    ChatOllama(model="llama3.1"),
    path="/ollama",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
