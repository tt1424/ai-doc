# LangChain 内置中间件（Built-in Middleware）完整参考

> 来源：https://docs.langchain.com/oss/python/langchain/middleware/built-in

LangChain 提供了 15+ 个开箱即用的中间件组件，覆盖生产环境中常见的 Agent 需求。

所有中间件均通过 `create_agent()` 的 `middleware` 参数注入：

```python
from langchain.agents import create_agent
from langchain.agents.middleware import [中间件名]

agent = create_agent(
    model=llm,
    tools=[your_tools],
    middleware=[中间件类(配置参数)]
)
```

---

## 一、对话管理类

### 1. Summarization Middleware（对话摘要中间件）

**用途**：当对话历史接近 token 上限时，自动对历史内容进行摘要压缩，防止超出上下文窗口。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `model` | 用于生成摘要的模型 |
| `trigger` | 触发条件（按 token 数、消息条数或比例）|
| `keep` | 压缩后保留的上下文策略 |
| `token_counter` | 自定义 token 计数函数 |

**适用场景**：长对话、多轮对话、上下文窗口管理。

---

### 2. Context Editing Middleware（上下文编辑中间件）

**用途**：在长对话中清理旧的工具调用结果，释放 token 空间。核心策略为 `ClearToolUsesEdit`。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `trigger` | token 阈值，默认 100,000 |
| `keep` | 保留最近几条工具结果 |
| `placeholder` | 替换被清除内容的占位文本 |
| `exclude_tools` | 不参与清除的工具列表 |

---

## 二、安全与审批类

### 3. Human-in-the-Loop Middleware（人工审批中间件）

**用途**：在执行特定工具前暂停，等待人工审核确认后再继续。

**关键特性**：
- 需要配合 `checkpointer` 使用（用于保存暂停状态）
- 可配置哪些工具需要审批
- 支持的决策：approve（批准）/ edit（修改参数）/ reject（拒绝）

**适用场景**：高风险操作、合规工作流、金融交易审批。

---

### 4. PII Detection Middleware（个人信息检测中间件）

**用途**：检测并处理输入/输出中的敏感个人信息。

**内置检测类型**：email、credit_card、IP 地址、MAC 地址、URL

**处理策略**：

| 策略 | 说明 |
|---|---|
| `block` | 直接拦截，不传递 |
| `redact` | 删除敏感内容 |
| `mask` | 用 * 遮盖 |
| `hash` | 哈希化处理 |

**作用范围**：input（用户输入）、output（模型输出）、tool results（工具结果）

支持自定义正则表达式或自定义函数扩展检测规则。

---

## 三、限流与容错类

### 5. Model Call Limit Middleware（模型调用次数限制）

**用途**：限制 LLM 的调用次数，防止失控的 Agent 无限循环。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `thread_limit` | 整个会话的最大调用次数 |
| `run_limit` | 单次 invoke 的最大调用次数 |
| `exit_behavior` | `'end'`（优雅结束）或 `'error'`（抛异常）|

---

### 6. Tool Call Limit Middleware（工具调用次数限制）

**用途**：限制工具的调用次数，保护高成本或有频率限制的 API。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `thread_limit` | 会话级别最大次数 |
| `run_limit` | 单次运行最大次数 |
| `exit_behavior` | `'continue'`、`'error'` 或 `'end'` |

支持全局限制或针对特定工具单独配置。

---

### 7. Model Fallback Middleware（模型降级备援）

**用途**：当主模型调用失败时，自动切换到备用模型。

**特性**：
- 可链式配置多个模型，按优先级依次尝试
- 实现供应商冗余、成本优化、故障容错

---

### 8. Tool Retry Middleware（工具重试中间件）

**用途**：工具调用失败时自动重试，采用指数退避策略。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `max_retries` | 最大重试次数，默认 2（共 3 次）|
| `backoff_factor` | 退避倍数，默认 2.0 |
| `initial_delay` | 初始延迟，默认 1.0 秒 |
| `jitter` | 随机抖动 ±25%，防止同时重试 |

失败后可选择返回错误消息或抛出异常。

---

### 9. Model Retry Middleware（模型重试中间件）

**用途**：模型 API 调用失败时自动重试，与工具重试类似但针对 LLM 调用。

**额外特性**：
- 支持异常过滤（指定哪些异常触发重试）
- 自定义错误消息格式
- 支持常数退避或指数退避
- 默认返回错误消息而非抛出异常

---

## 四、工具增强类

### 10. LLM Tool Selector Middleware（LLM 工具选择器）

**用途**：当 Agent 拥有大量工具时，先用 LLM 筛选出本次最相关的工具，减少传给模型的 token 数量。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `max_tools` | 每次最多选择的工具数量 |
| `always_include` | 始终包含、不参与筛选的工具 |

---

### 11. LLM Tool Emulator（LLM 工具模拟器）

**用途**：用 LLM 模拟工具的执行结果，用于测试和开发阶段无需真实工具。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `tools` | 要模拟的工具列表，None 表示模拟全部 |
| `model` | 用于生成模拟响应的模型 |

**适用场景**：单元测试、开发原型验证。

---

### 12. To-Do List Middleware（待办列表中间件）

**用途**：自动为 Agent 提供 `write_todos` 工具，让 Agent 能够规划任务和追踪进度。

**特性**：
- 支持自定义 system prompt 和工具描述
- 让 Agent 具备任务拆解和自我管理能力

---

## 五、文件与系统类

### 13. Shell Tool Middleware（Shell 工具中间件）

**用途**：让 Agent 能够执行 Shell 命令。

**执行策略**：

| 策略 | 说明 |
|---|---|
| `HostExecutionPolicy` | 完全访问宿主机 |
| `DockerExecutionPolicy` | 在 Docker 容器中隔离执行 |
| `CodexSandboxExecutionPolicy` | 受限系统调用的沙箱环境 |

**特性**：持久化 session、启动/关闭命令、输出脱敏规则。

---

### 14. File Search Middleware（文件搜索中间件）

**用途**：为 Agent 提供文件搜索能力（Glob 和 Grep 工具）。

**关键参数**：

| 参数 | 说明 |
|---|---|
| `root_path` | 搜索根目录（必填）|
| `use_ripgrep` | 使用 ripgrep 加速，默认 true |
| `max_file_size_mb` | 文件大小限制，默认 10MB |

**输出模式**：文件列表、匹配内容、匹配数量。

---

### 15. Filesystem Middleware（文件系统中间件，深度 Agent）

**用途**：为 Agent 提供完整的文件系统操作能力。

**提供的工具**：`ls`、`read_file`、`write_file`、`edit_file`

**存储模式**：
- 临时状态（Ephemeral）：运行结束后清除
- 持久化（StoreBackend）：跨次保存
- 支持 `CompositeBackend` 按路由分配不同存储后端

---

## 六、多 Agent 类

### 16. Subagent Middleware（子 Agent 中间件，深度 Agent）

**用途**：让主 Agent 能够派发子任务给专门的子 Agent 处理。

**配置项**：名称、描述、system prompt、工具列表、独立模型

**特性**：
- 上下文隔离，子 Agent 独立运行
- 默认子 Agent 继承主 Agent 的工具
- 高级用法：通过 `CompiledSubAgent` 传入自定义 LangGraph 图

---

## 七、厂商专属中间件

| 厂商 | 中间件 |
|---|---|
| Anthropic | Prompt 缓存、Bash 工具、文本编辑器、记忆工具 |
| AWS | Bedrock Prompt 缓存 |
| OpenAI | 内容审核 |

---

## 总结：按使用频率分类

| 类别 | 推荐中间件 |
|---|---|
| 新手必学 | Model Call Limit、Tool Retry、Model Fallback |
| 生产必备 | PII Detection、Human-in-the-Loop、Summarization |
| 性能优化 | LLM Tool Selector、Context Editing |
| 高级功能 | Subagent、Filesystem、Shell Tool |
