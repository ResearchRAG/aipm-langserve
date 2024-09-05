"""客户端服务器通过远程可执行文件与主服务器交互。

此服务器为主服务器设置了一个简单的代理。它使用RemoteRunnable与主服务器进行交互。预期主服务器在
http://localhost:8123 上运行。

客户端服务器最终可能会做一些更聪明的事情，而不仅仅是作为代理。
"""
from fastapi import FastAPI

from langserve import RemoteRunnable, add_routes

app = FastAPI()

MAIN_SERVER_URL = (
    "http://localhost:8123/chat_model/"  # <-- 主服务器上可执行文件的URL
)
# 目前远程可执行文件的类型推断不是自动的，
# 因此你必须指定用于游乐场工作所使用的类型。
remote_runnable = RemoteRunnable(MAIN_SERVER_URL).with_types(input_type=str)


# 添加一个示例链
add_routes(
    app,
    remote_runnable,
    path="/proxied",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
