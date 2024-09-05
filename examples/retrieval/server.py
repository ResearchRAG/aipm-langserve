#!/usr/bin/env python
"""示例LangChain服务器公开了一个检索器。"""
from fastapi import FastAPI
from langchain_community.vectorstores import FAISS
# from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from langserve import add_routes

vectorstore = FAISS.from_texts(
    ["猫喜欢鱼", "狗喜欢棍子"], embedding=OllamaEmbeddings(
        model="llama3.1")
)

retriever = vectorstore.as_retriever()

app = FastAPI(
    title="LangChain服务器",
    version="1.0",
    description="使用Langchain的Runnable接口快速搭建一个简单的API服务器",
)
# 在以下路径下为应用添加路由以使用检索器：
# /invoke
# /batch
# /stream
add_routes(app, retriever)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
