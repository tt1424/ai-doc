# LangChain 快速入门

> 本文基于 LangChain 官方文档整理：<https://docs.langchain.com/oss/python/langchain/quickstart>
>
> LangChain 是用于构建 **LLM 应用 / 智能体（Agent）** 的开源框架。新版以 `create_agent` 为核心 API，几行代码即可搭建一个能调用工具、带记忆的智能体。

---

## 一、核心概念

一个智能体（Agent）由三部分组成：

| 组件 | 说明 |
| --- | --- |
| **Model（模型）** | 大语言模型，负责推理和决策。通过 `init_chat_model()` 初始化，支持 OpenAI、Gemini、Claude、Ollama、Bedrock、HuggingFace 等多家供应商 |
| **Tools（工具）** | 用 `@tool` 装饰的普通 Python 函数，让模型可以与外部世界交互（查天气、抓网页、查数据库等） |
| **System Prompt（系统提示词）** | 指导智能体的角色与行为边界 |

此外两个关键能力：

- **Memory（记忆）**：通过 `checkpointer`（如 `InMemorySaver`）+ `thread_id` 在多轮对话间保留上下文。
- **循环推理（ReAct）**：`create_agent` 内部会让模型"思考 → 调用工具 → 观察结果 → 再思考"，自动循环直到得出最终答案。

---

## 二、安装

需要 Python 环境，并安装 `langchain`（以及可选的 `deepagents`）：

```bash
# 使用 uv
uv add langchain deepagents

# 或使用 pip
pip install -U langchain deepagents
```

然后配置所选供应商的 API Key（以环境变量形式），例如：

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 三、最小示例：5 分钟跑通一个 Agent

```python
from langchain.agents import create_agent

def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"

agent = create_agent(
    model="claude-sonnet-4-6",          # 也可写 "openai:gpt-5.5"、"google_genai:gemini-2.5-flash-lite" 等
    tools=[get_weather],
    system_prompt="You are a helpful assistant",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]}
)
print(result["messages"][-1].content_blocks)
```

要点：

1. `model` 用 `"供应商:模型名"` 字符串即可，框架自动选择对应的集成。
2. 工具就是带 **docstring 类型注解** 的普通函数——docstring 会作为工具说明告诉模型何时调用它。
3. 输入是消息列表 `{"messages": [...]}`，输出从 `result["messages"][-1]` 取最后一条回复。

### 不同供应商的写法对比

```python
# OpenAI
create_agent(model="openai:gpt-5.5", tools=[get_weather], system_prompt="...")

# Google Gemini
create_agent(model="google_genai:gemini-2.5-flash-lite", tools=[get_weather], system_prompt="...")

# Ollama（本地模型）
create_agent(model="ollama:devstral-2", tools=[get_weather], system_prompt="...")

# AWS Bedrock（需显式指定 provider）
create_agent(
    model="anthropic.claude-3-5-sonnet-20240620-v1:0",
    model_provider="bedrock_converse",
    tools=[get_weather],
    system_prompt="...",
)
```

---

## 四、进阶示例：带工具 + 记忆的研究型 Agent

下面是一个完整可运行示例：定义一个抓取网页文本的工具，初始化模型，加上记忆，让 Agent 回答关于《了不起的盖茨比》全文的问题。

```python
import urllib.error
import urllib.request

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

SYSTEM_PROMPT = """You are a literary data assistant.

## Capabilities

- `fetch_text_from_url`: loads document text from a URL into the conversation.
Do not guess line counts or positions—ground them in tool results from the saved file."""


@tool
def fetch_text_from_url(url: str) -> str:
    """Fetch the document from a URL."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
    except urllib.error.URLError as e:
        return f"Fetch failed: {e}"
    return raw.decode("utf-8", errors="replace")


# 1) 用 init_chat_model 做更精细的模型配置
model = init_chat_model(
    "claude-sonnet-4-6",
    temperature=0.5,
    timeout=600,
    max_tokens=25000,
    streaming=True,
)

# 2) 记忆：检查点保存器
checkpointer = InMemorySaver()

# 3) 组装 Agent
agent = create_agent(
    model=model,
    tools=[fetch_text_from_url],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

content = "请抓取 https://www.gutenberg.org/files/64317/64317-0.txt 并统计包含 'Gatsby' 的行数，再给出两句话的简介。"

# 4) 调用时通过 thread_id 关联同一会话，从而拥有记忆
result = agent.invoke(
    {"messages": [{"role": "user", "content": content}]},
    config={"configurable": {"thread_id": "great-gatsby-lc"}},
)
print(result["messages"][-1].content_blocks)
```

### `create_agent` vs `init_chat_model`

- `model="claude-sonnet-4-6"` 这种**字符串简写**适合快速开始。
- `init_chat_model(...)` 返回一个模型对象，可设置 `temperature`、`timeout`、`max_tokens`、`streaming` 等参数后再传给 `create_agent`，适合生产环境精细控制。

### 记忆的工作方式

- `checkpointer=InMemorySaver()` 把每轮对话状态存在内存中。
- 调用时传 `config={"configurable": {"thread_id": "xxx"}}`。
- **相同 `thread_id`** 的多次 `invoke` 会共享历史（实现多轮记忆）；**不同 `thread_id`** 则相互隔离。
- 生产环境可换成持久化的 checkpointer（如基于数据库的实现）。

---

## 五、create_agent vs Deep Agents

LangChain 还提供 `deepagents` 包，用 `create_deep_agent` 创建"深度智能体"：

| | `create_agent`（LangChain） | `create_deep_agent`（Deep Agents） |
| --- | --- | --- |
| 定位 | 细粒度可控的基础智能体 | 开箱即用、能力更强 |
| 内置能力 | 需自行实现高级功能 | 内置任务规划、文件系统工具（grep / read_file）、子智能体派生等 |
| 适用 | 需要精确控制每一步 | 复杂任务、希望最少配置获得最大能力 |

两者的模型配置方式完全一致，可以无缝切换。

---

## 六、可观测性（LangSmith）

通过设置环境变量即可开启 **LangSmith** 追踪，查看每一步的模型调用、工具调用与中间推理：

```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="..."
```

---

## 七、关键 API 速查

| API | 作用 |
| --- | --- |
| `create_agent(model, tools, system_prompt, checkpointer=...)` | 创建智能体 |
| `init_chat_model(name, temperature, max_tokens, streaming, ...)` | 初始化/配置聊天模型 |
| `@tool` | 把函数注册为工具 |
| `InMemorySaver()` | 内存型记忆检查点 |
| `agent.invoke({"messages": [...]}, config={...})` | 同步调用智能体 |
| `result["messages"][-1].content_blocks` | 取最终回复内容 |

---

# 面试问答

### Q1. 简述 LangChain 中一个 Agent 的核心组成。
**答：** 三部分——**Model**（负责推理决策的 LLM）、**Tools**（用 `@tool` 装饰的函数，提供与外界交互的能力）、**System Prompt**（定义角色与行为）。再配合 **Memory（checkpointer + thread_id）** 即可实现多轮对话。智能体内部按 ReAct 模式循环"推理→调用工具→观察→再推理"直到产出答案。

### Q2. `@tool` 装饰器的作用是什么？为什么函数的 docstring 和类型注解很重要？
**答：** `@tool` 把普通 Python 函数包装成 LLM 可识别和调用的工具。模型本身并不"看到"函数体，它依据**函数名、参数类型注解、docstring** 来判断这个工具做什么、何时调用、传什么参数。因此清晰的 docstring 与准确的类型注解直接决定模型能否正确调用工具。

### Q3. `create_agent` 里 `model` 参数为什么可以直接传字符串，又可以传对象？两者区别？
**答：** 传字符串（如 `"openai:gpt-5.5"`）是快捷写法，框架按 `"供应商:模型名"` 自动加载对应集成，适合快速上手。传对象则是先用 `init_chat_model()` 配置好 `temperature`、`timeout`、`max_tokens`、`streaming` 等参数再传入，适合需要精细控制的生产场景。

### Q4. LangChain 的记忆（Memory）是怎么实现的？`thread_id` 起什么作用？
**答：** 通过 `checkpointer`（如 `InMemorySaver`）保存对话状态，并在 `invoke` 时用 `config={"configurable": {"thread_id": "..."}}` 标识会话。**相同 thread_id** 的多次调用共享历史，从而具备多轮记忆；**不同 thread_id** 相互隔离。生产环境可替换为数据库支持的持久化 checkpointer。

### Q5. `init_chat_model` 中 `temperature`、`max_tokens`、`timeout`、`streaming` 各控制什么？
**答：**
- `temperature`：采样随机性，越低越确定/保守，越高越发散有创意。
- `max_tokens`：单次生成的最大 token 数，控制回复长度与成本上限。
- `timeout`：请求超时时间（秒），防止长任务无限等待。
- `streaming`：是否流式返回，开启后可边生成边接收，提升交互体验。

### Q6. `create_agent` 与 `create_deep_agent`（Deep Agents）有什么区别？如何选型？
**答：** `create_agent` 是基础智能体，可控性强但高级功能需自己实现；`create_deep_agent` 内置任务规划、文件系统工具（grep/read_file）、子智能体派生等，能"最少配置获得最大能力"。简单/需精确控制每一步选前者；复杂多步、希望开箱即用选后者。两者模型配置一致，可平滑切换。

### Q7. 如何从 `agent.invoke` 的返回值取出最终回复？
**答：** 返回值是一个含 `messages` 列表的字典，最后一条即最终回复：`result["messages"][-1].content_blocks`（或 `.content`）。中间还会包含模型的工具调用消息与工具返回消息，可用于调试和追踪。

### Q8. LangChain 如何切换不同模型供应商？需要改多少代码？
**答：** 基本只改 `model` 字符串即可，如从 `"claude-sonnet-4-6"` 换成 `"openai:gpt-5.5"` 或 `"ollama:devstral-2"`（本地模型）。部分供应商（如 AWS Bedrock、HuggingFace）需额外指定 `model_provider`。工具、系统提示、调用逻辑都无需改动，这正是 LangChain 统一抽象的价值。

### Q9. 生产环境中如何对 Agent 进行可观测/调试？
**答：** 集成 **LangSmith**，设置 `LANGSMITH_TRACING=true` 和 `LANGSMITH_API_KEY` 环境变量后，可追踪每一步的模型调用、工具调用、输入输出与中间推理链路，便于排查"为什么调用/没调用某工具""哪一步出错"。

### Q10. Agent 内部的执行循环（ReAct）大致是怎样的？
**答：** 模型收到用户消息后判断是否需要工具；若需要则发出工具调用（tool call），框架执行对应函数并把结果作为新消息回填；模型基于工具结果继续推理，可能再次调用工具，如此循环，直到模型认为信息足够、给出最终自然语言回答为止。`create_agent` 已封装好这一循环，开发者无需手写。
