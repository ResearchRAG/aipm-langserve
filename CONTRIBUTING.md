# 贡献指南

## 贡献者许可协议

我们对帮助 LangServe 进化并致力于该项目的的贡献者表示感激。作为 LangServe 的主要赞助商，LangChain, Inc. 旨在构建开放的产品，这些产品可以惠及数千名开发者，同时允许我们建立可持续的业务。对于所有对 LangServe 的代码贡献，我们要求贡献者完成并签署一份贡献者许可协议（“CLA”）。贡献者与项目之间的协议是明确的，因此 LangServe 用户可以对源代码的法律地位及其使用权有信心。CLA 不改变我们软件使用的底层许可条款，即 LangServe 许可。

在您能够为 LangServe 做出贡献之前，如果您还没有签署，一个机器人将在 PR 上发表评论，要求您同意 CLA。同意 CLA 是代码合并的先决条件，并且只需要在首次为项目做出贡献时发生。所有后续的贡献都将遵循同一 CLA。

## 🗺️ 指南

### 依赖管理：Poetry 及其他环境/依赖管理工具

本项目使用 [Poetry](https://python-poetry.org/) v1.6.1+ 作为依赖管理工具。

### 本地开发依赖

安装 langserve 开发需求（用于运行 langchain、运行示例、代码格式化、测试和覆盖）：

```sh
poetry install --with test,dev
```

然后验证测试是否通过：

```sh
make test
```

### 格式化和代码检查

在提交 PR 之前，请先在本地运行；CI 系统也会进行检查。

#### 代码格式化

本项目的格式化通过 [Black](https://black.readthedocs.io/en/stable/) 和 [ruff](https://docs.astral.sh/ruff/rules/) 的组合来完成。

要运行本项目的格式化：

```sh
make format
```

#### 代码检查

本项目的代码检查通过 [Black](https://black.readthedocs.io/en/stable/)、[ruff](https://docs.astral.sh/ruff/rules/) 和 [mypy](http://mypy-lang.org/) 的组合来完成。

要运行本项目的代码检查：

```sh
make lint
```

## 前端游乐场开发

在开发 LangServe 游乐场时，请记住以下几点：

### 设置

切换到 `langserve/playground` 或 `langserve/chat_playground` 目录，然后运行 `yarn` 安装所需的依赖。`yarn dev` 将在开发模式下启动游乐场，地址为 `http://localhost:5173/____LANGSERVE_BASE_URL/`。

您可以使用 `poetry run python path/to/file.py` 运行 `examples/` 仓库中的一个链。

### 设置 CORS

在开发游乐场的开发模式时，您可能需要在示例路由中添加以下内容以处理 CORS：

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
