# LangGraph 快速入门

> 本文基于 LangGraph 官方文档整理：<https://docs.langchain.com/oss/python/langgraph/quickstart>
>
> LangGraph 是用于构建**有状态、可控的智能体（Agent）应用**的框架。相比 LangChain 的 `create_agent`（高度封装），LangGraph 让你把智能体显式建模成一张**有向图**：节点（Node）做计算，边（Edge）控制流转，状态（State）贯穿全程。适合需要精细控制循环、分支、人机协同的复杂场景。

---

## 一、核心概念

| 概念 | 说明 |
| --- | --- |
| **StateGraph** | 核心类，把工作流定义成由节点和边组成的有向图 |
| **State（状态）** | 一个 `TypedDict`，定义贯穿整个执行过程的数据结构（通常含消息列表） |
| **Node（节点）** | 普通 Python 函数，执行计算（如调用 LLM、执行工具），输入状态、返回对状态的更新 |
| **Edge（边）** | 连接节点，决定执行流向；**普通边**固定流转，**条件边**根据逻辑动态路由 |
| **START / END** | 特殊标记，分别表示图的入口与出口 |
| **compile()** | 把图定义编译成可执行的智能体 |
| **Reducer（归约器）** | 定义状态字段如何更新，如 `operator.add` / `add_messages` 让新消息**追加**而非覆盖 |

LangGraph 提供两套 API：

- **Graph API**：显式定义节点和边，可视化强、可控性高（推荐入门理解）。
- **Functional API**：用 `@task` / `@entrypoint` 装饰器以普通控制流（while 循环等）编写，更贴近常规 Python。

---

## 二、安装

```bash
pip install -U langgraph langchain
```

并配置所选模型供应商的 API Key，例如：

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## 三、Graph API 完整示例：计算器 Agent

下面构建一个能调用加/乘/除工具的算术智能体。它的核心是经典的 **ReAct 循环**：LLM 判断是否调用工具 → 执行工具 → 把结果回填 → LLM 再判断，直到无需工具为止。

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
import operator
from typing import Literal
from langgraph.graph import StateGraph, START, END


# 初始化模型
model = init_chat_model("claude-sonnet-4-6", temperature=0)


# 定义工具
@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`."""
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`."""
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`."""
    return a / b


tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


# 定义状态：messages 用 operator.add 做 reducer，保证追加而非覆盖
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int


# 节点 1：LLM 决策（是否调用工具）
def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }


# 节点 2：执行工具调用
def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# 条件路由：最后一条消息有 tool_calls 就去执行工具，否则结束
def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue or stop"""
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"
    return END


# 构建并编译图
agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()

# 调用
messages = [HumanMessage(content="Add 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()
```

### 这张图的结构

```
START → llm_call → (should_continue?) ─┬─→ tool_node → llm_call  (循环)
                                       └─→ END
```

- `add_edge(START, "llm_call")`：入口固定进入 LLM 节点。
- `add_conditional_edges("llm_call", should_continue, [...])`：LLM 之后根据 `should_continue` 的返回值动态决定去 `tool_node` 还是 `END`。
- `add_edge("tool_node", "llm_call")`：工具执行完回到 LLM，形成循环。

---

## 四、Functional API 完整示例

同样的逻辑，用 `@task`（封装一个工作单元）和 `@entrypoint`（封装整个流程）写成普通 while 循环，更直观：

```python
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langgraph.graph import add_messages
from langchain.messages import SystemMessage, HumanMessage, ToolCall
from langchain_core.messages import BaseMessage
from langgraph.func import entrypoint, task


model = init_chat_model("claude-sonnet-4-6", temperature=0)


@tool
def multiply(a: int, b: int) -> int:
    """Multiply `a` and `b`."""
    return a * b


@tool
def add(a: int, b: int) -> int:
    """Adds `a` and `b`."""
    return a + b


@tool
def divide(a: int, b: int) -> float:
    """Divide `a` and `b`."""
    return a / b


tools = [add, multiply, divide]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


@task
def call_llm(messages: list[BaseMessage]):
    """LLM decides whether to call a tool or not"""
    return model_with_tools.invoke(
        [
            SystemMessage(
                content="You are a helpful assistant tasked with performing arithmetic on a set of inputs."
            )
        ]
        + messages
    )


@task
def call_tool(tool_call: ToolCall):
    """Performs the tool call"""
    tool = tools_by_name[tool_call["name"]]
    return tool.invoke(tool_call)


@entrypoint()
def agent(messages: list[BaseMessage]):
    model_response = call_llm(messages).result()

    while True:
        if not model_response.tool_calls:
            break

        # 多个工具调用可并行发起
        tool_result_futures = [
            call_tool(tool_call) for tool_call in model_response.tool_calls
        ]
        tool_results = [fut.result() for fut in tool_result_futures]
        messages = add_messages(messages, [model_response, *tool_results])
        model_response = call_llm(messages).result()

    messages = add_messages(messages, model_response)
    return messages


# 调用（流式输出每一步更新）
messages = [HumanMessage(content="Add 3 and 4.")]
for chunk in agent.stream(messages, stream_mode="updates"):
    print(chunk)
    print("\n")
```

要点：

- `@task` 返回一个 future，用 `.result()` 取值；多个 task 可并发执行后再统一收集。
- `@entrypoint()` 是整个智能体的入口，内部就是普通 Python 控制流。
- `add_messages(old, new)` 负责把新消息正确合并进历史。

---

## 五、Graph API vs Functional API

| | Graph API | Functional API |
| --- | --- | --- |
| 写法 | 显式 `add_node` / `add_edge` / 条件边 | `@task` / `@entrypoint` + 普通控制流 |
| 心智模型 | 有向图 | 函数与循环 |
| 优势 | 结构清晰、易可视化、便于人机协同/断点 | 上手快、贴近常规 Python |
| 适用 | 复杂分支、需要图层面控制 | 流程相对线性、偏好命令式写法 |

两者底层一致，都支持记忆、流式、检查点。

---

## 六、Reducer：为什么需要 `operator.add` / `add_messages`

State 是一个字典，节点返回的更新默认会**覆盖**同名字段。但对 `messages` 这种需要不断累积的字段，我们希望**追加**。这就是 reducer 的作用：

```python
messages: Annotated[list[AnyMessage], operator.add]
```

`Annotated[..., operator.add]` 告诉 LangGraph：当节点返回新的 `messages` 时，用 `operator.add`（列表拼接）合并到现有列表，而不是替换。`add_messages` 是更智能的 reducer，能按消息 id 去重/更新。

---

## 七、记忆与持久化（扩展）

给 `compile()` 传入 `checkpointer` 即可让图具备跨轮记忆与断点续跑能力：

```python
from langgraph.checkpoint.memory import InMemorySaver

checkpointer = InMemorySaver()
agent = agent_builder.compile(checkpointer=checkpointer)

# 调用时用 thread_id 标识会话
agent.invoke(
    {"messages": [HumanMessage(content="Add 3 and 4.")]},
    config={"configurable": {"thread_id": "1"}},
)
```

相同 `thread_id` 的多次调用共享状态历史；这也是实现**人机协同（human-in-the-loop）**、断点恢复、时间回溯的基础。

---

## 八、关键 API 速查

| API | 作用 |
| --- | --- |
| `StateGraph(StateSchema)` | 以状态结构创建图 |
| `.add_node(name, fn)` | 添加节点 |
| `.add_edge(a, b)` | 添加普通边（固定流转） |
| `.add_conditional_edges(src, router_fn, paths)` | 添加条件边（动态路由） |
| `START` / `END` | 图的入口 / 出口 |
| `.compile(checkpointer=...)` | 编译成可执行 agent |
| `agent.invoke(state, config=...)` | 同步执行 |
| `agent.stream(state, stream_mode="updates")` | 流式执行，逐步返回更新 |
| `Annotated[T, reducer]` | 为状态字段指定归约方式 |
| `@task` / `@entrypoint` | Functional API 的工作单元 / 入口 |

---

# 面试问答

### Q1. LangGraph 是什么？它和 LangChain 的 `create_agent` 有何区别？
**答：** LangGraph 是构建**有状态、可控**智能体的框架，把智能体显式建模成"节点+边+状态"的有向图。相比 `create_agent`（高度封装、几行搞定但难以干预内部流程），LangGraph 暴露了循环、分支、状态流转的每一步，适合需要精细控制、人机协同、断点续跑的复杂场景。实际上 `create_agent` 底层就是基于 LangGraph 构建的。

### Q2. 解释 StateGraph 中的 State、Node、Edge 三个核心概念。
**答：**
- **State**：一个 `TypedDict`，定义贯穿执行过程的共享数据（通常含 `messages`）。
- **Node**：普通函数，接收当前 state、返回对 state 的部分更新。
- **Edge**：连接节点决定流向。普通边（`add_edge`）固定跳转；条件边（`add_conditional_edges`）由路由函数的返回值动态决定下一个节点。

### Q3. 什么是 Reducer？为什么 `messages` 字段要用 `Annotated[list, operator.add]`？
**答：** Reducer 定义状态字段在被节点更新时如何合并。默认是**覆盖**，但消息历史需要**追加**。`Annotated[list[AnyMessage], operator.add]` 告诉 LangGraph 用列表拼接合并新旧消息，从而累积对话历史。`add_messages` 是更智能的 reducer，能按消息 id 去重和更新。

### Q4. 条件边（conditional edges）是怎么工作的？请结合计算器示例说明。
**答：** `add_conditional_edges("llm_call", should_continue, ["tool_node", END])` 表示从 `llm_call` 出来后调用 `should_continue` 路由函数。该函数检查最后一条消息是否含 `tool_calls`：有则返回 `"tool_node"`（去执行工具），没有则返回 `END`（结束）。这样就实现了"需要工具就调用、不需要就停止"的动态分支。

### Q5. 描述这个计算器 Agent 的完整执行循环（图结构）。
**答：** `START → llm_call`；`llm_call` 后经 `should_continue` 判断：若需工具则 `→ tool_node → llm_call`（回到 LLM 形成循环），否则 `→ END`。即 LLM 决策 → 执行工具 → 回填结果 → LLM 再决策，直到不再需要工具，本质是 ReAct 循环的图化表达。

### Q6. Graph API 和 Functional API 有什么区别？分别适合什么场景？
**答：** Graph API 用显式的 `add_node`/`add_edge`/条件边把流程画成图，结构清晰、易可视化、便于断点与人机协同，适合复杂分支。Functional API 用 `@task`/`@entrypoint` 加普通 while 循环写命令式代码，上手快、贴近常规 Python，适合流程较线性、偏好命令式写法的情况。两者底层一致，能力相同。

### Q7. `tool_node` 节点内部做了什么？`ToolMessage` 的作用是什么？
**答：** `tool_node` 遍历上一条消息里的 `tool_calls`，按名字找到对应工具并用其参数 `invoke` 执行，把每个结果包成 `ToolMessage`（带 `tool_call_id` 与对应的工具调用关联），返回到 state 的 `messages`。`ToolMessage` 是把工具执行结果回传给 LLM 的标准消息类型，LLM 据此继续推理。

### Q8. `compile()` 起什么作用？`checkpointer` 又解决了什么问题？
**答：** `compile()` 把图的定义转换成可执行对象（带 `invoke`/`stream` 等方法）。传入 `checkpointer`（如 `InMemorySaver`）后，图会在每一步保存状态快照，配合 `thread_id` 即可实现跨轮记忆、断点续跑、人机协同与"时间回溯"等能力。

### Q9. `invoke` 和 `stream` 有什么区别？`stream_mode="updates"` 是什么含义？
**答：** `invoke` 一次性运行到结束返回最终状态；`stream` 边执行边产出中间结果，利于实时观察与展示。`stream_mode="updates"` 表示每个节点执行后只产出**该步对状态的增量更新**（而非完整状态），便于逐步打印执行轨迹。

### Q10. Functional API 中 `@task` 返回的是什么？示例里多个工具调用是如何并行的？
**答：** `@task` 调用后返回一个 future（异步句柄），用 `.result()` 阻塞取值。示例中先对每个 `tool_call` 调用 `call_tool` 收集一批 future（`tool_result_futures`），此时它们可并发执行，再统一 `fut.result()` 收集结果。这样多个独立工具调用能并行，提升效率。
