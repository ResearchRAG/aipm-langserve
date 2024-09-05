# 🦜️🏓 LangServe

[![发布说明](https://img.shields.io/github/release/langchain-ai/langserve)](https://github.com/langchain-ai/langserve/releases) 
[![下载量](https://static.pepy.tech/badge/langserve/month)](https://pepy.tech/project/langserve) 
[![开放问题](https://img.shields.io/github/issues-raw/langchain-ai/langserve)](https://github.com/langchain-ai/langserve/issues) 
[![](https://dcbadge.vercel.app/api/server/6adMQxSpJS?compact=true&style=flat)](https://discord.com/channels/1038097195422978059/1170024642245832774) 

## 概览

[LangServe](https://github.com/langchain-ai/langserve) 帮助开发者将 `LangChain` 的[可运行组件和链](https://python.langchain.com/docs/expression_language/) 部署为 REST API。

这个库与 [FastAPI](https://fastapi.tiangolo.com/) 集成，并使用 [pydantic](https://docs.pydantic.dev/latest/) 进行数据验证。

此外，它还提供了一个客户端，可用于调用部署在服务器上的可运行组件。
JavaScript 客户端可在 [LangChain.js](https://js.langchain.com/docs/ecosystem/langserve) 中获取。

## 特性

- 从你的 LangChain 对象自动推断输入和输出模式，并在每个 API 调用上执行，带有丰富的错误消息
- 带有 JSONSchema 和 Swagger 的 API 文档页面（插入示例链接）
- 支持单个服务器上许多并发请求的 `/invoke`, `/batch` 和 `/stream` 端点
- `/stream_log` 端点，用于流式传输链/代理的所有（或部分）中间步骤
- **新** 从 0.0.40 版本开始，支持 `/stream_events`，使得流式传输更加容易，无需解析 `/stream_log` 的输出。
- `/playground/` 的游乐场页面，带有流式输出和中间步骤
- 内置（可选）追踪到 [LangSmith](https://www.langchain.com/langsmith)，只需添加你的 API 密钥（见[说明](https://docs.smith.langchain.com/)) 
- 所有功能都使用经过实战测试的开源 Python 库构建，如 FastAPI、Pydantic、uvloop 和 asyncio。
- 使用客户端 SDK 调用 LangServe 服务器，就像它是一个本地运行的可运行组件（或直接调用 HTTP API）
- [LangServe Hub](https://github.com/langchain-ai/langchain/blob/master/templates/README.md) 

## ⚠️ LangGraph 兼容性

LangServe 主要设计用于部署简单的可运行组件，并与 langchain-core 中的知名原语一起工作。

如果你需要 LangGraph 的部署选项，你应该查看 [LangGraph Cloud (beta)](https://langchain-ai.github.io/langgraph/cloud/)，它更适合部署 LangGraph 应用。

## 限制

- 客户端回调尚不支持源自服务器的事件
- 当使用 Pydantic V2 时，不会生成 OpenAPI 文档。Fast API 不支持 [混合 pydantic v1 和 v2 命名空间](https://github.com/tiangolo/fastapi/issues/10360)。 
  请参阅下文以获取更多详细信息。

## 安全性

- 版本 0.0.13 - 0.0.15 中的漏洞 -- 游乐场端点允许访问服务器上的任意文件。[在 0.0.16 版本中已解决](https://github.com/langchain-ai/langserve/pull/98). 

## 安装

对于客户端和服务器：

```bash
pip install "langserve[all]"
```

或者 `pip install "langserve[client]"` 用于客户端代码，
和 `pip install "langserve[server]"` 用于服务器代码。

## LangChain CLI 🛠️

使用 `LangChain` CLI 快速启动 `LangServe` 项目。

要使用 langchain CLI，请确保安装了最新版本的 `langchain-cli`。你可以使用 `pip install -U langchain-cli` 进行安装。

## 设置

**注意**：我们使用 `poetry` 进行依赖管理。请遵循 poetry [文档](https://python-poetry.org/docs/) 以了解更多信息。

### 1. 使用 langchain cli 命令创建新应用

```sh
langchain app new my-app
```

### 2. 在 add_routes 中定义可运行组件。转到 server.py 并编辑

```sh
add_routes(app. NotImplemented)
```

### 3. 使用 `poetry` 添加第三方包（例如，langchain-openai, langchain-anthropic, langchain-mistral 等）。

```sh
poetry add [package-name] // 例如 `poetry add langchain-openai`
```

### 4. 设置相关环境变量。例如，

```sh
export OPENAI_API_KEY="sk-..."
```

### 5. 启动你的应用

```sh
poetry run langchain serve --port=8100
```

## 示例

通过 [LangChain 模板](https://github.com/langchain-ai/langchain/blob/master/templates/README.md) 快速启动你的 LangServe 实例。

更多示例，请查看模板 [索引](https://github.com/langchain-ai/langchain/blob/master/templates/docs/INDEX.md) 
或 [示例](https://github.com/langchain-ai/langserve/tree/main/examples) 目录。

| 描述                                                                                                                                                                                                                                                        | 链接                                                                                                                                                                                                                               |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **LLMs** 最小示例，保留 OpenAI 和 Anthropic 聊天模型。使用异步，支持批处理和流式传输。                                                                                                                                              | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/llm/server.py),  [客户端](https://github.com/langchain-ai/langserve/blob/main/examples/llm/client.ipynb)                                                        |
| **检索器** 将检索器作为可运行组件公开的简单服务器。                                                                                                                                                                                                | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/retrieval/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/retrieval/client.ipynb)                                            |
| **对话检索器** 通过 LangServe 公开的 [对话检索器](https://python.langchain.com/docs/expression_language/cookbook/retrieval#conversational-retrieval-chain)                                                                           | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/conversational_retrieval_chain/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/conversational_retrieval_chain/client.ipynb)  |
| **代理** 基于 [OpenAI 工具](https://python.langchain.com/docs/modules/agents/agent_types/openai_functions_agent) 且没有 **对话历史** 的代理                                                                                                             | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/agent/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/agent/client.ipynb)                                                    |
| **代理** 基于 [OpenAI 工具](https://python.langchain.com/docs/modules/agents/agent_types/openai_functions_agent) 且有 **对话历史** 的代理                                                                                                                | [服务器](https://github.com/langchain-ai/langserve/blob/main/examples/agent_with_history/server.py),  [客户端](https://github.com/langchain-ai/langserve/blob/main/examples/agent_with_history/client.ipynb)                          |
| [RunnableWithMessageHistory](https://python.langchain.com/docs/expression_language/how_to/message_history) 用于在后端持久化聊天，通过客户端提供的 `session_id` 进行索引。                                                                    | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/chat_with_persistence/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/chat_with_persistence/client.ipynb)                    |
| [RunnableWithMessageHistory](https://python.langchain.com/docs/expression_language/how_to/message_history) 用于在后端持久化聊天，通过客户端提供的 `conversation_id` 和 `user_id` 进行索引（参见 Auth 以正确实现 `user_id`）。 | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/chat_with_persistence_and_user/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/chat_with_persistence_and_user/client.ipynb)  |
| [可配置可运行组件](https://python.langchain.com/docs/expression_language/how_to/configure) 用于创建支持运行时配置索引名称的检索器。                                                                                      | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/configurable_retrieval/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/configurable_retrieval/client.ipynb)                  |
| [可配置可运行组件](https://python.langchain.com/docs/expression_language/how_to/configure) 展示可配置字段和可配置替代方案。                                                                                                      | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/configurable_chain/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/configurable_chain/client.ipynb)                          |
| **APIHandler** 展示如何使用 `APIHandler` 而不是 `add_routes`。这为开发者定义端点提供了更多的灵活性。与所有 FastAPI 模式兼容，但需要更多的努力。                                                        | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/api_handler_examples/server.py)                                                                                                                                |
| **LCEL 示例** 使用 LCEL 操作字典输入的示例。                                                                                                                                                                                          | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/passthrough_dict/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/passthrough_dict/client.ipynb)                              |
| **认证** 使用 `add_routes`：可以跨所有与应用关联的端点应用的简单认证。（单独使用时，不适用于实现每用户逻辑。）                                                                                           | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/global_deps/server.py)                                                                                                                                    |
| **认证** 使用 `add_routes`：基于路径依赖的简单认证机制。（单独使用时，不适用于实现每用户逻辑。）                                                                                                                    | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/path_dependencies/server.py)                                                                                                                              |
| **认证** 使用 `add_routes`：实现每用户逻辑和认证，用于使用每次请求配置修饰符的端点。（**注意**：目前，不与 OpenAPI 文档集成。）                                                                                 | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/per_req_config_modifier/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/auth/per_req_config_modifier/client.ipynb)      |
| **认证** 使用 `APIHandler`：实现每用户逻辑和认证，展示如何在用户拥有的文档内进行搜索。                                                                                                                                           | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/api_handler/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/auth/api_handler/client.ipynb)                              |
| **小部件** 游乐场可以使用的不同小部件（文件上传和聊天）                                                                                                                                                                              | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/widgets/chat/tuples/server.py)                                                                                                                                 |
| **小部件** 用于 LangServe 游乐场的文件上传小部件。                                                                                                                                                                                                      | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing/client.ipynb)                                |

## 示例应用

### 服务器

这是一个部署了 OpenAI 聊天模型、Anthropic 聊天模型和一个使用 Anthropic 模型讲述笑话的链的服务器。

```python
#!/usr/bin/env python
from fastapi import FastAPI
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatAnthropic, ChatOpenAI
from langserve import add_routes

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用 Langchain 的可运行接口的简单 API 服务器",
)

add_routes(
    app,
    ChatOpenAI(model="gpt-3.5-turbo-0125"),
    path="/openai",
)

add_routes(
    app,
    ChatAnthropic(model="claude-3-haiku-20240307"),
    path="/anthropic",
)

model = ChatAnthropic(model="claude-3-haiku-20240307")
prompt = ChatPromptTemplate.from_template("给我讲一个关于 {topic} 的笑话")
add_routes(
    app,
    prompt | model,
    path="/joke",
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
```

如果你想从浏览器调用你的端点，你还需要设置 CORS 头。
你可以使用 FastAPI 的内置中间件来实现这一点：

```python
from fastapi.middleware.cors import CORSMiddleware

# 设置所有 CORS 启用的源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)
```

### 文档

如果你部署了上面的服务器，你可以使用以下命令查看生成的 OpenAPI 文档：

> ⚠️ 如果使用 pydantic v2，则不会为 _invoke_, _batch_, _stream_, 
> _stream_log_ 生成文档。请参阅下文 [Pydantic](#pydantic) 部分以获取更多详细信息。

```sh
curl localhost:8000/docs
```

确保 **添加** `/docs` 后缀。

> ⚠️ 索引页面 `/` 按 **设计** 未定义，所以 `curl localhost:8000` 或访问
> 该 URL 将返回 404。如果你想在 `/` 上有内容，请定义一个端点 `@app.get("/")`。

### 客户端

Python SDK

```python

from langchain.schema import SystemMessage, HumanMessage
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableMap
from langserve import RemoteRunnable

openai = RemoteRunnable("http://localhost:8000/openai/")
anthropic = RemoteRunnable("http://localhost:8000/anthropic/")
joke_chain = RemoteRunnable("http://localhost:8000/joke/")

joke_chain.invoke({"topic": "parrots"})

# 或异步
await joke_chain.ainvoke({"topic": "parrots"})

prompt = [
    SystemMessage(content='表现得像一只猫或鹦鹉。'),
    HumanMessage(content='你好！')
]

# 支持 astream
async for msg in anthropic.astream(prompt):
    print(msg, end="", flush=True)

prompt = ChatPromptTemplate.from_messages(
    [("system", "告诉我一个关于 {topic} 的长故事")]
)

# 可以定义自定义链
chain = prompt | RunnableMap({
    "openai": openai,
    "anthropic": anthropic,
})

chain.batch([{"topic": "parrots"}, {"topic": "cats"}])
```

在 TypeScript 中（需要 LangChain.js 版本 0.0.166 或更高）：

```typescript
import { RemoteRunnable } from "@langchain/core/runnables/remote";

const chain = new RemoteRunnable({
  url: `http://localhost:8000/joke/`,
});
const result = await chain.invoke({
  topic: "cats",
});
```

Python 使用 `requests`：

```python
import requests

response = requests.post(
    "http://localhost:8000/joke/invoke",
    json={'input': {'topic': 'cats'}}
)
response.json()
```

你还可以使用 `curl`：

```sh
curl --location --request POST 'http://localhost:8000/joke/invoke' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "input": {
            "topic": "cats"
        }
    }'
```

## 端点

以下代码：

```python
...
add_routes(
    app,
    runnable,
    path="/my_runnable",
)
```

向服务器添加了这些端点：

- `POST /my_runnable/invoke` - 调用单个输入的可运行组件
- `POST /my_runnable/batch` - 调用一批输入的可运行组件
- `POST /my_runnable/stream` - 调用单个输入并在流式传输输出
- `POST /my_runnable/stream_log` - 调用单个输入并在流式传输输出时，包括生成的中间步骤的输出
- `POST /my_runnable/astream_events` - 调用单个输入并在生成事件时流式传输事件，
  包括来自中间步骤的事件。
- `GET /my_runnable/input_schema` - 可运行组件输入的 JSON 模式
- `GET /my_runnable/output_schema` - 可运行组件输出的 JSON 模式
- `GET /my_runnable/config_schema` - 可运行组件配置的 JSON 模式

这些端点匹配
[LangChain 表达式语言接口](https://python.langchain.com/docs/expression_language/interface)  --
请参考此文档以获取更多详细信息。

## 游乐场

你可以在 `/my_runnable/playground/` 找到你的可运行组件的游乐场页面。这
提供了一个简单的 UI
来 [配置](https://python.langchain.com/docs/expression_language/how_to/configure) 
并调用你的可运行组件，带有流式输出和中间步骤。

<p align="center">
<img src="https://github.com/langchain-ai/langserve/assets/3205522/5ca56e29-f1bb-40f4-84b5-15916384a276"  width="50%"/>
</p>

### 小部件

游乐场支持 [小部件](#playground-widgets)，并且可以用来测试你的
可运行组件的不同输入。请参阅下文以获取更多详细信息。

### 分享

此外，对于可配置的可运行组件，游乐场还将允许你配置可运行组件并分享一个带有配置的链接：

<p align="center">
<img src="https://github.com/langchain-ai/langserve/assets/3205522/86ce9c59-f8e4-4d08-9fa3-62030e0f521d"  width="50%"/>
</p>

## 聊天游乐场

LangServe 还支持一个以聊天为重点的游乐场，可以选择加入并在 `/my_runnable/playground/` 下使用。与普通游乐场不同，只有特定类型的可运行组件受到支持 - 可运行组件的输入模式必须是 `dict`，其中要么：

- 一个键，该键的值必须是聊天消息的列表。
- 两个键，一个的值是消息列表，另一个代表最近的消息。

我们建议你使用第一种格式。

可运行组件还必须返回 `AIMessage` 或字符串。

要启用它，你必须在添加路由时设置 `playground_type="chat"`。这里有一个例子：

```python
# 声明一个链
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名为 Cob 的乐于助人的、专业的助理。"),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | ChatAnthropic(model="claude-2")


class InputChat(BaseModel):
    """聊天端点的输入。"""

    messages: List[Union[HumanMessage, AIMessage, SystemMessage]] = Field(
        ...,
        description="代表当前对话的聊天消息。",
    )


add_routes(
    app,
    chain.with_types(input_type=InputChat),
    enable_feedback_endpoint=True,
    enable_public_trace_link_endpoint=True,
    playground_type="chat",
)
```

如果你使用 LangSmith，你还可以设置 `enable_feedback_endpoint=True` 在你的路由上启用点赞/差评按钮
在每条消息之后，和 `enable_public_trace_link_endpoint=True` 添加一个按钮，为运行创建公共追踪。
注意，你还需要设置以下环境变量：

```bash
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="YOUR_PROJECT_NAME"
export LANGCHAIN_API_KEY="YOUR_API_KEY"
```

这里有一个启用上述两个选项的例子：

<p align="center">
<img src="./.github/img/chat_playground.png" width="50%"/>
</p>

注意：如果你启用了公共追踪链接，你的链的内部将被暴露。我们建议仅在演示或测试中使用此设置。

## 传统链

LangServe 与通过 [LangChain 表达式语言](https://python.langchain.com/docs/expression_language/) 构建的 Runnables（可运行组件）
和传统链（继承自 `Chain`）一起工作。
然而，一些传统链的输入模式可能是不完整/错误的，
导致错误。
这可以通过在 LangChain 中更新这些链的 `input_schema` 属性来修复。
如果你遇到任何错误，请在此仓库中提出问题，我们将努力
解决它。

## 部署

### 部署到 AWS

你可以使用 [AWS Copilot CLI](https://aws.github.io/copilot-cli/) 部署到 AWS

```bash
copilot init --app [application-name] --name [service-name] --type 'Load Balanced Web Service' --dockerfile './Dockerfile' --deploy
```

点击 [这里](https://aws.amazon.com/containers/copilot/) 了解更多。

### 部署到 Azure

你可以使用 Azure Container Apps (Serverless) 部署到 Azure：

```
az containerapp up --name [container-app-name] --source . --resource-group [resource-group-name] --environment  [environment-name] --ingress external --target-port 8001 --env-vars=OPENAI_API_KEY=your_key
```

你可以在 [这里](https://learn.microsoft.com/en-us/azure/container-apps/containerapp-up) 
找到更多信息

### 部署到 GCP

你可以使用以下命令将应用部署到 GCP Cloud Run：

```
gcloud run deploy [your-service-name] --source . --port 8001 --allow-unauthenticated --region us-central1 --set-env-vars=OPENAI_API_KEY=your_key
```

## 社区贡献

#### 部署到 Railway

[示例 Railway 仓库](https://github.com/PaulLockett/LangServe-Railway/tree/main) 

[![在 Railway 上部署](https://railway.app/button.svg)](https://railway.app/template/pW9tXP?referralCode=c-aq4K) 

## Pydantic

LangServe 提供对 Pydantic 2 的支持，但有一些限制。

1. 当使用 Pydantic V2 时，不会为 invoke/batch/stream/stream_log 生成 OpenAPI 文档。Fast API 不支持 [混合 pydantic v1 和 v2 命名空间]。为解决此问题，请使用 `pip install pydantic==1.10.17`。
2. LangChain 在 Pydantic v2 中使用 v1 命名空间。请阅读
   [以下指南以确保与 LangChain 兼容](https://github.com/langchain-ai/langchain/discussions/9337) 

除了这些限制外，我们期望 API 端点、游乐场和任何其他
功能按预期工作。

## 高级

### 处理认证

如果你需要在服务器上添加认证，请阅读 Fast API 的文档
关于 [依赖项](https://fastapi.tiangolo.com/tutorial/dependencies/) 
和 [安全性](https://fastapi.tiangolo.com/tutorial/security/). 

以下示例展示了如何使用 FastAPI 原语为 LangServe 端点设置认证逻辑。

你需要提供实际的认证逻辑，用户表等。

如果你不确定你在做什么，你可以尝试使用现有的解决方案 [Auth0](https://auth0.com/). 

#### 使用 add_routes

如果你使用 `add_routes`，请参见
示例 [这里](https://github.com/langchain-ai/langserve/tree/main/examples/auth). 

| 描述                                                                                                                                                                        | 链接                                                                                                                                                                                                                           |
| :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **认证** 使用 `add_routes`：可以跨所有与应用关联的端点应用的简单认证。（单独使用时，不适用于实现每用户逻辑。）           | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/global_deps/server.py)                                                                                                                                |
| **认证** 使用 `add_routes`：基于路径依赖的简单认证机制。（单独使用时，不适用于实现每用户逻辑。）                                    | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/path_dependencies/server.py)                                                                                                                          |
| **认证** 使用 `add_routes`：实现每用户逻辑和认证，用于使用每次请求配置修饰符的端点。（**注意**：目前，不与 OpenAPI 文档集成。） | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/per_req_config_modifier/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/auth/per_req_config_modifier/client.ipynb)  |

或者，你可以使用 FastAPI 的 [中间件](https://fastapi.tiangolo.com/tutorial/middleware/). 

使用全局依赖项和路径依赖项的优点是认证将在 OpenAPI 文档页面中得到适当的支持，但
这些不足以实现每用户逻辑（例如，制作一个只能搜索用户拥有的文档的应用）。

如果你需要实现每用户逻辑，你可以使用 `per_req_config_modifier` 或 `APIHandler`（下面）来实现这个逻辑。

**每用户**

如果你需要授权或依赖于用户逻辑，
指定 `per_req_config_modifier` 当使用 `add_routes`。使用一个可调用接收
原始 `Request` 对象，可以从中提取相关信息用于认证和授权。

#### 使用 APIHandler

如果你对 FastAPI 和 python 感到舒适，你可以使用 LangServe 的 [APIHandler](https://github.com/langchain-ai/langserve/blob/main/examples/api_handler_examples/server.py). 

| 描述                                                                                                                                                                                                 | 链接                                                                                                                                                                                                           |
| :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **认证** 使用 `APIHandler`：实现每用户逻辑和认证，展示如何在用户拥有的文档内进行搜索。                                                                                    | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/auth/api_handler/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/auth/api_handler/client.ipynb)          |
| **APIHandler** 展示如何使用 `APIHandler` 而不是 `add_routes`。这为开发者定义端点提供了更多的灵活性。与所有 FastAPI 模式兼容，但需要更多的努力。 | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/api_handler_examples/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/api_handler_examples/client.ipynb)  |

这是一项有点多的工作，但它给你完全控制端点定义，所以
你可以做任何你需要的自定义逻辑认证。

### 文件

LLM 应用通常涉及文件处理。可以制作不同的架构
以实现文件处理；在高层次上：

1. 文件可能通过专用端点上传到服务器，并使用一个
   单独的端点进行处理
2. 文件可能通过值（文件的字节）或引用（例如，s3 url
   到文件内容）上传
3. 处理端点可能是阻塞的或非阻塞的
4. 如果需要大量的处理，处理可能会被卸载到专用的
   进程池

你应该确定对你的应用来说什么是合适的架构。

目前，要通过值上传文件到可运行组件，请使用 base64 编码文件（还不支持 `multipart/form-data`）。

这是一个 [示例](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing) 
展示了如何使用 base64 编码将文件发送到远程可运行组件。

记住，你总是可以通过引用上传文件（例如，s3 url）或将它们作为
multipart/form-data 上传到专用端点。

### 自定义输入和输出类型

所有可运行组件都定义了输入和输出类型。

你可以通过 `input_schema` 和 `output_schema` 属性访问它们。

`LangServe` 使用这些类型进行验证和文档编制。

如果你想覆盖默认推断的类型，你可以使用 `with_types` 方法。

这里有一个玩具示例来说明这个想法：

```python
from typing import Any

from fastapi import FastAPI
from langchain.schema.runnable import RunnableLambda

app = FastAPI()


def func(x: Any) -> int:
    """类型错误的函数，应该接受一个 int，但接受任何东西。"""
    return x + 1


runnable = RunnableLambda(func).with_types(
    input_type=int,
)

add_routes(app, runnable)
```

### 自定义用户类型

如果你希望数据反序列化为一个 pydantic 模型而不是等效的字典表示，
请继承 `CustomUserType`。

目前，此类型仅在 **服务器** 端工作，并用于指定所需的 _解码_ 行为。如果继承自这个类型
服务器将保持解码后的类型为 pydantic 模型而不是
将其转换为字典。

```python
from fastapi import FastAPI
from langchain.schema.runnable import RunnableLambda

from langserve import add_routes
from langserve.schema import CustomUserType

app = FastAPI()


class Foo(CustomUserType):
    bar: int


def func(foo: Foo) -> int:
    """示例函数，期望一个 Foo 类型，它是一个 pydantic 模型"""
    assert isinstance(foo, Foo)
    return foo.bar


# 注意，输入和输出类型是自动推断的！
# 你不需要指定它们。
# runnable = RunnableLambda(func).with_types( # <-- 在这种情况下不需要
#     input_type=Foo,
#     output_type=int,
#
add_routes(app, RunnableLambda(func), path="/foo")
```

### 游乐场小部件

游乐场允许你从后端为你的可运行组件定义自定义小部件。

这里有一些示例：

| 描述                                                                           | 链接                                                                                                                                                                                                 |
| :------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **小部件** 游乐场可以使用的不同小部件（文件上传和聊天） | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/widgets/chat/tuples/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/widgets/client.ipynb)      |
| **小部件** 用于 LangServe 游乐场的文件上传小部件。                         | [服务器](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing/server.py),  [客户端](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing/client.ipynb)  |

#### 模式

- 小部件在字段级别指定，并作为输入类型的 JSON 模式的一部分发货
- 小部件必须包含一个名为 `type` 的键，其值为已知
  一系列小部件之一
- 其他小部件键将与描述 JSON 对象中路径的值相关联

```typescript
type JsonPath = number | string | (number | string)[];
type NameSpacedPath = { title: string; path: JsonPath }; // 使用 title 来模仿 json 模式，但可以使用命名空间
type OneOfPath = { oneOf: JsonPath[] };

type Widget = {
  type: string; // 一些已知类型（例如，base64file, chat 等）
  [key: string]: JsonPath | NameSpacedPath | OneOfPath;
};
```

### 可用小部件

目前，用户只能手动指定两种小部件：

1. 文件上传小部件
2. 聊天历史记录小部件

请参阅下文以获取有关这些小部件的更多信息。

游乐场 UI 上的所有其他小部件都由 UI 根据可运行组件的配置模式自动创建和管理。当你创建可配置的可运行组件时，
游乐场应该为你创建适当的小部件，以便你控制行为。

#### 文件上传小部件

允许在 UI 游乐场中为文件创建文件上传输入，
这些文件被上传为 base64 编码的字符串。这里有一个
完整的 [示例](https://github.com/langchain-ai/langserve/tree/main/examples/file_processing). 

片段：

```python
try:
    from pydantic.v1 import Field
except ImportError:
    from pydantic import Field

from langserve import CustomUserType


# 注意：继承自 CustomUserType 而不是 BaseModel，否则
#        服务器会将其解码为字典而不是 pydantic 模型。
class FileProcessingRequest(CustomUserType):
    """包含 base64 编码文件的请求。"""

    # extra 字段用于指定游乐场 UI 的小部件。
    file: str = Field(..., extra={"widget": {"type": "base64file"}})
    num_chars: int = 100

```

示例小部件：

<p align="center">
<img src="https://github.com/langchain-ai/langserve/assets/3205522/52199e46-9464-4c2e-8be8-222250e08c3f"  width="50%"/>
</p>

### 聊天小部件

查看
[小部件示例](https://github.com/langchain-ai/langserve/tree/main/examples/widgets/chat/tuples/server.py). 

要定义聊天小部件，请确保你传递 "type": "chat"。

- "input" 是 JSONPath 到 _Request_ 中包含新输入消息的字段。
- "output" 是 JSONPath 到 _Response_ 中包含新输出消息的字段。
- 如果整个输入或输出应如其所是使用（
  例如，如果输出是聊天消息的列表。）

这里有一个片段：

```python
class ChatHistory(CustomUserType):
    chat_history: List[Tuple[str, str]] = Field(
        ...,
        examples=[[("human input", "ai response")]],
        extra={"widget": {"type": "chat", "input": "question", "output": "answer"}},
    )
    question: str


def _format_to_messages(input: ChatHistory) -> List[BaseMessage]:
    """将输入格式化为消息列表。"""
    history = input.chat_history
    user_input = input.question

    messages = []

    for human, ai in history:
        messages.append(HumanMessage(content=human))
        messages.append(AIMessage(content=ai))
    messages.append(HumanMessage(content=user_input))
    return messages


model = ChatOpenAI()
chat_model = RunnableParallel({"answer": (RunnableLambda(_format_to_messages) | model)})
add_routes(
    app,
    chat_model.with_types(input_type=ChatHistory),
    config_keys=["configurable"],
    path="/chat",
)
```

示例小部件：

<p align="center">
<img src="https://github.com/langchain-ai/langserve/assets/3205522/a71ff37b-a6a9-4857-a376-cf27c41d3ca4"  width="50%"/>
</p>

你也可以直接指定消息列表作为你的一个参数，如这个片段所示：

```python
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "你是一个名为 Cob 的乐于助人的助理。"),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | ChatAnthropic(model="claude-2")


class MessageListInput(BaseModel):
    """聊天端点的输入。"""
    messages: List[Union[HumanMessage, AIMessage]] = Field(
        ...,
        description="代表当前对话的聊天消息。",
        extra={"widget": {"type": "chat", "input": "messages"}},
    )


add_routes(
    app,
    chain.with_types(input_type=MessageListInput),
    path="/chat",
)
```

看 [这个示例文件](https://github.com/langchain-ai/langserve/tree/main/examples/widgets/chat/message_list/server.py) 以获取示例。

### 启用/禁用端点（LangServe >=0.0.33）

你可以在为给定链添加路由时启用/禁用暴露的端点。

使用 `enabled_endpoints` 如果你想确保在升级 langserve 到较新版本时永远不会获得新端点。

启用：下面的代码将只启用 `invoke`, `batch` 和
相应的 `config_hashes` 端点变体。

```python
add_routes(app, chain, enabled_endpoints=["invoke", "batch", "config_hashes"], path="/mychain")
```

禁用：下面的代码将为链禁用游乐场

```python
add_routes(app, chain, disabled_endpoints=["playground"], path="/mychain")
```


