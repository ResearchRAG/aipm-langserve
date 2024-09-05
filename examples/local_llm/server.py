#!/usr/bin/env python
"""示例 LangChain 服务器，运行本地大型语言模型。

**注意**：此服务器适用于原型设计/开发用途，但在可能存在来自不同用户的并发请求的生产环境中不应使用。
截至目前，Ollama 被设计为单用户使用，无法处理并发请求，详见此问题：
https://github.com/ollama/ollama/issues/358

部署本地模型时，请确保了解模型是否能够处理并发请求。如果并发请求处理不当，服务器可能会崩溃，或者根本无法同时处理多个用户。
"""
from fastapi import FastAPI
from langchain_community.chat_models import ChatOllama

from langserve import add_routes

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 Langchain 的可运行接口快速搭建一个简单的 API 服务器",
)


llm = ChatOllama(model="llama3.1")

add_routes(
    app,
    llm,
    path="/ollama",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
