#!/usr/bin/env python
"""一个更复杂的例子，展示了如何在运行时配置索引名称。"""
from typing import Any, Iterable, List, Optional, Type

from fastapi import FastAPI
from langchain.schema.vectorstore import VST
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import (
    ConfigurableFieldSingleOption,
    RunnableConfig,
    RunnableSerializable,
)
from langchain_core.vectorstores import VectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field

vectorstore1 = FAISS.from_texts(
    ["猫咪喜欢鱼", "狗狗喜欢棍子"], embedding=OllamaEmbeddings(model="llama3.1")
)

vectorstore2 = FAISS.from_texts(["x_n+1=a * xn * (1-xn)"], embedding=OllamaEmbeddings(model="llama3.1"))


app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用Langchain的Runnable接口启动一个简单的API服务器",
)


class UnderlyingVectorStore(VectorStore):
    """这是用于演示目的的假矢量存储库。"""

    def __init__(self, collection_name: str) -> None:
        """具有集合名称的假矢量存储库。"""
        self.collection_name = collection_name

    def as_retriever(self) -> BaseRetriever:
        if self.collection_name == "index1":
            return vectorstore1.as_retriever()
        elif self.collection_name == "index2":
            return vectorstore2.as_retriever()
        else:
            raise NotImplementedError(
                f"没有为集合 {self.collection_name} 提供检索器"
            )

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> List[str]:
        raise NotImplementedError()

    @classmethod
    def from_texts(
        cls: Type[VST],
        texts: List[str],
        embedding: Embeddings,
        metadatas: Optional[List[dict]] = None,
        **kwargs: Any,
    ) -> VST:
        raise NotImplementedError()

    def similarity_search(
        self, embedding: List[float], k: int = 4, **kwargs: Any
    ) -> List[Document]:
        raise NotImplementedError()


class ConfigurableRetriever(RunnableSerializable[str, List[Document]]):
    """创建一个可以由用户配置的自定义检索器。

    这是一个如何创建可以在运行时配置使用不同集合名称的自定义可运行实例的例子。

    配置涉及在运行时实例化一个带有集合名称的矢量存储库，
    因此底层矢量存储库的实例化应该是*低成本*的。

    例如，它在实例化时不应该进行任何网络请求。

    确保您使用的矢量存储库满足此标准。
    """

    collection_name: str

    def invoke(
        self, input: str, config: Optional[RunnableConfig] = None
    ) -> List[Document]:
        """调用检索器。"""
        vectorstore = UnderlyingVectorStore(self.collection_name)
        retriever = vectorstore.as_retriever()
        return retriever.invoke(input, config=config)


configurable_collection_name = ConfigurableRetriever(
    collection_name="index1"
).configurable_fields(
    collection_name=ConfigurableFieldSingleOption(
        id="collection_name",
        name="集合名称",
        description="用于检索器的集合名称。",
        options={
            "Index 1": "index1",
            "Index 2": "index2",
        },
        default="Index 1",
    )
)


class Request(BaseModel):
    __root__: str = Field(default="cat", description="搜索查询")


add_routes(app, configurable_collection_name.with_types(input_type=Request))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
