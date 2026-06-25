# 预习

https://gitee.com/mood6666/mcp-agent-preview-materials

需要通读一遍

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=OGVmYTRkMjhlMTkzMTgzOTRlNDEzOTY2YTAyMzBlZDNfNms5RUlFclkyeXhXaDh2cG80VldzbU8yc0FJVHpzUzlfVG9rZW46Wkx1WGJKRHhrb2VXSzB4ZmJjemNyVTdTbm5kXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

在node40k课程中找

1. Docker
2. CICD自动化部署

# Agent集群背景

1. 未来所有的软件公司，所有的软件全部要接入ai
2. 所有的数据库都要结合向量数据库，搞语义化
3. 我一家公司，有很多系统
   1. ERP    几十个
   2. Ai的系统也需要全部打通   形成Agent集群

# Agent集群架构核心

1. MCP  集群（公共服务）
2. Ai项目业务  集群

# 需要考虑以下4个点

10个项目

80个MCP服务

1. ## 路由与调度层 (The Router Layer)

当你只有 3 个 MCP 服务时，Agent 还可以手动连接。但当你有 30 个 MCP 服务时，Agent 无法在 Prompt 里塞进所有工具的说明（Context Window 会爆）。

- **缺失的环节：** 你需要一个 **Agent Router**。
- **解决：** 它的任务是根据用户的需求，动态地选择加载哪几个 MCP Server。比如用户提到“画图”，Router 才把 `Image-MCP` 的接口描述喂给当前的业务 Agent。
- **价值：** 节省 Token 成本，提升响应速度。

1. ## 跨 Agent 的“统一记忆体” (Global Memory)

业务 Agent 之间目前是孤立的。如果用户在“语音客服”里提到了他的学习进度，等他打开“生图 Agent”做教案时，后者并不知道这个信息。

- **缺失的环节：** **User-Centric Profile (用户画像中心)**。
- **解决：** 建立一个独立的 MCP 资源服务，专门管理“用户记忆”。
  - **短期记忆：** 跨项目的 Session 共享。
  - **长期记忆：** 用户的教育背景、偏好风格、历史纠错记录。
- **价值：** 让你的所有 AI 产品看起来像是一个统一的“AI 助手集群”，而不是一堆互不认识的工具。

1. ## 可观测性与调试 (Observability)

在 MCP 架构下，一个请求的链路变长了：`用户 -> 业务 Agent -> MCP Proxy -> MCP Server -> 大模型/工作流`。如果结果报错或变慢，定位问题会非常痛苦。

- **缺失的环节：** **Tracing (链路追踪)**。
- **解决：**
  - **日志对齐：** 所有的业务 Agent 和 MCP 服务必须带上同一个 `trace_id`。
  - **评估系统：** 引入像 **LangSmith** 或 **Arize Phoenix** 这样的工具，专门监控每个 MCP 节点的耗时和 Token 消耗。
- **价值：** 确保你能回答“为什么这通电话延迟了 3 秒”或者“哪个 MCP 服务最费钱”。

1. ## 资产的安全隔离 (Security & Multitenancy)

作为老板，你需要考虑不同项目的权限。

- **缺失的环节：** **MCP 访问控制 (AuthZ)**。
- **解决：**
  - 不是所有 Agent 都能调用“生图 MCP”（因为生图很贵）。
  - 需要一个网关层来校验：`Agent_A` 是否有权调用 `Server_B`。
  - **资源配额：** 给每个项目设置 Token 或 GPU 调用上限，防止某个实验性项目把公司的 API 额度瞬间刷爆。

1. ## 项目与MCP鉴权

1. ## 集群部署

# Ai服务的部署流程

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=MjBkYzRjZjY3MWQ2NzkxMGI5MmM5YmMzNTAzMDQxYzZfR2VxOVVmdVhpemVvTGJKQnRuY2ZuMGRKcnNaZ2x1eE9fVG9rZW46WkZIWWJUeExVb09FOWx4bTN5MmM4VDZHbmJiXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

## 后端部署

后台想CICD

1. Gitlab（仓库  起点）
2. push代码
3. 触发钩子（shell脚本   项目代码里）
   1. 打包镜像
   2. 上传阿里云镜像仓库

1. 项目打镜像
   1. 本地打  push给阿里云
   2. Dockerfile.aliyun  本地打
      1. 本地安装docker
      2. 

暂时无法在飞书文档外展示此内容

1. 云函数业务代码部署 SAE
2. 跑脚本
   1. 轻量
3. 跑镜像
   1. 整个项目在里面

云函数  serverless

核心：含量计费。

1. 流量
2. CPU计算量
3. 弹性扩容（云函数是自动扩容 写规则  充钱   K8S是手动的，是运维玩的）

传统：

买一个阿里云的ECS  500/年

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=MjgzNzcwNmEyY2Y1MTI2YWYzMjYwMDFmYTgwODIxNmZfaDJhTTQ1ZlkzTmdMQjhiS3Z1SmpsS2VrUVlPbUhvelNfVG9rZW46V1FKVWJsVHY4b0VOT2J4R0ZCeWN6eHdIbmFkXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

1. CLB负载均衡（Nginx）
   1. SAE 提供一个内网地址，通过负载均衡CLB到公网  比如：152.152.1.1
   2. 域名的DNS解析到  公网IP   152.152.1.1

1. HTTPS证书（在CLB里面去配  免费证书）（火山引擎的RTC语音服务必须要HTTPS）
2. 网关 NAT   

## 前端部署

1. Npm run build
   1. Html css js  也可以走CICD
2. 上传到oss（源站）
3. 配CDN  （内容分发）

# 什么是正向代理？反向代理？

1. ### 正向代理（Forward Proxy）

服务器不知道客户端是谁

**故事：未成年小明想买烟** 小明还是个孩子，便利店老板不卖烟给他。于是小明给了邻居大哥哥 20 块钱，让大哥哥帮他去买。

- **小明**：客户端（Client）
- **大哥哥**：正向代理服务器（Proxy）
- **便利店老板**：目标服务器（Server）

**关键点**：

- 老板只知道烟卖给了大哥哥，**不知道真正想抽烟的是小明**。
- 正向代理是**为了保护或代表客户端**去访问它访问不到（或不想暴露身份）的东西。
- **用途**：科学上网、隐藏真实 IP、公司内网访问外网控制。

1. ### 反向代理（Reverse Proxy）

客户端，不知道服务器是谁

**故事：****你拨打 10086 客服电话** 当你手机欠费了，你拨打 10086。电话接通后，对面有个温柔的声音帮你解决了问题。但你并不知道接电话的是坐在北京的张三，还是坐在上海的李四，你只知道你拨的是 10086。

- **你**：客户端（Client）
- **10086 总机**：反向代理服务器（Nginx）
- **具体的客服张三/李四**：后端真实服务器（Real Server）

**关键点**：

- 你以为你在和 10086 说话，其实 10086 只是个“接线员”，它把你的请求**偷偷转发**给了后台某个有空的客服。
- 你**不知道**具体是哪台服务器在为你服务，你只跟反向代理打交道。
- **用途**：负载均衡（谁闲着给谁接）、保护服务器安全（不让外人知道服务器真实 IP）、SSL 卸载（统一处理加密）。

除了当“接线员”，Nginx 还有几个拿手好戏：

- **负载均衡（Load Balancing）**： 如果 10086 同时涌入 100 万个电话，Nginx 会像交警一样指挥交通：“1 号服务器满了，去 2 号；2 号也满了，去 3 号。”确保没有服务器被累死。
- **动静分离（Static Content Serving）**： 如果有人只是想问“现在几点了”这种简单问题（静态文件：图片、CSS、HTML），Nginx 根本不需要打扰后端的“厨师”（应用服务器），它自己口袋里就有答案，直接秒回。
- **虚拟主机**： 一台服务器上可以跑好几个网站（比如 `a.com` 和 `b.com`），Nginx 能根据用户输入的域名，精准地把请求带到对应的家门口。

# CLB和Nginx的区别？

1. ### 真正的“高可用” (High Availability)

- **自建 Nginx**：如果运行 Nginx 的那台云服务器（ECS）挂了，你的整个网站就断网了。要解决这个问题，你得自己再买一台服务器，配上 Keepalived 搞主备切换。
- **阿里云负载均衡**：它底层是一个庞大的**集群**。阿里云保证了即使某台物理服务器坏了，流量会自动漂移。它还支持**跨可用区（Zone）容灾**，即便整个机房断电了，它能秒级切换到另一个机房。

1. ### 自动扩容 (Elasticity)

- **自建 Nginx**：双 11 流量翻了 10 倍，你的 Nginx 可能会因为 CPU 爆满而宕机。你需要手动去升级服务器配置。
- **阿里云负载均衡**：它是弹性的。流量大时，后台会自动分配更多资源去扛；流量小时，按量付费（如果选了按量模式），不需要你操心底层硬件。

1. ### 与云生态的“深度集成”

这是自建 Nginx 很难做到的：

- **自动发现服务器 (Auto Scaling)**：如果你开启了“弹性伸缩”，当业务太忙自动增加 10 台服务器时，CLB 会**自动**把这 10 台加进白名单。Nginx 则需要你手动改配置文件并重启。
- **一键挂载证书**：在阿里云后台买的 SSL 证书，点一下就能挂到负载均衡上，不需要去服务器里敲命令行、配路径。
- **健康检查 (Health Check)**：它有一套非常成熟的探测机制。如果后端某台服务器“感冒”了（响应变慢或报错），CLB 会立刻把它踢出去，等它恢复了再拉回来，全程自动化。

1. ### 极致的安全防护

- **免费的 DDoS 防护**：由于负载均衡是流量的入口，它天然集成了阿里云的基础防护。小规模的攻击在到达你的服务器之前，就被云端清洗掉了。
- **WAF 集成**：可以直接在负载均衡层面开启 Web 应用防火墙，过滤 SQL 注入、脚本攻击等，而不需要在每台后端服务器上装安全软件。

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=YWNiZTUxYjVhNzZhODA3Y2QyODZmZWNlZDNiNWM3ZDZfdU9WRE93am1zVFJ4b3NSRVR4ZTdhVjdxNEd6RjFjU3FfVG9rZW46TFJrR2JrUzJCb2RnaGN4SDZHc2N1algwbmxkXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

# 什么是NAT？

简单来说，**阿里云 NAT 网关（NAT Gateway）** 是为你的云上私网服务器（ECS）提供 **“上外网”** 和 **“被外网访问”** 的一个企业级公共出口。

如果把你的阿里云 VPC 网络比作一栋**没有窗户的办公大楼**，里面的服务器就是坐在工位上的员工。NAT 网关就是大楼的**总机房/传达室**。

1. ### 它的两个核心功能

#### A. SNAT（让服务器能“上外网”）—— 就像“代拨电话”

你的服务器（ECS）通常只有内网 IP，为了安全不直接绑定公网 IP。但它们需要下载补丁、更新代码或调用外部 API。

- **作用**：多台没有公网 IP 的服务器，可以通过同一个 NAT 网关的公网 IP 访问互联网。
- **好处**：隐藏了后端服务器的真实位置，非常安全；同时省钱，不需要给每台服务器都买公网 IP。

#### B. DNAT（让外网能“找进来”）—— 就像“分机号转发”

如果你想让外部用户访问你内网里的某台服务器（比如数据库或私有服务）。

- **作用**：你可以设定规则：当有人访问 NAT 网关 IP 的 8080 端口时，自动转发到内网 A 服务器的 80 端口。
- **好处**：这是一种比直接把服务器暴露在公网更受控、更安全的映射方式。

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=OTM2M2U4MGU1NmJmNDJjMmU3YzQxZjUwNDhiNTM2NzlfWDRJYng0UkNOT05zMzEzN0dBM3BiV1V3a2d1RHNjSXNfVG9rZW46SHRGamIyUHE1b1hGWGx4dEl3eGNXZER3bk1oXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

## DNAT需要配置吗？

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=Njg3Zjc5OTQyZDdmYmIxZDBkMWMwNDhkZTI3NDQzMGZfRjVSek5qMm9Obk5henluRFczeHY3dk1iZzFyczVDbElfVG9rZW46T2Nab2JDYUt2b3BROGR4NFlabGNiUWtxblZmXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

![img](https://jianxuanguan.feishu.cn/space/api/box/stream/download/asynccode/?code=NzQ4ZWFlYjg1NzAzZWJkNjE3MjIxMGIzZWQzODliOTVfR3hvYUtiZzIzaXNOMzFYMWpDemJGQWZIQVhsd1VoTnVfVG9rZW46SnNWYmJtZVJyb01Tdkp4c1dYaGM2T2w2bjdiXzE3ODIxMzEzMTI6MTc4MjEzNDkxMl9WNA&add_watermark=true&scene_type=CCM)

# 从0到1实现Agent集群

## 代码仓库

https://gitee.com/mood6666/mcp-agent-preview-materials

1. 我有个想法，我多个项目想使用通用的MCP的服务，有通用的，有自己的MCP
2. 需要考虑哪些问题，如何设计架构
3. Ai给我方案
4. 我提意见
5. 行 就这个方案吧，给我把你的方案输出到MD

暂时无法在飞书文档外展示此内容

暂时无法在飞书文档外展示此内容

1. ### SSE (Server-Sent Events)：单向的大喇叭

**SSE 的本质是：服务器往客户端“单向推数据”。**

- **形象理解：** 就像你在广场上听**大喇叭广播**，或者看**电视直播**。
- **怎么工作：** 你（客户端）跟服务器说：“我要听广播了。” 然后服务器就一直拿着喇叭喊，有新消息就喊一句，你只能听，没法顺着喇叭喊回去。
- **在 AI 里的用途：** 比如 ChatGPT 吐字，服务器一个字一个字往外蹦，这就是典型的 SSE。

1. ### Streamable HTTP：双向的对讲机

**Streamable HTTP（在 MCP 语境下）是：基于 HTTP 的“双向实时聊天”。**

- **形象理解：** 就像两个人拿着**对讲机**或者在打**微信电话**。
- **怎么工作：** 它不只是服务器给你发数据，它还允许你（客户端）在**同一个连接**里不断地给服务器发指令。
- **在 MCP 里的特殊性：** MCP 需要 Client 和 Server 频繁“切磋”（Client 问：你有什么工具？Server 答：我有加法。Client 又问：那帮我算 1+1。Server 又答：结果是 2）。
- **关键点：** 它把原本“一问一答就断开”的传统 HTTP，变成了“一直连着、随时交流”的**长连接流**。

### 为什么 MCP 选择了 Streamable HTTP？

如果只用 SSE，客户端发一个指令，服务器回一个结果，连接就断了。下次想再调用另一个工具，又得重新建立连接、重新握手、重新验证身份……这太慢了！

**Streamable HTTP 就像是在 Client 和 Server 之间修了一条“高速专用双向车道”：**

1. **省事：** 握手一次，终身受益（直到会话结束）。
2. **快：** AI 这种需要反复确认、多次调用的场景，这种“连着不撒手”的方式效率最高。

# 我们为何要抽象出通用的MCP服务？

1. 不用配一大堆key，直接访问地址就能用。
   1. 像组件库

# 项目env

暂时无法在飞书文档外展示此内容

## LLM gateway 主要作用

我项目所有大模型的调用，都走这个MCP服务。

# 简历模板

# **项目4** 

## **基于 MCP 协议的多 Agent 共享服务集群　　2025.X ~ 至今**

1. **基于 MCP（Model Context Protocol）协议设计多 Agent 共享服务架构**，将 LLM 网关、RAG 检索、会话记忆、Prompt 管理抽离为 4 个独立 MCP Server，通过 Streamable HTTP 传输暴露标准化 Tool/Prompt 原语；上层业务项目经 HTTP 网关统一接入，新业务接入仅需编写 Agent 编排层。
2. **设计 REST → MCP 协议桥接网关，**基于 FastAPI 构建四层中间件链（认证 → 日志 → 配额 → 路由），通过 Trace ID 实现全链路追踪；内置 MCP Client Manager 管理 Streamable HTTP 短连接，按项目维度实现 API Key 认证与 Token 配额计量，确保多租户安全隔离与成本管控。
3. **构建统一 LLM 网关，封装豆包 ARK API（OpenAI 兼容）**，实现逻辑模型名到 Endpoint 的路由策略（auto/pro/lite），通过 YAML 配置热切换模型业务层无感；Embedding 接口兼容火山引擎 text 与 vision 两种向量化路径，Token 消耗统一回传网关配额模块扣减。
4. **实现多租户 RAG 检索服务，基于火山引擎 Viking DB 按 project_id 划分独立 Collection 实现知识库物理隔离；**文档按 Markdown 标题层级 + 段落边界语义切分避免跨主题截断，检索侧支持 top-k 语义召回，新项目调用 `ingest_document` Tool 即可自助接入。
5. **设计双层记忆架构：**对话记忆按 `project_id + session_id` 隔离，支持最近 N 轮召回与会话清空；用户画像按 `user_id` 跨项目共享，基于 PostgreSQL `UPSERT`（ON CONFLICT DO UPDATE）实现幂等写入；客服 Agent 通过 LLM 自动提取用户事实（过敏/预算/偏好）写入画像，写作 Agent 即时读取，实现跨项目用户认知同步。
6. **基于 MCP 原生 Prompt 原语构建模板中心，**YAML 定义参数 Schema，服务端渲染后以 `PromptMessage` 结构返回；Agent 按需组合画像、检索片段、对话历史进行 Prompt 装配，模板修改即时生效无需重启，实现提示词工程与业务逻辑解耦。
7. **实现 Agent 七步编排流水线（召回历史 → 读取画像 → 检索知识 → 渲染 Prompt → LLM 推理 → 保存记忆 → 提取事实）**，全部通过 GatewayClient 统一调用，Agent 不持有状态，所有状态下沉到共享 MCP 服务，实现业务与基础设施彻底分离。
8. **各服务独立构建 Docker 镜像，部署至阿里云 Serverless（函数计算 / SAE），按依赖拓扑分层发布（MCP 服务 → 网关 → 业务项目）；**借助平台自动弹性伸缩应对流量波动，单服务独立镜像更新实现灰度发布与秒级回滚，SIGTERM 信号触发优雅终止确保在途请求不丢失。

# 面试题

1. # 你在项目中Ai编程，有没有碰到过什么问题？

比如embbeding模型，你要去告诉Ai文档信息，否则bug永远解决不掉。

模型，训练即封印。

所以Claude code只能解决99%问题，1%必须人工介入。