# 安全政策

## 报告开源软件漏洞

LangChain 与 [huntr by Protect AI](https://huntr.com/) 合作，为我们的开源项目提供赏金计划。

请通过访问以下链接报告与 LangChain 开源项目相关的安全漏洞：

[https://huntr.com/bounties/disclose/](https://huntr.com/bounties/disclose/?target=https%3A%2F%2Fgithub.com%2Flangchain-ai%2Flangchain&validSearch=true)

在报告漏洞之前，请查阅：

1) 下方的“范围内目标”和“范围外目标”。
2) [langchain-ai/langchain](https://python.langchain.com/docs/contributing/repo_structure) 单体仓库结构。
3) LangChain [安全指南](https://python.langchain.com/docs/security) 以了解我们认为什么是安全漏洞与开发者责任的区别。

### 范围内目标

以下包和仓库符合漏洞赏金资格：

- langchain-core
- langchain（见例外情况）
- langchain-community（见例外情况）
- langgraph
- langserve

### 范围外目标

huntr 定义的所有范围外目标，以及：

- **langchain-experimental**：此仓库用于实验性代码，不符合漏洞赏金资格，对该仓库的漏洞报告将被标记为有趣或浪费时间，并在不附带赏金的情况下发布。
- **工具**：在 langchain 或 langchain-community 中的工具不符合漏洞赏金资格。这包括以下目录：
  - langchain/tools
  - langchain-community/tools
  - 请查阅我们的 [安全指南](https://python.langchain.com/docs/security) 了解更多详情，但一般来说，工具与现实世界交互。开发者应理解其代码的安全影响，并负责其工具的安全性。
- 已用安全通知记录的代码。这将根据具体情况决定，但很可能不符合赏金资格，因为代码已经用应该遵循的指南记录了，以确保其应用的安全。
- 任何与 LangSmith 相关的仓库或 API，见下文。

## 报告 LangSmith 漏洞

请通过电子邮件 `security@langchain.dev` 报告与 LangSmith 相关的安全漏洞。

- LangSmith 网站：https://smith.langchain.com 
- SDK 客户端：https://github.com/langchain-ai/langsmith-sdk 

### 其他安全问题

对于任何其他安全问题，请通过 `security@langchain.dev` 与我们联系。
