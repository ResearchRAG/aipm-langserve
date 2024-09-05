#!/usr/bin/env python
"""
示例展示了如何在服务器上传和处理文件。

这个示例使用了一种非常简单的架构来处理文件上传和处理。

这种方法的主要问题是处理是在同一个进程中完成的，而不是卸载到进程池中。一个较小的问题是，base64编码增加了额外的编码/解码开销。

这个示例还指定了一个 "base64file" 小部件，它将创建一个小部件，允许用户使用 langserve 游乐场 UI 上传二进制文件。
"""
import base64

from fastapi import FastAPI
from langchain.pydantic_v1 import Field
from langchain_community.document_loaders.parsers.pdf import PDFMinerParser
from langchain_core.document_loaders import Blob
from langchain_core.runnables import RunnableLambda

from langserve import CustomUserType, add_routes

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 LangChain 的可运行接口快速搭建一个简单的 API 服务器",
)

# 注意：继承自 CustomUserType 而不是 BaseModel，否则
# 服务器会将其解码为字典而不是 pydantic 模型。
class FileProcessingRequest(CustomUserType):
    """包含 base64 编码文件的请求。"""

    # extra 字段用于为游乐场 UI 指定小部件。
    file: str = Field(..., extra={"widget": {"type": "base64file"}})
    num_chars: int = 100


def _process_file(request: FileProcessingRequest) -> str:
    """从 PDF 的第一页提取文本。"""
    content = base64.b64decode(request.file.encode("utf-8"))
    blob = Blob(data=content)
    documents = list(PDFMinerParser().lazy_parse(blob))
    content = documents[0].page_content
    return content[: request.num_chars]


add_routes(
    app,
    RunnableLambda(_process_file).with_types(input_type=FileProcessingRequest),
    config_keys=["configurable"],
    path="/pdf",
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
