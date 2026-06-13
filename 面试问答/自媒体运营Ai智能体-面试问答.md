# 自媒体运营 AI 智能体(LangGraph)· 面试问答

> 基于《自媒体运营Ai智能体》项目文档整理的面试题库。项目是用 **LangGraph 1.0** 为教育培训公司做的「AI 内容运营助手」:自动生成小红书配图文案 + 微信公众号技术文章,核心是 **Human-in-the-loop(人工选题/审稿)** 工作流。技术栈:LangGraph + FastAPI + PostgreSQL(Checkpointer)+ 豆包 1.8 + Doubao-Seedream 图片模型。
> 每题含「考察点」「参考回答」「加分项」,覆盖 LangGraph 核心、持久化、流式、并发、可观测性、鉴权、限流熔断等 30+ 高频考点。

---

## 一、项目与 LangGraph 架构

### Q1. 这个项目是做什么的?整体架构怎么分层?

**考察点**:项目全局认知。

**参考回答**:
为教育培训公司做的 **AI 内容运营助手**:根据用户喜欢的内容,自动生成技术干货文章(发公众号)和配图文案(发小红书),核心是带**人工介入**的自动化工作流。
分四层(为扩展性——换平台/换模型/加视频):
- **表现层(前端)**:运营人员交互(选题、审稿、看图);
- **接入层(FastAPI)**:处理 HTTP、WebSocket,业务入口;
- **核心编排层(LangGraph)**:系统大脑,定义状态机、节点逻辑、流转规则;
- **基础设施层**:PostgreSQL(业务数据 + LangGraph Checkpoints)、Model Provider(LLM + 图片生成)。

代码用**模块化单体(Modular Monolith)**:api / core / graph(state、nodes、edges、workflow)/ services(LLM、image、social 适配器)/ models。

---

### Q2. 这个工作流的节点和流转是怎么设计的?

**考察点**:状态机设计。

**参考回答**:
是一个**带循环的状态机**,核心节点:
1. `plan_topics`:LLM 生成 3-5 个选题;
2. **INTERRUPT(中断)**:等人工选题;
3. `write_draft`:根据选题写长文(若有反馈则参考反馈重写);
4. **INTERRUPT(中断)**:等人工审稿;
5. 条件分支——**Approve** 走 `extract_visuals`(提炼图片知识点)→ `generate_images` → END;**Reject** 带上修改意见**回退到 `write_draft`** 重写。

两个关键中断点等待人工介入,审稿驳回会循环改到满意为止。

**加分项**:能指出 LangGraph 1.0 用 `interrupt()` 函数实现中断,不再需要旧版的 `interrupt_before` 参数。

---

### Q3. 什么是 AgentState?它的作用是什么?

**考察点**:LangGraph 状态管理。

**参考回答**:
`AgentState` 是用 **TypedDict 定义的全局状态**,在各节点间传递数据。包含:`topic_direction`(初始方向)、`generated_topics`(AI 推荐选题)、`selected_topic`(用户选中)、`article_content`(文章)、`review_feedback`(修改意见)、`visual_points`(图片文案)、`image_urls`(图片链接)、`status`(状态)。

它就是工作流的"数据载体"——每个节点读取需要的字段、写回更新的字段,通过状态流转串起整个流程。`messages` 这类字段还能用 `Annotated[List, operator.add]` 实现追加而非覆盖。

---

### Q4. Human-in-the-loop 是怎么通过 API 实现的?

**考察点**:中断与恢复机制(核心)。

**参考回答**:
靠 **`thread_id` + 中断恢复**,三个核心接口:
- **POST /start**:接收 `topic_direction`,生成 `thread_id`,`ainvoke` 运行到第一个 `interrupt()`(选题生成完)暂停,返回 thread_id 和选题列表;
- **GET /state/{thread_id}**:`aget_state(config)` 取当前快照(给前端展示草稿/选题);
- **POST /resume/{thread_id}**:接收 action(select_topic/approve/reject)和 data,用 `ainvoke(Command(resume=value), config)` 从中断点恢复,运行到下一个中断或结束。

**关键点**:`ainvoke` 的返回值是"运行到流程走不动(中断或结束)为止"决定的;`config` 里的 `thread_id` 是恢复上下文的唯一标识。

**加分项**:human_review 节点不管同意还是拒绝**都会重新走一次**——拒绝时带 feedback 回到 write_draft 重写。

---

## 二、PostgreSQL 持久化(Checkpointer)

### Q5. 为什么要用 PostgreSQL 做持久化?LangGraph 是怎么做的?

**考察点**:状态持久化原理(高频)。

**参考回答**:
**目的**:让用户关掉浏览器、第二天回来还能从"选题后"继续"生成文案",上下文不丢。
LangGraph 用 **`AsyncPostgresSaver`(Checkpointer)** 自动序列化状态,不需要手动把每步存业务表。核心步骤:
1. 用官方 `AsyncPostgresSaver` 创建连接池得到 `_checkpointer`;
2. `workflow.compile(checkpointer=checkpointer)` 把它绑到图上;
3. graph 运行时**每个节点执行后状态自动写入** PostgreSQL;
4. 读取用 `graph.aget_state(config)`,按 thread_id 查。

启动时调 `setup_checkpointer()`,用 autocommit 连接执行 `setup()` 自动建表(因为 `CREATE INDEX CONCURRENTLY` 不能在事务块里跑)。

---

### Q6. Checkpointer 会建哪些表?为什么要把元数据和数据分开存?

**考察点**:存储结构设计理解(深挖)。

**参考回答**:
`setup()` 建 4 张表:
- **checkpoints**:检查点**元数据**(thread_id、checkpoint_id、父检查点 id、metadata),JSONB 轻量;
- **checkpoint_blobs**:**实际状态数据**,blob 字段是 BYTEA 二进制(pickle 序列化);
- **checkpoint_writes**:每个节点的写入记录;
- **checkpoint_migrations**:Schema 版本控制。

**分开存的好处**:
1. **查询效率**:查检查点列表不用加载大量数据;
2. **去重**:相同状态数据可被多个检查点引用;
3. **灵活性**:不同 channel(messages、values)分开存,增量更新只存变化的。

**加分项**:每条记录由 `(thread_id, checkpoint_id)` 唯一标识;checkpoints 里只存 blob 引用,不存实际数据。

---

### Q7. 为什么直接查 checkpoint_blobs 表看不到选题列表?

**考察点**:序列化理解。

**参考回答**:
因为数据是 **pickle 序列化后存成二进制**的,直接查 blob 字段看到的是 `\x80049563...` 一串十六进制,必须用 Python 反序列化才能还原。
正确查看方式:调 API `/workflow/state/{thread_id}`,或用 `graph.aget_state(config)` 拿 `state.values.get("generated_topics")`。

---

### Q8. 什么是连接池?为什么 1000 个用户不需要 1000 个连接?

**考察点**:连接池与并发理解(高频)。

**参考回答**:
**连接池(`psycopg_pool` 的 AsyncConnectionPool)** 预先建好一批连接放池子里,程序用时直接拿、用完归还,**不用每次重新握手**。Async 保证等数据库时不阻塞,连接池管理连接数防止压垮数据库、断了自动重连。

**1000 用户不需要 1000 连接的原因**:"用户在线" ≠ "数据库正在操作"。用户阅读、思考、打字时不占连接;一次 Checkpoint 存取只要几十毫秒;同一毫秒真正发请求的可能只有几十个。所以中小应用起始 `min_size=1~10`、`max_size=10` 就够;企业级 `min_size=20, max_size=100` 大概能抗 1000-1w QPS、日活 5000-2w。

---

## 三、流式输出(SSE)

### Q9. 流式输出是怎么实现的?astream 和 astream_events 有什么区别?

**考察点**:LangGraph 流式机制(高频)。

**参考回答**:
用 **SSE** 流式返回。两种流模式:
- **普通流 `astream`**:基于"状态更新",一个**节点收工**才告诉你结果(节点级);
- **事件流 `astream_events`**:基于"生命周期事件",监听每一步:`on_chain_start`(节点开始)、`on_chat_model_stream`(**LLM 正在吐字**,最关键)、`on_tool_start`、`on_chain_end`。

要实现 Token 级实时流式输出,必须用 `astream_events`,监听 `on_chat_model_stream` 事件把每个 token 实时 yield 给前端。服务端用 `StreamingResponse`,media_type=`text/event-stream`,响应头设 `X-Accel-Buffering: no` 禁用 Nginx 缓冲。

**好处**:减少 TTFT(首字延迟),用户实时看到文章生成过程。

---

### Q10. LLM 是用非流式调用的(ainvoke),为什么 astream_events 还能拿到 token 流?

**考察点**:流式底层原理。

**参考回答**:
因为 LangChain 的 `ChatOpenAI` **默认支持流式**,`astream_events()` 会自动监听底层的流式事件,即使节点里用的是 `ainvoke`,它也会把 LLM 调用变成 astream 模式从而捕获到 token 流。
**但建议显式把 LLM 调用改成 stream 模式**,方便项目维护、逻辑一目了然。

**加分项**:能说出前端用 `ReadableStream` 的 reader 循环读、按 `\n\n` 分割 SSE 消息、`data: ` 前缀解析 JSON,按 `type`(init/llm_token/update/done)分发回调。

---

## 四、子图、并发与可靠性

### Q11. 为什么引入 SubGraph 子图?子图和主图共享状态吗?Checkpointer 怎么管?

**考察点**:复杂工作流编排(高频深挖)。

**参考回答**:
**引入子图**:把选题、写作、配图拆成独立子图,支持复用和组合编排。比如"选题子图"可以加 RAG 提供选题 + LLM 提供选题 + 多人审核(组长、总监)。

**状态共享**:子图和主图用**同一个类型定义但不是同一个实例**。机制是:主图调子图时把当前 state 传给子图 → 子图对 state 的修改(`Command(update={...})`)被收集 → 子图结束后更新的 state 传回主图。所以是**流转共享**而非引用同一内存对象。

**Checkpointer**:**统一由主图管理,不要搞多个**(否则中断恢复容易冲突)。主图的 checkpointer 会记录完整执行路径,包括"主图→子图→子图内某节点"的嵌套位置,所以子图内的 `interrupt()` 也能正常工作和恢复。

---

### Q12. 图片批量生成怎么优化?同步 API 怎么改成异步并行?

**考察点**:异步并发(高频实战)。

**参考回答**:
图片生成原本是**串行**的,改成**并行**。但 Doubao-Seedream 不支持异步调用,所以用 **`run_in_executor` 把同步函数丢到线程池跑**,模拟异步:
```python
loop = asyncio.get_running_loop()
url = await loop.run_in_executor(None, self._generate_single_image_sync, prompt, size)
```
然后用 **`asyncio.gather`** 并发执行多张图:
```python
tasks = [self.generate_single_image(prompt=p, size=size) for p in visual_points]
image_urls = await asyncio.gather(*tasks)
```
多张配图从串行改并发,整体生成耗时缩减约 70%。

---

### Q13. 超时和重试是怎么做的?

**考察点**:容错设计。

**参考回答**:
- 每个节点配超时时间;
- LLM 调用失败**自动重试 + 指数退避**:第一次间隔 1s、第二次 2s、第三次 4s,依次翻倍。

指数退避避免失败时密集重试把下游打垮,给服务恢复时间。

---

### Q14. 限流和熔断有什么区别?分别保护谁?

**考察点**:稳定性设计(高频)。

**参考回答**:
- **限流(Rate Limit)**:保护**自己**。用户请求太多时"我忙不过来,你少来点",防止自己被压垮。用 SlowAPI `@limiter.limit("10/minute")`。
- **熔断(Circuit Breaker)**:保护**自己不被下游拖死**。调用下游(LLM/数据库/第三方)连续失败/超时时"它挂了,我不等了",快速失败走降级,不浪费资源干等。

**熔断 ≠ 服务挂了,熔断 = 走备用方案**(高速封了走国道)。熔断有三态:连续失败超阈值→**熔断打开**(直接走降级 0 秒返回)→30 秒后→**半开**(放一个请求试探)→成功则恢复。

**加分项**:企业级是多层防护——CDN/WAF(DDoS)→ API 网关(全局限流)→ 应用层(业务限流 + 熔断)→ 下游服务(LLM 自身限流)。

---

## 五、可观测性与成本

### Q15. 你是怎么追踪 LLM 的 Token 消耗和耗时的?

**考察点**:监控埋点设计(简历亮点)。

**参考回答**:
设计了一个 **`MetricsContext` 上下文管理器**,用 `with` 包裹节点逻辑,`__enter__` 记开始时间、`__exit__` 记结束算耗时,中间 `set_llm_usage(usage)` 记 token,最后把指标 append 到 state 的 `node_metrics`:
```python
with MetricsContext("my_node") as tracker:
    result, usage = await llm_service.call_with_metrics(...)
    tracker.set_llm_usage(usage)
return {..., "node_metrics": state.get("node_metrics", []) + [tracker.to_dict()]}
```
这样每个节点的 token、延迟、错误率都被采集。结合火山引擎定价(输入 0.8 元/百万 token、输出 2 元/百万、图片 0.25 元/张)做**成本核算**,为模型选型和资源调优提供数据。

---

### Q16. LangSmith 是干什么的?接入复杂吗?

**考察点**:全链路可观测性。

**参考回答**:
**LangSmith** 是 LangChain 官方的全链路追踪平台,**只需配 env 自动集成**(`LANGCHAIN_TRACING_V2=true` + API Key + Project)。
能统计:Graph 的流转路径、每个流程的耗时和 token、每个流程的调用结果、注入 graph 的 state 状态。配合 structlog 结构化日志 + request_id 关联,把问题定位从小时级压缩到分钟级。

---

### Q17. 高并发下日志怎么保证 request_id 不串?为什么用 ContextVar?

**考察点**:异步编程深度(高频深挖)。

**参考回答**:
异步里一个线程并发跑成百上千个协程。
- 如果用普通全局变量或 `threading.local()`:所有协程在同一线程,协程 A 改了值协程 B 就看到,日志 request_id 会"张冠李戴"(用户甲的日志印成用户乙的 ID);
- 用 **`ContextVar`**:Python 底层保证**每个协程只能读写属于自己的那份上下文数据**,即使协程切换执行 request_id 也不乱。

流程:中间件请求进来 `request_id_var.set(id)` → 业务代码不用手动传 ID,日志处理器自动 `request_id_var.get()` → 请求结束清空。这是 Python 3.7+ 的特性,核心是**上下文隔离性**。

---

### Q18. 业务指标埋点怎么做?B 端和 C 端有什么不同?

**考察点**:数据驱动优化。

**参考回答**:
- **B 端**(看系统好不好用):选题重试率(如 10%)、文章修改率(如 30%)、图片重生成率等,做漏斗分析优化转化,自己开发上报服务(数据敏感的公司);
- **C 端**(通用统计):接入**神策数据**统计 UV/PV、按钮点击(原理是代理浏览器 DOM 事件,获取 button 文本 post 到神策),前端接 SDK 几行代码,80% 前端接、20% 后台接。

---

## 六、LLM 工程化

### Q19. 结构化输出和 Token 统计为什么不能兼容?怎么解决?

**考察点**:LLM 输出控制(高频技术细节)。

**参考回答**:
**矛盾原因**:`with_structured_output()` 会构建 `llm | output_parser` 链,最终返回**解析后的 Pydantic 对象**而非原始 AIMessage,所以拿不到 `usage_metadata`(token 信息)。

**解决方案**:不用 `with_structured_output`,改用 **JSON 模式**:
1. `model_kwargs={"response_format": {"type": "json_object"}}` 直接调 LLM;
2. 拿到原始 AIMessage 从中提取 usage;
3. 手动把 `response.content` 解析成 JSON,再用 Pydantic 校验。

若模型不支持 response_format 或解析失败,**回退到按行解析**保证可用性。

**加分项**:流式和结构化也矛盾——流式是"边生成边输出",结构化是"等完整结果再解析"。推荐做法:流式接口输出纯文本,非流式接口用结构化输出。

---

### Q20. 选题生成用 temperature=0 合适吗?

**考察点**:采样参数与场景匹配。

**参考回答**:
**不合适**。temperature=0 意味着同一主题方向每次生成的选题几乎一样,缺乏多样性,用户重试也得不到新选题——对创意类任务不理想。选题属于创意生成,应该调高 temperature 增加多样性。
(对比:严谨问答、知识库复读才适合用 0。)

---

### Q21. 多模型路由策略是怎么设计的?

**考察点**:降本增效。

**参考回答**:
根据**内容类型、成本、延迟动态选模型**:简单任务用轻量 **Flash** 模型,复杂任务用旗舰 **Doubao-1.8**。比如简单的选题/摘要用 Flash,复杂的长文写作用旗舰版。在保证质量的同时降低约 40% 推理成本。

---

### Q22. 项目里 RAG 是怎么用的?业务上怎么规划?

**考察点**:RAG 在内容生成中的应用。

**参考回答**:
**技术实现**:在 LLM 调用之前加入知识库检索。
**业务规划**:
- **选题**:公司内部有选题题库,RAG 检索提供选题;
- **文章风格**:把别人的好文章 + 自己写的文章收集进知识库(可用爬虫 Agent 爬取目标网址 → LLM 清洗调格式 → 存知识库),让生成的文章风格更贴近爆款。

---

## 七、鉴权、配置与部署

### Q23. JWT 是什么?和传统 token 方案比有什么优势?

**考察点**:鉴权方案(高频)。

**参考回答**:
**JWT 是无状态登录鉴权方案**。流程:用户登录验证密码 → 服务器把用户信息(user_id、权限等)打包成 JSON,用密钥签名生成 token 返回 → 前端存 localStorage,每次请求在 Header 带 token → 服务器解密 token 直接拿到用户信息,**不用查数据库/Redis**。结构:Header(算法)+ Payload(sub/name/exp 等)+ 签名。

**对比传统方案**:传统 token 存 Redis 或服务器内存,是**有状态**的,不好横向扩展。JWT **无状态、自解析**,完美契合 Docker 容器化(无状态服务可无限横向扩展)。

**双 11 场景对比**:传统方案每次请求要查用户库,流量来了用户库也得扩容、加 Redis 主从读写分离;JWT 只带 token 就知道用户信息,**只需扩容业务服务器**。

**加分项**:OAuth2.0 解决 **SSO 单点登录**(一个账户登录多系统),通信协议用 JWT;流程是访问→未登录跳认证中心→换 code→换 token→写 cookie→访问其他系统直接带 token。

---

### Q24. 不同用户怎么区分会话?需要登录的接口怎么鉴权?

**考察点**:多租户与依赖注入。

**参考回答**:
- **区分会话**:`thread_id = user_id + 随机字符串`,查询时按 user_id 前缀查;
- **接口鉴权**:用 FastAPI 的依赖注入 `current_user: User = Depends(get_current_user)`,从请求 Header 的 Bearer token 解析校验。

---

### Q25. API 版本控制怎么做?什么时候要新增 v2?

**考察点**:接口演进。

**参考回答**:
项目用 `/api/v1/` 路由前缀,支持多版本并存平滑迁移:
- **破坏性变更 → 新增 v2**:接口不兼容旧版(新增必填字段、改字段名/状态值)时,新建 `v2/`,v1 保持维护模式;
- **非破坏性变更 → 直接改 v1**:向后兼容(新增可选字段且有默认值)时直接改 v1。

**加分项**:数据库字段一般**只增不删**,虽然影响一点性能,但**稳定性 > 性能**。

---

### Q26. 配置中心怎么抽象?有哪几种方案?

**考察点**:配置管理。

**参考回答**:
项目配置分两层:**项目层(env:API key、LLM url、模型类型、Mock、Debug)** 和 **业务层(提示词:用户/系统提示词)**。三种方案:
1. **集中式模块**(最简单):`core/config.py` + `core/prompts.py`;
2. **存数据库**(做成系统):提示词拿出来让产品/运营写,支持运行时修改、A/B 测试灰度、多版本管理;缺点是复杂度高、增加 DB 依赖;
3. **Nacos/Apollo**:分布式配置中心,解决微服务配置管理,体量大、极重稳定性,一般中大厂 Java 用。

---

### Q27. Mock 开关体系是怎么设计的?有什么用?

**考察点**:开发效率工程化。

**参考回答**:
用**环境变量驱动 Mock 开关**:`llm_mock`、`image_mock`、`checkpointer_mock`(如 `USE_MOCK_CHECKPOINTER`)。比如 checkpointer mock 时用 `MemorySaver`(内存,不持久化),关闭时用 `AsyncPostgresSaver`(持久化)。
**作用**:开发阶段不完全依赖外部服务(LLM/图片 API/数据库都没配好时),数据写死也能先把项目跑起来,保证业务顺利开发。

**加分项**:做 AI 应用的要点是**先写好 AI 服务端逻辑再写前端**;项目后期要去掉前期 mock 和过度防御性编程,因为它们会增加 token 消耗、影响性能。

---

### Q28. MCP 服务拆分是怎么考虑的?

**考察点**:服务化思维。

**参考回答**:
**MCP 的目的**:公司有多个系统 A/B/C 都需要生成图片,把图片能力做成 MCP 服务(传提示词+参数返回图片),就像前端组件库发布成 NPM 包供复用。
拆分:
- **Image MCP Server**:`generate_image(prompt, size, style)`、批量生成;
- **LLM MCP Server**:`chat_completion`、`structured_output`、`plan_topics`、`write_article`,多模型路由、Prompt 管理;
- **RAG MCP Server**:知识库检索。

---

### Q29. 健康检查和优雅关闭有什么用?

**考察点**:部署运维。

**参考回答**:
- **健康检查 `/health`**:返回服务状态和 DB 连接状态。配合监控系统轮询访问,挂了就报警/发邮件/发短信;用于**容器化部署的存活探针**(K8s/Pod 弹性扩缩容需要知道服务死没死)。
- **优雅关闭**:shutdown 时关闭连接池、关闭 checkpointer 释放资源。用 FastAPI 的 `lifespan`(`@asynccontextmanager`)管理——yield 之前是启动(初始化 DB、checkpointer 建表),yield 之后是关闭(释放资源)。

---

### Q30. 错误边界和降级策略怎么设计?

**考察点**:高可用兜底。

**参考回答**:
**多级兜底**:主模型失败 → 备用模型 → 兜底模板:
```python
try: return await llm_primary.invoke(topic)      # 主模型
except: return await llm_secondary.invoke(topic) # 备用模型
except: return get_cached_template(topic)        # 兜底模板
```
配合熔断器:简单降级是每个请求都试主服务(挂了每人等 10 秒);熔断降级是熔断打开后直接走备用(0 秒),用户秒拿结果——核心是**快速失败,不浪费时间**。降级结果用 `is_degraded: True` 标记。

---

## 八、面试方法论(文档作者强调)

### Q31. 这些技术(JWT/OAuth/SSO/熔断等)我没真正写过代码,面试能过吗?

**考察点**:作者的核心观点,值得理解。

**参考回答(作者观点)**:
**理解 > 说 > 能写**。很多技术(SSO、JWT、限流熔断)即使腾讯的老 Java 也未必都亲手写过,关键是**能讲清楚原理**。做项目的目的是掌握知识点、让面试官认为你厉害。用 Gemini 出方案、Claude 干活把功能实现出来,自己理解透了能讲出来,大概率能过——**用最短时间达到最强面试效果,靠的是能说清楚**。

---

## 附:简历项目描述(可背诵亮点)

> **自媒体智能内容运营系统(LangGraph + RAG)**

1. 基于 **LangGraph** 构建多阶段内容生成工作流,用 **SubGraph 子图**拆分选题/写作/配图;通过 **PostgreSQL Checkpointer** 实现状态持久化,支持任意历史节点回滚与增量重试,故障恢复粒度从整图细化到单节点。
2. 设计 **MetricsContext** 上下文管理器实现 LLM 全链路追踪(token/延迟/错误率),结合火山定价做成本核算。
3. 实现 **SSE 流式输出**与 `astream_events` 深度集成,监听 `on_chat_model_stream` 捕获 token 级流,**TTFT 降低 60%**。
4. 图片批量生成用 `asyncio.gather` + `run_in_executor` 由串行改并发,引入指数退避重试(1s→2s→4s),**生成耗时缩减 70%**。
5. 多模型动态路由(简单→Flash,复杂→Doubao-1.8),用 JSON Mode + 手动解析解决结构化输出与 token 统计不兼容,**降低 40% 成本**。
6. 环境变量驱动 **Mock 开关体系**(llm/image/checkpointer),配合 Swagger + Ngrok,本地调试效率提升 3 倍。
7. 接入 **LangSmith** 全链路可观测,配合 structlog + request_id 关联,问题定位从小时级压缩到分钟级。
8. **SlowAPI 限流** + **熔断器**保护下游 LLM,降级模板兜底;健康检查 + 优雅关闭保障容器化高可用。

---

## 附:高频速记要点

- **LangGraph 三件套**:StateGraph(状态机)/ AgentState(TypedDict 状态)/ `interrupt()`(1.0 中断,不用 interrupt_before)
- **HITL**:thread_id + start/state/resume 三接口;`ainvoke(Command(resume=...))` 恢复;review 节点同意/拒绝都重走一次
- **Checkpointer**:AsyncPostgresSaver 自动序列化;4 张表(checkpoints 元数据 / blobs 二进制数据 / writes / migrations);分开存为查询效率+去重
- **连接池**:在线≠操作,1000 用户 ≠ 1000 连接;中小 max=10,企业 20-100
- **流式**:`astream`(节点级)vs `astream_events`(`on_chat_model_stream` token 级);SSE + StreamingResponse + 禁 Nginx 缓冲
- **子图**:同类型不同实例,状态流转共享;Checkpointer 主图统一管,别搞多个
- **并发**:`run_in_executor` 包同步 API + `asyncio.gather`;指数退避 1→2→4s
- **限流(保护自己)vs 熔断(保护不被下游拖死)**;熔断三态:开→半开→恢复;降级兜底
- **可观测**:MetricsContext 算 token/耗时;LangSmith 配 env 即用;ContextVar 防高并发 request_id 串
- **结构化输出 vs token 统计冲突** → 用 JSON Mode 拿原始 AIMessage 提 usage
- **选题用 temperature=0 不合适**(缺多样性);多模型路由降本
- **JWT 无状态自解析**,契合 Docker 横向扩展,双 11 只扩业务服务器;OAuth2.0 解决 SSO
- **方法论**:理解 > 说 > 能写,Gemini 出方案 + Claude 实现
