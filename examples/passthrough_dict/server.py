#!/usr/bin/env python
"""示例LangChain服务器在响应中传递部分输入信息。"""

from typing import Any, Callable, Dict, List, Optional, TypedDict

from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI

from langserve import add_routes

app = FastAPI(
    title="LangChain服务器",
    version="1.0",
    description="使用Langchain的Runnable接口快速搭建一个简单的API服务器",
)


def _create_projection(
    *, include_keys: Optional[List] = None, exclude_keys: Optional[List[str]] = None
) -> Callable[[dict], dict]:
    """创建一个投影函数。"""

    def _project_dict(
        d: dict,
    ) -> dict:
        """投影字典。"""
        keys = d.keys()
        if include_keys is not None:
            keys = set(keys) & set(include_keys)
        if exclude_keys is not None:
            keys = set(keys) - set(exclude_keys)
        return {k: d[k] for k in keys}

    return _project_dict


prompt = ChatPromptTemplate.from_messages(
    [("human", "将 `{thing}` 翻译成 {language}")]
)
model = ChatOpenAI(
    api_key="我的API密钥",
    base_url="https://我的基准URL/v1",      
    model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
)

underlying_chain = prompt | model

wrapped_chain = RunnableParallel(
    {
        "output": _create_projection(exclude_keys=["info"]) | underlying_chain,
        "info": _create_projection(include_keys=["info"]),
    }
)


class Input(TypedDict):
    thing: str
    language: str
    info: Dict[str, Any]


class Output(TypedDict):
    output: underlying_chain.output_schema
    info: Dict[str, Any]


add_routes(
    app, wrapped_chain.with_types(input_type=Input, output_type=Output), path="/v1"
)

# 版本2
# 使用RunnablePassthrough.assign
wrapped_chain_2 = RunnablePassthrough.assign(output=underlying_chain) | {
    "output": lambda x: x["output"],
    "info": lambda x: x["info"],
}

add_routes(
    app,
    wrapped_chain_2.with_types(input_type=Input, output_type=Output),
    path="/v2",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
