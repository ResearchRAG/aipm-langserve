#!/usr/bin/env python
"""示例LangChain服务器公开了一个会话检索链。

参考这里：

https://python.langchain.com/docs/expression_language/cookbook/retrieval#conversational-retrieval-chain 

要运行这个示例，你需要安装以下包：
pip install langchain openai faiss-cpu tiktoken
"""  # noqa: F401

from operator import itemgetter
from typing import List, Tuple

from fastapi import FastAPI
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate, format_document
from langchain_core.runnables import RunnableMap, RunnablePassthrough
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_ollama import ChatOllama, OllamaEmbeddings

from langserve import add_routes
from langserve.pydantic_v1 import BaseModel, Field

_TEMPLATE = """给定以下对话和后续问题，将后续问题改写为一个独立的原始语言问题。

聊天历史：
{chat_history}
后续输入：{question}
独立问题："""
CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(_TEMPLATE)

ANSWER_TEMPLATE = """仅根据以下上下文回答问题：
{context}

问题：{question}
"""
ANSWER_PROMPT = ChatPromptTemplate.from_template(ANSWER_TEMPLATE)

DEFAULT_DOCUMENT_PROMPT = PromptTemplate.from_template(template="{page_content}")


def _combine_documents(
    docs, document_prompt=DEFAULT_DOCUMENT_PROMPT, document_separator="\n\n"
):
    """将文档合并为一个字符串。"""
    doc_strings = [format_document(doc, document_prompt) for doc in docs]
    return document_separator.join(doc_strings)


def _format_chat_history(chat_history: List[Tuple]) -> str:
    """将聊天历史格式化为字符串。"""
    buffer = ""
    for dialogue_turn in chat_history:
        human = "人类：" + dialogue_turn[0]
        ai = "助手：" + dialogue_turn[1]
        buffer += "\n" + "\n".join([human, ai])
    return buffer


vectorstore = FAISS.from_texts(
    ["harrison worked at kensho"], embedding=OllamaEmbeddings(model="llama3.1")
)
retriever = vectorstore.as_retriever()

_inputs = RunnableMap(
    standalone_question=RunnablePassthrough.assign(
        chat_history=lambda x: _format_chat_history(x["chat_history"])
    )
    | CONDENSE_QUESTION_PROMPT
    | ChatOllama(model="llama3.1",temperature=0)
    | StrOutputParser(),
)
_context = {
    "context": itemgetter("standalone_question") | retriever | _combine_documents,
    "question": lambda x: x["standalone_question"],
}


# 用户输入
class ChatHistory(BaseModel):
    """与机器人的聊天历史。"""

    chat_history: List[Tuple[str, str]] = Field(
        ...,
        extra={"widget": {"type": "chat", "input": "question"}},
    )
    question: str


conversational_qa_chain = (
    _inputs | _context | ANSWER_PROMPT | ChatOllama(model="llama3.1") | StrOutputParser()
)
chain = conversational_qa_chain.with_types(input_type=ChatHistory)

app = FastAPI(
    title="LangChain 服务器",
    version="1.0",
    description="使用Langchain的Runnable接口启动一个简单的API服务器",
)
# 为使用链向应用程序添加路由：
# /invoke
# /batch
# /stream
add_routes(app, chain, enable_feedback_endpoint=True)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)
