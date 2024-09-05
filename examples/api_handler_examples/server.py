"""一个示例，展示了如何直接使用 API 处理器。

要使 RemoteClient 正常工作，路由必须与客户端预期的路由相匹配；即 /invoke, /batch, /stream 等。不应使用尾随斜杠。
"""
from importlib import metadata
from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response
from langchain_core.runnables import RunnableLambda
from sse_starlette import EventSourceResponse

from langserve import APIHandler

PYDANTIC_VERSION = metadata.version("pydantic")
_PYDANTIC_MAJOR_VERSION: int = int(PYDANTIC_VERSION.split(".")[0])

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的 Runnable 接口启动一个简单的 API 服务器",
)


##
# 示例 1 -- 调用和批量处理，并生成文档
# 此端点展示了如何使用 APIHandler 暴露 `invoke` 和 `batch`。
# 它还展示了如何正确生成文档，以便与 Fast API 和 pydantic 版本兼容。
def add_one(x: int) -> int:
    """给定数字加一。"""
    return x + 1


chain = RunnableLambda(add_one)

api_handler = APIHandler(chain, path="/simple")


# 首先注册没有文档的端点
@app.post("/simple/invoke", include_in_schema=False)
async def simple_invoke(request: Request) -> Response:
    """处理请求。"""
    # API 处理器验证请求的部分内容
    # 这些内容由可运行项使用（例如，输入，配置字段）
    return await api_handler.invoke(request)


@app.post("/simple/batch", include_in_schema=False)
async def simple_batch(request: Request) -> Response:
    """处理请求。"""
    # API 处理器验证请求的部分内容
    # 这些内容由可运行项使用（例如，输入，配置字段）
    return await api_handler.batch(request)


# 这里，我们展示了如何为端点生成文档。
# 请注意，这是从实际端点分开完成的。
# 这有两个原因：
# 1. FastAPI 不支持在文档端点中使用 pydantic.v1 模型。
#    "https://github.com/tiangolo/fastapi/issues/10360" 
#    LangChain 使用 pydantic.v1 模型！
# 2. 可配置的 Runnables 具有 *动态* 模式，这意味着
#    输入的形状取决于配置。
#    在这种情况下，openapi 模式是最佳努力，显示文档
#    将适用于默认配置（以及任何不冲突的配置）。
if _PYDANTIC_MAJOR_VERSION == 1:  # 不要在您自己的代码中使用
    # 添加文档
    @app.post("/simple/invoke")
    async def simple_invoke_docs(
        request: api_handler.InvokeRequest,
    ) -> api_handler.InvokeResponse:
        """仅用于文档目的的 API 端点。填充 /docs 端点"""
        raise NotImplementedError(
            "这个端点仅用于文档目的"
        )

    @app.post("/simple/batch")
    async def simple_batch_docs(
        request: api_handler.BatchRequest,
    ) -> api_handler.BatchResponse:
        """仅用于文档目的的 API 端点。填充 /docs 端点"""
        raise NotImplementedError(
            "这个端点仅用于文档目的"
        )

else:
    print(
        "跳过 pydantic v2 的文档生成: "
        "https://github.com/tiangolo/fastapi/issues/10360" 
    )


##
# 示例 2 -- 使用 API 处理器暴露 `invoke` 和 `stream`。
# 使用 FastAPI Depends 获取准备好的 API 处理器。
async def _get_api_handler() -> APIHandler:
    """准备一个 RunnableLambda。"""
    return APIHandler(RunnableLambda(add_one), path="/v2")


@app.post("/v2/invoke")
async def v2_invoke(
    request: Request, runnable: Annotated[APIHandler, Depends(_get_api_handler)]
) -> Response:
    """处理调用请求。"""
    # API 处理器验证请求的部分内容
    # 这些内容由可运行项使用（例如，输入，配置字段）
    return await runnable.invoke(request)


@app.post("/v2/stream")
async def v2_stream(
    request: Request, runnable: Annotated[APIHandler, Depends(_get_api_handler)]
) -> EventSourceResponse:
    """处理流请求。"""
    # API 处理器验证请求的部分内容
    # 这些内容由可运行项使用（例如，输入，配置字段）
    return await runnable.stream(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
