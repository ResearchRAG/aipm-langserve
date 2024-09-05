#!/usr/bin/env python
"""可配置运行实例的示例。

这个示例展示了如何使用两种配置运行实例的选项：

1) 可配置字段：使用这个来为特定的初始化参数指定值
2) 可配置替代品：使用这个来指定完整的替代运行实例
"""
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import ConfigurableField
from langchain_openai import ChatOpenAI

from langserve import add_routes

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用Langchain的Runnable接口启动一个简单的API服务器",
)

# 设置所有CORS启用的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

###############################################################################
#                示例 1：根据RunnableConfig配置字段          #
###############################################################################
model = ChatOpenAI(temperature=0.5).configurable_alternatives(
    ConfigurableField(
        id="llm",
        name="语言模型",
        description=(
            "决定为语言模型使用高还是低的温度参数。"
        ),
    ),
    high_temp=ChatOpenAI(temperature=0.9),
    low_temp=ChatOpenAI(temperature=0.1),
    default_key="medium_temp",
)
prompt = PromptTemplate.from_template(
    "讲一个关于{topic}的笑话。"
).configurable_fields(  # 可配置字段的示例
    template=ConfigurableField(
        id="prompt",
        name="提示",
        description="要使用的提示。必须包含{topic}。",
    )
)
chain = prompt | model | StrOutputParser()

add_routes(app, chain, path="/configurable_temp")


###############################################################################
#                示例 2：根据RunnableConfig配置提示          #
###############################################################################
configurable_prompt = PromptTemplate.from_template(
    "讲一个关于{topic}的笑话。"
).configurable_alternatives(
    ConfigurableField(
        id="prompt",
        name="提示",
        description="要使用的提示。必须包含{topic}。",
    ),
    default_key="joke",
    fact=PromptTemplate.from_template(
        "告诉我关于{topic}的一个事实，用{language}语言。"
    ),
)
prompt_chain = configurable_prompt | model | StrOutputParser()

add_routes(app, prompt_chain, path="/configurable_prompt")


###############################################################################
#             示例 3：根据请求元数据配置字段           #
###############################################################################


# 添加另一个示例路由，你可以根据请求的属性来配置模型。
# 这对于从请求头传递API密钥（需要谨慎）或使用请求的其他属性来配置模型很有用。
def fetch_api_key_from_header(config: Dict[str, Any], req: Request) -> Dict[str, Any]:
    if "x-api-key" in req.headers:
        config["configurable"]["openai_api_key"] = req.headers["x-api-key"]
    else:
        raise HTTPException(401, "未提供API密钥")

    return config


dynamic_auth_model = ChatOpenAI(openai_api_key="placeholder").configurable_fields(
    openai_api_key=ConfigurableField(
        id="openai_api_key",
        name="OpenAI API 密钥",
        description=("与OpenAI交互的API密钥"),
    ),
)

dynamic_auth_chain = dynamic_auth_model | StrOutputParser()

add_routes(
    app,
    dynamic_auth_chain,
    path="/auth_from_header",
    per_req_config_modifier=fetch_api_key_from_header,
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
