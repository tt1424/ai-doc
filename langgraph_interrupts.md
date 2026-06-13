# LangGraph 中断机制（Interrupts）完整指南

> 整理自 LangGraph 官方文档：https://docs.langchain.com/oss/python/langgraph/interrupts

---

## 一、核心概念

**Interrupt（中断）** 是 LangGraph 的暂停/恢复机制，允许在图执行过程中暂停，等待外部输入（人工审批、用户输入等），然后继续执行。

这类模式叫做 **Human-in-the-Loop（人在循环中）**。

### 三个必要条件

1. **Checkpointer** — 用于持久化图的状态
2. **thread_id** — 标识哪个对话线程需要恢复
3. **interrupt() 调用** — 在节点中标记暂停点，传入 JSON 可序列化的值

### 执行流程

```
graph.invoke() 触发
       ↓
节点内执行 interrupt("提示信息")
       ↓
图暂停，状态通过 checkpointer 保存
       ↓
interrupt 的值返回给调用者（在 __interrupt__ 字段里）
       ↓
等待……（无限期）
       ↓
graph.invoke(Command(resume=用户输入), config)
       ↓
interrupt() 的返回值 = 用户输入的内容
       ↓
节点继续执行，图恢复运行
```

---

## 二、基础用法

### 最简单的中断节点

```python
from langgraph.types import interrupt

def approval_node(state: State):
    # 暂停，把问题展示给外部
    approved = interrupt("Do you approve this action?")

    # resume 之后，approved 就是 Command(resume=...) 传入的值
    return {"approved": approved}
```

### 恢复执行（v1，默认）

```python
from langgraph.types import Command

config = {"configurable": {"thread_id": "thread-1"}}

# 第一次调用，触发中断
result = graph.invoke({"input": "data"}, config=config)
print(result["__interrupt__"])
# > [Interrupt(value='Do you approve this action?')]

# 恢复执行，传入用户的回答
graph.invoke(Command(resume=True), config=config)
```

### 恢复执行（v2，LangGraph >= 1.1）

```python
# 第一次调用
result = graph.invoke({"input": "data"}, config=config, version="v2")
print(result.interrupts)
# > (Interrupt(value='Do you approve this action?'),)

# 恢复
graph.invoke(Command(resume=True), config=config, version="v2")
```

---

## 三、常见使用场景

### 场景 1：审批工作流

暂停执行，等待人工批准后再继续（比如转账、发邮件前确认）。

```python
from typing import Literal, Optional, TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class ApprovalState(TypedDict):
    action_details: str
    status: Optional[Literal["pending", "approved", "rejected"]]


def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
    decision = interrupt({
        "question": "Approve this action?",
        "details": state["action_details"],
    })
    # decision 是 True/False，据此决定下一个节点
    return Command(goto="proceed" if decision else "cancel")


def proceed_node(state: ApprovalState):
    return {"status": "approved"}

def cancel_node(state: ApprovalState):
    return {"status": "rejected"}


builder = StateGraph(ApprovalState)
builder.add_node("approval", approval_node)
builder.add_node("proceed", proceed_node)
builder.add_node("cancel", cancel_node)
builder.add_edge(START, "approval")
builder.add_edge("proceed", END)
builder.add_edge("cancel", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

config = {"configurable": {"thread_id": "approval-123"}}

# 触发中断
initial = graph.invoke(
    {"action_details": "Transfer $500", "status": "pending"},
    config=config,
)
print(initial["__interrupt__"])

# 恢复，传入 True 表示同意
resumed = graph.invoke(Command(resume=True), config=config)
print(resumed["status"])  # -> "approved"
```

---

### 场景 2：人工审核并编辑内容

LLM 生成内容后，让人工审查并修改，再继续。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class ReviewState(TypedDict):
    generated_text: str


def review_node(state: ReviewState):
    updated = interrupt({
        "instruction": "Review and edit this content",
        "content": state["generated_text"],
    })
    return {"generated_text": updated}


builder = StateGraph(ReviewState)
builder.add_node("review", review_node)
builder.add_edge(START, "review")
builder.add_edge("review", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "review-42"}}

# 触发中断
initial = graph.invoke({"generated_text": "Initial draft"}, config=config)
print(initial["__interrupt__"])

# 恢复，传入修改后的内容
final_state = graph.invoke(
    Command(resume="Improved draft after review"),
    config=config,
)
print(final_state["generated_text"])
```

---

### 场景 3：工具调用前中断（在工具函数内部）

在工具函数内部使用 `interrupt()`，让用户在真正执行前确认。

```python
from langchain.tools import tool
from langgraph.types import Command, interrupt


@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient."""
    response = interrupt({
        "action": "send_email",
        "to": to,
        "subject": subject,
        "body": body,
        "message": "Approve sending this email?",
    })

    if response.get("action") == "approve":
        # 可以在 resume 时修改参数
        final_to = response.get("to", to)
        final_subject = response.get("subject", subject)
        print(f"Sending email to {final_to}, subject: {final_subject}")
        return f"Email sent to {final_to}"

    return "Email cancelled by user"
```

---

### 场景 4：循环验证用户输入

不断请求输入，直到数据合法为止。

```python
from typing import TypedDict
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt


class FormState(TypedDict):
    age: int | None


def get_age_node(state: FormState):
    prompt = "What is your age?"

    while True:
        answer = interrupt(prompt)

        if isinstance(answer, int) and answer > 0:
            return {"age": answer}

        # 输入不合法，更新提示重新问
        prompt = f"'{answer}' is not a valid age. Please enter a positive number."


builder = StateGraph(FormState)
builder.add_node("collect_age", get_age_node)
builder.add_edge(START, "collect_age")
builder.add_edge("collect_age", END)

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)
config = {"configurable": {"thread_id": "form-1"}}

# 第一次触发
first = graph.invoke({"age": None}, config=config)

# 传入非法值，继续中断
retry = graph.invoke(Command(resume="thirty"), config=config)

# 传入合法值，结束
final = graph.invoke(Command(resume=30), config=config)
print(final["age"])  # -> 30
```

---

### 场景 5：并行分支同时中断

多个并行节点都触发了中断，需要用 ID 映射来一起恢复。

```python
from typing import Annotated, TypedDict
import operator
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command, interrupt


class State(TypedDict):
    vals: Annotated[list[str], operator.add]


def node_a(state):
    answer = interrupt("question_a")
    return {"vals": [f"a:{answer}"]}

def node_b(state):
    answer = interrupt("question_b")
    return {"vals": [f"b:{answer}"]}


graph = (
    StateGraph(State)
    .add_node("a", node_a)
    .add_node("b", node_b)
    .add_edge(START, "a")
    .add_edge(START, "b")
    .add_edge("a", END)
    .add_edge("b", END)
    .compile(checkpointer=InMemorySaver())
)

config = {"configurable": {"thread_id": "1"}}

# 触发，两个节点都中断
interrupted_result = graph.invoke({"vals": []}, config)

# 一次性恢复所有中断，用 ID 做映射
resume_map = {
    i.id: f"answer for {i.value}"
    for i in interrupted_result["__interrupt__"]
}
result = graph.invoke(Command(resume=resume_map), config)
print(result)
```

---

## 四、调试用途：静态断点

不需要 `interrupt()` 函数，直接在编译时指定断点节点：

```python
# 编译时设置断点
graph = builder.compile(
    interrupt_before=["node_a"],        # 在 node_a 执行前暂停
    interrupt_after=["node_b", "node_c"],  # 在 node_b、node_c 执行后暂停
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": "debug-1"}}

# 运行到断点
graph.invoke(inputs, config=config)

# 继续执行（传 None 即可）
graph.invoke(None, config=config)
```

适合调试场景，逐步检查每个节点执行后的状态。

---

## 五、流式输出 + 中断结合

```python
from langgraph.types import Command
from langchain_core.messages import AIMessageChunk

async for chunk in graph.astream(
    initial_input,
    stream_mode=["messages", "updates"],
    subgraphs=True,
    config=config,
    version="v2",
):
    if chunk["type"] == "messages":
        msg, _ = chunk["data"]
        if isinstance(msg, AIMessageChunk) and msg.content:
            print(msg.content, end="", flush=True)  # 流式输出

    elif chunk["type"] == "updates":
        if "__interrupt__" in chunk["data"]:
            # 检测到中断，获取用户输入
            interrupt_info = chunk["data"]["__interrupt__"][0].value
            user_response = input(f"\n[需要输入] {interrupt_info}: ")
            initial_input = Command(resume=user_response)
            break
```

---

## 六、重要注意事项

### ❌ 不要用 try/except 包裹 interrupt()

```python
# 错误写法！
def bad_node(state):
    try:
        answer = interrupt("question")  # interrupt 内部会抛出异常来暂停
    except Exception:
        pass  # 这里会吞掉暂停信号，导致中断失效
```

### ✅ 正确写法

```python
def good_node(state):
    answer = interrupt("question")  # 直接调用，不包裹
    return {"result": answer}
```

### 其他注意点

| 注意事项 | 说明 |
|---------|------|
| 调用顺序要一致 | 同一节点内多次 `interrupt()` 的顺序必须固定，恢复时按索引匹配 |
| 只传 JSON 可序列化的值 | 不能传函数、类实例等不可序列化对象 |
| interrupt() 前的代码会重新执行 | 恢复时节点从头开始，`interrupt()` 之前的代码会再跑一遍，注意副作用 |
| 子图中的中断 | 父图和子图节点恢复时都从各自的起点重新执行 |

---

## 七、快速对比：interrupt() vs 静态断点

| | `interrupt()` | `interrupt_before/after` |
|--|---------------|--------------------------|
| 用途 | 生产环境 Human-in-the-Loop | 开发调试 |
| 触发方式 | 代码中主动调用 | 编译时配置 |
| 传递数据 | 可以传任意 JSON 值给外部 | 只是暂停，不传数据 |
| 恢复方式 | `Command(resume=用户输入)` | `invoke(None, config)` |

---

## 八、关键 API 速查

```python
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver

# 1. 在节点内暂停
value = interrupt("传给外部的信息")

# 2. 编译时挂载 checkpointer
graph = builder.compile(checkpointer=MemorySaver())

# 3. 触发执行（会在 interrupt() 处暂停）
result = graph.invoke(input, config={"configurable": {"thread_id": "xxx"}})

# 4. 查看中断信息
print(result["__interrupt__"])  # v1
print(result.interrupts)        # v2

# 5. 恢复执行
graph.invoke(Command(resume=用户输入), config=config)

# 6. 调试断点（编译时）
graph = builder.compile(
    interrupt_before=["node_name"],
    checkpointer=checkpointer,
)
```
