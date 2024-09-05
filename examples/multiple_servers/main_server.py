"""主服务器，公开一个或多个链作为HTTP端点。"""
from fastapi import FastAPI
from langchain_openai import ChatOpenAI

from langserve import add_routes

app = FastAPI()

# 添加一个示例链
add_routes(
    app,
    ChatOpenAI(
        api_key="我的API密钥",
        base_url="https://我的基准URL/v1",      
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"
        ),
    path="/chat_model",
)

if __name__ == "__main__":
    import uvicorn

    # 在端口8123上运行
    uvicorn.run(app, port=8123)
