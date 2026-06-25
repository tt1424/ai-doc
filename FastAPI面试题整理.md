# FastAPI 面试题整理

> 根据《FastAPI 入门教程》12 章内容整理的面试题，覆盖从基础概念到工程化、部署的完整知识体系。
>
> 每题包含 **参考答案**，建议先自己作答，再对照答案查漏补缺。
> 难度标记：⭐ 基础 / ⭐⭐ 进阶 / ⭐⭐⭐ 高阶

---

## 目录

1. [第一章 初识 FastAPI](#一初识-fastapi)
2. [第二章 路由与请求处理](#二路由与请求处理)
3. [第三章 数据校验与序列化（Pydantic）](#三数据校验与序列化pydantic)
4. [第四章 自动交互式文档](#四自动交互式文档)
5. [第五章 依赖注入系统](#五依赖注入系统)
6. [第六章 中间件与异常处理](#六中间件与异常处理)
7. [第七章 异步与性能](#七异步与性能)
8. [第八章 数据库集成](#八数据库集成)
9. [第九章 认证与安全](#九认证与安全)
10. [第十章 项目结构与工程化](#十项目结构与工程化)
11. [第十一章 测试](#十一测试)
12. [第十二章 部署上线](#十二部署上线)
13. [综合 / 场景题](#十三综合--场景题)

---

## 一、初识 FastAPI

**Q1.1 ⭐ FastAPI 是什么？它的核心卖点有哪些？**

FastAPI 是基于 Python 类型提示构建 Web API 的现代框架。核心理念是：**用 Python 类型提示描述接口，框架自动完成参数校验、序列化和文档生成**。核心卖点：
- **快（性能）**：基于 ASGI，性能与 Node.js、Go 同级别，约为 Flask 的 5~10 倍。
- **快（开发）**：类型提示驱动，编辑器自动补全好，开发效率高。
- **少 Bug**：请求参数自动校验，类型错误在进入业务逻辑前被拦截。
- **标准化**：完全兼容 OpenAPI（Swagger）和 JSON Schema。
- **自动文档**：启动即自带交互式文档，零配置。

**Q1.2 ⭐ FastAPI 底层依赖哪两个库？各自负责什么？**

- **Starlette**：负责 Web 层（路由、请求、响应、WebSocket、中间件、静态文件）。
- **Pydantic**：负责数据层（数据校验、序列化、类型转换）。

即 `FastAPI = Starlette（Web）+ Pydantic（数据）`。

**Q1.3 ⭐⭐ WSGI 和 ASGI 有什么区别？为什么 ASGI 性能更好？**

- WSGI（Flask/Django 默认）是**同步**协议：一个请求占一个线程，等待 I/O（如数据库）时线程闲置，同一时间能处理的请求有限。
- ASGI（FastAPI）是**异步**协议：等待 I/O 时可以切换去处理别的请求，用同样的资源获得更高吞吐量。

对于经常需要等数据库、等外部接口的 API 场景，ASGI 的异步架构天然更高效。

**Q1.4 ⭐ FastAPI 与 Flask、Django REST Framework 的定位差异？**

| 维度 | Flask | DRF | FastAPI |
|------|-------|-----|---------|
| 定位 | 轻量 Web | 全功能 Web+API | 专注 API |
| 协议 | WSGI 同步 | WSGI 同步 | ASGI 异步 |
| 数据校验 | 手动/第三方 | Serializer | Pydantic 自动 |
| API 文档 | 需插件 | 内置但重 | 自动生成、零配置 |
| 性能 | 一般 | 一般 | 极高 |

**Q1.5 ⭐ `fastapi dev main.py` 和生产启动方式有什么不同？两个自动文档地址是什么？**

`fastapi dev` 是开发模式，支持代码热重载，绑定本地地址。生产环境用 `uvicorn`/`gunicorn` 启动、关闭热重载、多 Worker。两个自动文档：
- `/docs` —— Swagger UI（可在线测试）
- `/redoc` —— ReDoc（只读，适合分享）

---

## 二、路由与请求处理

**Q2.1 ⭐ FastAPI 如何区分路径参数、查询参数和请求体？**

FastAPI 按以下决策规则自动识别：
1. 参数名出现在路径模板 `{...}` 中 → **路径参数**。
2. 参数类型是 Pydantic `BaseModel` → **请求体**。
3. 以上都不是 → **查询参数**。

三种参数可以在同一个函数里混用，FastAPI 自动区分。

**Q2.2 ⭐ HTTP 方法与 RESTful 语义如何对应？哪些是幂等的？**

| 方法 | 语义 | 幂等性 |
|------|------|--------|
| GET | 读取 | 是 |
| POST | 创建 | 否 |
| PUT | 全量更新 | 是 |
| PATCH | 局部更新 | 否 |
| DELETE | 删除 | 是 |

幂等性：同一请求执行多次效果与一次相同。POST 连发多次可能创建多条记录，所以不幂等。

**Q2.3 ⭐⭐ 为什么 `/users/me` 必须写在 `/users/{user_id}` 前面？**

FastAPI 按代码中**装饰器的书写顺序**从上到下匹配，匹配到第一个就停止。如果 `/users/{user_id}` 在前，请求 `/users/me` 会先匹配到它，把 `"me"` 当作 `user_id`，无法转成 `int` 而返回 422。所以**固定路径必须写在动态路径前面**。

**Q2.4 ⭐ 必填、选填、可选三种参数写法分别怎么定义？**

| 写法 | 含义 | 不传时 |
|------|------|--------|
| `keyword: str` | 必填 | 422 错误 |
| `page: int = 1` | 有默认值（选填） | 用默认值 |
| `tag: str \| None = None` | 可选 | 值为 None |

**Q2.5 ⭐ 路径参数支持哪些类型校验？举几个例子。**

支持 `int`、`str`、`float`、`UUID`、`Enum` 等。声明类型后自动转换并校验，非法值返回 422。例如 `order_id: UUID` 会校验 UUID 格式；用继承 `str, Enum` 的枚举类可限定取值范围。

**Q2.6 ⭐⭐ `model_dump(exclude_unset=True)` 在更新接口里有什么作用？**

它只取客户端**显式传了**的字段，没传的字段不会出现在结果里。用于 PUT/PATCH 局部更新时，避免把没传的字段覆盖成 `None` 或默认值——只更新用户真正想改的字段。

---

## 三、数据校验与序列化（Pydantic）

**Q3.1 ⭐ Pydantic 在 FastAPI 中承担哪些职责？**

Pydantic 是 FastAPI 的「数据守门员」，所有进出数据都经过它：
- 类型转换（`"42"` → `42`）
- 数据校验（`age < 0` 报错）
- 序列化（Model → JSON）
- 文档生成（自动出现在 `/docs`）

**Q3.2 ⭐⭐ `name: str | None` 和 `name: str | None = None` 有什么区别？**

- `name: str | None = None`：**可选**字段，不传时值为 `None`。
- `name: str | None`：**必填**字段，但允许传 `None`，不传会报 422（必须显式传值）。

区别在于有没有默认值——有默认值才是真正可选。

**Q3.3 ⭐ `Field()` 常用的数值约束和字符串约束有哪些？**

- 数值：`gt`（>）、`ge`（>=）、`lt`（<）、`le`（<=）。
- 字符串：`min_length`、`max_length`、`pattern`（正则）。
- 通用：`default`、`description`、`examples`。

**Q3.4 ⭐⭐ `@field_validator` 和 `@model_validator` 有什么区别？**

- `@field_validator`：校验**单个字段**，入参是该字段的值，用于格式检查、值清洗（如 `v.strip()`）。Pydantic V2 中必须配合 `@classmethod`。
- `@model_validator(mode="after")`：校验**整个模型**，入参是完整模型实例，用于**跨字段**关联校验（如「结束日期必须晚于开始日期」）。

校验失败时 `raise ValueError(...)` 会触发 422。

**Q3.5 ⭐⭐ `response_model` 的作用是什么？为什么说它和安全有关？**

`response_model` 控制接口实际返回给客户端的数据结构。即使函数返回了包含敏感字段（如 `password`、`hashed_password`）的完整对象，FastAPI 也只会按 `response_model` 定义的字段输出，多余字段被自动过滤。这避免了不小心泄露敏感字段，是一道安全防线。

**Q3.6 ⭐⭐ 什么是「读写分离」的模型设计思想？为什么要分多个模型？**

为不同场景定义不同模型：
- `UserCreate`（输入）：含明文密码，不含 id。
- `UserUpdate`（输入）：字段全可选，只改需要改的。
- `UserInDB`（数据库）：含密码哈希、id。
- `UserResponse`（输出）：含 id，不含密码。

好处：每个场景只暴露必要字段，输入校验与输出格式各自独立，文档自动展示正确 Schema，避免创建时要传 id、返回时泄露密码等问题。

**Q3.7 ⭐⭐ 嵌套模型的校验是如何进行的？错误信息有什么特点？**

嵌套模型**递归校验**——外层模型校验完会进入内层模型继续校验，列表中每个元素也会被独立校验。错误信息会给出**精确的嵌套路径**，例如 `["body", "company", "address", "zipcode"]`，方便定位是哪一层哪个字段出错。

**Q3.8 ⭐⭐ `response_model_exclude_unset` 和 `response_model_exclude_none` 有什么用？**

- `response_model_exclude_unset=True`：未显式赋值的字段不出现在响应中。
- `response_model_exclude_none=True`：值为 `None` 的字段不出现在响应中。

还有 `response_model_include` / `response_model_exclude` 用于精确包含/排除字段。

---

## 四、自动交互式文档

**Q4.1 ⭐ Swagger UI 和 ReDoc 有什么区别？分别适合什么场景？**

| 维度 | Swagger UI (`/docs`) | ReDoc (`/redoc`) |
|------|---------------------|------------------|
| 交互性 | 可直接发请求测试 | 只读 |
| 布局 | 单栏逐个展开 | 三栏，左导航 |
| 适合 | 开发者自己调试 | 分享给前端/第三方 |

两者数据源相同（都来自 `/openapi.json`），只是展现形式不同。

**Q4.2 ⭐ `tags`、`summary`、`description` 这三个路由参数分别影响文档的哪里？**

- `tags`：接口分组（文档中按标签归类）。
- `summary`：接口标题（折叠状态可见，替代默认函数名）。
- `description`：接口详细说明，支持 Markdown。

**Q4.3 ⭐⭐ 如何给 Pydantic 模型添加文档示例值？两种方式有何区别？**

- `model_config` 里的 `json_schema_extra` → `examples`：**整个模型级别**，提供一组完整示例。
- `Field(examples=[...])`：**单个字段级别**，各字段独立展示示例。

**Q4.4 ⭐⭐ 生产环境想关闭文档怎么做？想自定义文档路径呢？**

通过 `FastAPI()` 参数控制：
```python
app = FastAPI(docs_url="/swagger", redoc_url="/api-doc")  # 自定义路径
app = FastAPI(docs_url=None, redoc_url=None)              # 关闭文档
```

**Q4.5 ⭐ 如何控制文档中 tag 的顺序和描述？**

在 `FastAPI()` 中配置 `openapi_tags`，传入一个列表，每项含 `name` 和 `description`。文档中 tag 的显示顺序就是该列表的定义顺序。

---

## 五、依赖注入系统

**Q5.1 ⭐ 什么是依赖注入？FastAPI 用什么实现？**

依赖注入的本质是：**把「准备工作」从业务逻辑抽出来，由框架按需自动调用并注入结果**。FastAPI 用 `Depends()` 实现，写在路由函数的参数中。常见用途：认证、权限校验、数据库会话、公共查询参数。好处是逻辑只写一次、多处复用。

**Q5.2 ⭐⭐ 什么是多级依赖？依赖链中某一层抛异常会怎样？**

依赖函数自身也能用 `Depends()`，形成链式调用（如 `get_token` → `get_current_user` → 路由函数），FastAPI 自动解析整个依赖链。如果某一层抛异常（如 `raise HTTPException`），链在此**断开**，后续层和路由函数都不执行，直接返回错误响应。

**Q5.3 ⭐⭐⭐ `yield` 依赖和普通依赖有什么区别？典型应用场景？**

- 普通依赖：`return value`，用于计算值、校验、获取配置。
- `yield` 依赖：`yield value` + `finally: cleanup`，可在请求处理前后执行代码，自动管理需要「打开→使用→关闭」的资源。

最典型的场景是数据库 Session 管理：
```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
关键点：**`finally` 块一定会执行**，即使路由函数抛异常也不例外，保证资源不泄漏。

**Q5.4 ⭐⭐ 类作为依赖有什么优势？`Depends()` 不传参数是什么意思？**

类依赖适合复杂逻辑或需要携带配置参数的场景。访问结果用 `result.key`（属性）比 dict 的 `result["key"]` 更友好。当依赖是类时可以简写 `pagination: Pagination = Depends()`，FastAPI 会根据类型注解自动推断，等价于 `Depends(Pagination)`。

**Q5.5 ⭐⭐⭐ 如何用类依赖实现「可配置的权限检查器」？**

通过 `__init__` 接收配置、`__call__` 实现可调用逻辑：
```python
class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    def __call__(self, authorization: str = Header()):
        # 校验 token、检查 role 是否在 allowed_roles 中
        ...

allow_admin = RoleChecker(["admin"])
allow_editor = RoleChecker(["admin", "editor"])
```
不同实例携带不同配置，用 `Depends(allow_admin)` 即可复用。核心技巧是实现 `__call__` 让实例可调用。

**Q5.6 ⭐ 把分页参数抽成公共依赖有什么好处？对调用方透明吗？**

多个接口共享 `skip`/`limit` 等参数时抽成依赖，修改一处全局生效。对调用方完全透明——这些查询参数会自动出现在每个接口的文档里。

---

## 六、中间件与异常处理

**Q6.1 ⭐ `HTTPException` 怎么用？有哪些参数？**

抛出后立即终止请求并返回错误响应。参数：
- `status_code`：HTTP 状态码。
- `detail`：错误详情，支持 str / dict / list（可构造复杂错误结构）。
- `headers`：可选，附加自定义响应头。

```python
raise HTTPException(status_code=404, detail="Todo 不存在")
```

**Q6.2 ⭐ 常见 HTTP 状态码 401、403、404、409、422 分别代表什么？**

- 401 Unauthorized：未登录 / Token 无效。
- 403 Forbidden：已登录但无权限。
- 404 Not Found：资源不存在。
- 409 Conflict：资源冲突（如用户名已存在）。
- 422 Unprocessable Entity：请求参数校验失败（FastAPI 自动返回）。

**Q6.3 ⭐⭐ 如何自定义异常处理器统一错误响应格式？**

用 `@app.exception_handler(异常类型)` 注册处理器。可以定义自己的业务异常类，注册处理器返回统一格式的 `JSONResponse`：
```python
@app.exception_handler(BusinessError)
async def handler(request: Request, exc: BusinessError):
    return JSONResponse(status_code=exc.status_code,
        content={"success": False, "error_code": exc.code, "message": exc.message})
```

**Q6.4 ⭐⭐ 如何全局捕获 `RequestValidationError` 并自定义 422 的格式？**

注册 `@app.exception_handler(RequestValidationError)`，遍历 `exc.errors()` 提取字段路径和消息，组装成统一格式返回。实际项目通常还会加一个兜底的 `@app.exception_handler(Exception)`，捕获未预料异常返回 500，避免泄露堆栈信息。

**Q6.5 ⭐⭐ 中间件的「洋葱模型」是什么意思？中间件函数的标准结构？**

请求从外到内依次经过每层中间件 → 到达路由函数 → 响应从内到外依次返回。标准结构：
```python
@app.middleware("http")
async def my_middleware(request: Request, call_next):
    # ① 请求前逻辑
    response = await call_next(request)  # ② 调用下一层
    # ③ 响应后逻辑（如加响应头、记录耗时）
    return response
```

**Q6.6 ⭐⭐ CORS 是什么问题？FastAPI 如何配置？生产环境要注意什么？**

CORS（跨域资源共享）：当前端和后端不在同一个域时，浏览器会先发预检请求询问后端是否允许跨域。用 `CORSMiddleware` 配置：
```python
app.add_middleware(CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
```
**生产环境绝对不要用 `allow_origins=["*"]`**，应明确列出允许的前端域名。

**Q6.7 ⭐⭐ 中间件里如何直接拦截请求、不让它到达路由函数？**

中间件中直接 `return` 一个 `Response`（如 `JSONResponse`）而**不调用** `call_next`，请求就会被拦截。常用于 IP 黑名单等场景。

---

## 七、异步与性能

**Q7.1 ⭐ 同步和异步的核心区别是什么？为什么异步适合 Web 请求？**

同步是任务排队，一个做完才做下一个；异步是等待 I/O 时切换去做别的事。Web 请求大量时间花在「等待」（等数据库、等外部 API），异步让 CPU 在等待时去服务其他请求，而不是干等，从而提升吞吐量。

**Q7.2 ⭐⭐ FastAPI 中 `async def` 和普通 `def` 路由如何选择？**

- 函数内调用 `await` 异步操作（异步数据库、httpx）→ 用 `async def`。
- 函数内调用同步阻塞操作（requests、普通数据库驱动）→ 用普通 `def`（FastAPI 自动放到线程池）。
- 纯计算 → 两者皆可。
- **不确定时用普通 `def` 更安全**，FastAPI 会自动处理线程池调度。

**Q7.3 ⭐⭐⭐ 为什么在 `async def` 里调用 `time.sleep()` 是严重错误？**

`async def` 路由直接在事件循环（主线程）中执行。`time.sleep()` 是同步阻塞操作，会**阻塞整个事件循环**，导致其他所有请求都被卡住。正确做法是用 `await asyncio.sleep()`，或者干脆改成普通 `def`（自动进线程池）。这是 FastAPI 异步的「黄金法则」：`async def` 里禁止同步阻塞。

**Q7.4 ⭐⭐ FastAPI 怎么处理普通 `def` 路由函数？**

自动提交到**线程池**执行（等效于 `loop.run_in_executor(None, func)`），即使内部有同步阻塞也不会影响事件循环和其他请求。但线程池有默认大小限制（约 40 线程），高并发下会分批执行。

**Q7.5 ⭐⭐ I/O 密集型和 CPU 密集型任务分别该怎么处理？**

- I/O 密集型（数据库、HTTP、文件）：`async def` + 异步库，获得最佳并发。
- CPU 密集型（图像处理、加密、大数据）：用 `run_in_threadpool`、多进程，或推荐用 Celery、RQ 等**任务队列**异步执行，不要在请求中同步等待。

**Q7.6 ⭐⭐ 主流的异步数据库方案有哪些？**

SQLAlchemy 2.0 async、SQLModel（FastAPI 作者开发）、Tortoise ORM、databases、asyncpg（PostgreSQL 最快驱动）、aiosqlite。异步数据库 + `async def` 可用单线程处理数千并发，不受线程池限制。

---

## 八、数据库集成

**Q8.1 ⭐ SQLAlchemy 集成中 `engine`、`SessionLocal`、`Base` 各是什么？**

- `engine`：数据库引擎，管理连接池。
- `SessionLocal`：会话工厂，每次调用生成一个新的数据库会话。
- `Base`（继承 `DeclarativeBase`）：所有 ORM 模型的基类。

**Q8.2 ⭐⭐ ORM 模型和 Pydantic 模型有什么区别？为什么要分开？**

- ORM 模型（继承 `Base`，用 `mapped_column`）：映射数据库表结构，包含索引、约束等数据库细节。
- Pydantic 模型（继承 `BaseModel`）：定义 API 请求/响应格式，包含校验规则、示例值。

职责不同：一个面向数据库，一个面向接口，分开后各自独立演进。

**Q8.3 ⭐⭐ Pydantic 模型的 `from_attributes = True` 有什么作用？**

让 Pydantic 能从 ORM 对象的**属性**读取数据，而不只是从 dict 读取。没有这个配置，`TodoResponse.model_validate(orm_obj)` 会报错。这是返回 ORM 对象给客户端的关键配置（Pydantic V2 写法，旧版叫 `orm_mode`）。

**Q8.4 ⭐ SQLAlchemy 创建一条记录的标准流程是什么？`refresh` 有什么用？**

`db.add(obj)` → `db.commit()` → `db.refresh(obj)`。`refresh` 用于从数据库重新加载对象，获取数据库生成的字段（如自增 id、`created_at` 等默认值）。

**Q8.5 ⭐⭐ `Base.metadata.create_all()` 有什么局限？为什么生产要用 Alembic？**

`create_all()` 只能创建**不存在的表**，不能修改已有表结构。如果给模型加了新字段，再次启动它发现表已存在就什么都不做，字段加不上。生产环境需要 Alembic 这类迁移工具来管理表结构变更。

**Q8.6 ⭐⭐ Alembic 的核心流程是什么？类比 Git 怎么理解？**

- `revision`（生成迁移脚本）≈ git commit
- `upgrade`（应用变更）≈ git pull
- `downgrade`（回滚）≈ git revert

常用命令：`alembic init`、`alembic revision --autogenerate -m "描述"`、`alembic upgrade head`、`alembic downgrade -1`、`alembic current`、`alembic history`。

**Q8.7 ⭐⭐⭐ Repository / Service 分层架构是什么？各层职责？**

`请求 → Router → Service → Repository → 数据库`：
- **Router**（路由层）：接收请求、参数校验、调用 Service。
- **Service**（服务层）：业务逻辑编排、规则校验、组合多个 Repository。
- **Repository**（仓储层）：纯数据库操作，封装 SQL。

好处：各司其职、路由保持简洁、容易单元测试。

---

## 九、认证与安全

**Q9.1 ⭐ OAuth2 密码模式 + JWT 的认证流程是怎样的？**

三步走：
1. 客户端 `POST /token` 提交用户名密码 → 服务端验证后生成 JWT 返回。
2. 后续请求在 `Authorization: Bearer <token>` 头携带 Token。
3. 服务端验证 JWT 有效性后返回数据。

涉及三个工具：`passlib`（密码哈希）、`python-jose`（JWT 签发/验证）。

**Q9.2 ⭐ 为什么不能存明文密码？用什么处理？**

明文密码一旦数据库泄露后果严重。用 `passlib` + bcrypt 算法做哈希：
- `pwd_context.hash(password)`：注册时明文 → 哈希存储。
- `pwd_context.verify(plain, hashed)`：登录时比较明文与哈希。

bcrypt 每次哈希结果不同（加盐），但 `verify` 能正确匹配。

**Q9.3 ⭐⭐ JWT 由哪几部分组成？`sub` 和 `exp` 是什么？**

JWT = `Header.Payload.Signature`（算法信息.载荷数据.数字签名）。
- `sub`（subject）：标识用户身份，通常是用户名或用户 ID。
- `exp`（expiration）：过期时间，过期后 Token 自动失效。

`jwt.decode()` 会自动校验签名和过期时间。`SECRET_KEY` 是签名密钥，绝不能泄露。

**Q9.4 ⭐⭐ `OAuth2PasswordBearer` 和 `OAuth2PasswordRequestForm` 各是什么？**

- `OAuth2PasswordBearer(tokenUrl="token")`：声明认证方案，告诉 Swagger UI 在哪里登录；注入依赖时自动从请求头提取 `Authorization: Bearer <token>`。
- `OAuth2PasswordRequestForm`：标准 OAuth2 登录表单，含 `username` 和 `password` 字段，作为 `/token` 接口的参数。

**Q9.5 ⭐⭐⭐ `get_current_user` 依赖通常做哪些事？如何用它做权限控制？**

`get_current_user` 是核心认证依赖：解码 Token → 校验 → 查找用户 → 返回用户对象。任何需要认证的接口加 `Depends(get_current_user)` 即可。

权限控制用「依赖工厂」实现：
```python
def require_role(required_role: str):
    async def role_checker(user: User = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(403, detail="权限不足")
        return user
    return role_checker

@app.get("/admin")
async def admin(user=Depends(require_role("admin"))): ...
```
需要多角色时改成 `require_roles(*allowed_roles)`，判断 `role not in allowed_roles`。

**Q9.6 ⭐ 声明了 `tokenUrl` 后，Swagger UI 会有什么变化？**

Swagger UI 右上角会出现 **Authorize** 按钮，输入用户名密码登录后，所有请求会自动携带 Token，方便在文档里测试受保护接口。

---

## 十、项目结构与工程化

**Q10.1 ⭐ `APIRouter` 是什么？`prefix`、`tags`、`dependencies` 各有什么用？**

`APIRouter` 用于按功能模块拆分路由，再用 `app.include_router()` 注册到主应用。
- `prefix`：统一路由前缀（如 `/users`）。
- `tags`：Swagger UI 分组标签。
- `dependencies`：该路由组的公共依赖（如整组接口都要认证）。

**Q10.2 ⭐⭐ 推荐的 FastAPI 项目目录结构是怎样的？**

```
app/
├── main.py          # 入口：创建 app、注册路由
├── config.py        # 配置 BaseSettings
├── database.py      # 数据库连接与会话
├── models/          # SQLAlchemy ORM 模型
├── schemas/         # Pydantic 模型
├── routers/         # 路由模块 APIRouter
├── services/        # 业务逻辑层
└── dependencies/    # 公共依赖
alembic/ tests/ .env requirements.txt
```

**Q10.3 ⭐⭐ 为什么用 `BaseSettings` 管理配置？环境变量映射规则是什么？**

避免把数据库地址、密钥等硬编码到代码里。`BaseSettings`（来自 `pydantic-settings`）自动从环境变量 / `.env` 读取，并做类型转换（字符串 → int/bool/list）。映射规则：Python 字段名自动转大写匹配环境变量，如 `database_url` ↔ `DATABASE_URL`。好处是开发用 `.env`、生产用真实环境变量，**代码不用改**。

**Q10.4 ⭐⭐⭐ `lifespan` 是什么？为什么替代了 `on_event`？**

`lifespan` 是上下文管理器，用于管理应用启动/关闭逻辑：
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：初始化资源（连接池、ML 模型）
    app.state.db_pool = await create_db_pool()
    yield
    # 关闭：清理资源
    await app.state.db_pool.close()

app = FastAPI(lifespan=lifespan)
```
相比已废弃的 `@app.on_event("startup")/("shutdown")`，`lifespan` 把启动和关闭逻辑放在同一函数，用上下文管理器模式确保资源释放，是官方推荐方式。共享资源存在 `app.state`，路由里通过 `request.app.state` 访问。

---

## 十一、测试

**Q11.1 ⭐ `TestClient` 怎么用？它底层依赖什么？**

```python
from fastapi.testclient import TestClient
client = TestClient(app)

def test_create():
    resp = client.post("/items/", json={"name": "手机", "price": 4999})
    assert resp.status_code == 201
    assert resp.json()["name"] == "手机"
```
底层基于 `httpx`，所以需要 `pip install httpx`。常用方法：`client.get/post/put/delete/patch`，断言 `status_code` 和 `json()`。

**Q11.2 ⭐⭐ 测试时不想连真实数据库怎么办？`dependency_overrides` 怎么用？**

用 `app.dependency_overrides` 替换依赖。定义一个测试版的 `get_db`（连测试数据库），然后 `app.dependency_overrides[get_db] = override_get_db`。这样路由里的 `Depends(get_db)` 在测试时就会用测试数据库。同理可覆盖 `get_current_user` 跳过真实登录。

**Q11.3 ⭐⭐ 为什么推荐用 pytest fixture 管理依赖覆盖？**

fixture（放在 `conftest.py`）能为每个测试用例提供独立的测试数据库和客户端，并在测试结束后 `app.dependency_overrides.clear()` 清理覆盖，避免测试之间互相污染。

**Q11.4 ⭐⭐ 什么时候需要 `AsyncClient` 而不是 `TestClient`？**

`TestClient` 是同步的，内部会自动处理异步，**大多数场景够用**。只有在测试异步依赖、异步数据库，或需要精确控制异步执行流程时，才用 `httpx.AsyncClient` + `ASGITransport`，配合 `pytest-asyncio`（`asyncio_mode = "auto"` 可简化写法）。

**Q11.5 ⭐ 一组完整的接口测试通常覆盖哪些情况？**

至少覆盖：创建成功（2xx）、列表查询、单个查询、资源不存在返回 404、参数校验失败返回 422，以及带认证接口的 Token 流程。

---

## 十二、部署上线

**Q12.1 ⭐ 开发环境和生产环境的启动方式有何不同？**

| 项 | 开发 | 生产 |
|----|------|------|
| 命令 | `fastapi dev main.py` | `uvicorn`/`gunicorn` |
| 热重载 | 开启 | 关闭 |
| Worker | 1 个 | 多个（多核） |
| 绑定地址 | 127.0.0.1 | 0.0.0.0 |

**Q12.2 ⭐⭐ Uvicorn 单独部署和 Gunicorn + Uvicorn Worker 有什么区别？**

- Uvicorn `--workers 4`：简单、跨平台（Windows 也能用），但进程管理能力弱。
- Gunicorn + UvicornWorker：进程管理成熟、能自动重启崩溃的 Worker，但**仅支持 Linux/macOS**（Gunicorn 不支持 Windows）。

Worker 数推荐 `CPU 核心数 × 2 + 1`。

**Q12.3 ⭐⭐ Docker 多阶段构建有什么好处？**

builder 阶段安装依赖，运行阶段只复制安装产物（不带 pip 缓存），显著减小镜像体积。配合 `python:3.12-slim` 基础镜像，镜像可从约 1GB 降到约 120MB。再配 `.dockerignore` 排除 `__pycache__`、`.env`、`.git`、`tests/` 等。

**Q12.4 ⭐⭐ 上线前的安全检查清单包含哪些关键项？**

- `DEBUG = False`
- `SECRET_KEY` 换成强随机字符串
- 敏感信息走环境变量，`.env` 加入 `.gitignore`
- CORS `allow_origins` 明确指定域名，不用 `["*"]`
- 多 Worker 启动
- 配置 HTTPS（Nginx + SSL 证书）
- 结构化日志、连接池、健康检查接口 `GET /health`、所有测试通过

**Q12.5 ⭐⭐ 为什么生产用 Nginx 反向代理？流量路径是怎样的？**

`客户端 ──HTTPS──→ Nginx(443) ──HTTP──→ Uvicorn(8000)`。Nginx 负责 SSL 证书终结（HTTPS）、转发请求头（`X-Real-IP`、`X-Forwarded-For`、`X-Forwarded-Proto`）。免费证书可用 Let's Encrypt + certbot 自动申请续期。

---

## 十三、综合 / 场景题

**Q13.1 ⭐⭐ 一个请求从进来到返回，在 FastAPI 里大致经历哪些环节？**

中间件（洋葱外层）→ 路由匹配 → 解析并校验参数（路径/查询/请求体，Pydantic）→ 解析依赖链（`Depends`）→ 执行路由函数（async 在事件循环、普通 def 在线程池）→ 按 `response_model` 序列化 → 中间件（洋葱内层返回）→ 响应客户端。任何环节校验/依赖失败都会提前返回错误。

**Q13.2 ⭐⭐⭐ 设计一个带认证的 Todo API，你会如何分层和组织代码？**

- `schemas/`：`TodoCreate`/`TodoUpdate`/`TodoResponse`（读写分离）、`User`/`Token`。
- `models/`：`Todo`、`User` 的 ORM 模型。
- `dependencies/`：`get_db`（yield 依赖）、`get_current_user`（JWT 解析）、`require_role`。
- `repositories/` + `services/`：数据库操作与业务逻辑分离。
- `routers/`：`auth.py`（登录/注册）、`todos.py`（带 `dependencies=[Depends(get_current_user)]`）。
- `config.py`：`BaseSettings` 管理密钥、数据库地址。
- `main.py`：`lifespan` 初始化、`include_router`、CORS。
- Alembic 管理表结构，pytest + `dependency_overrides` 写测试。

**Q13.3 ⭐⭐ 接口偶发响应很慢、拖垮整个服务，你怎么排查？**

常见根因是 `async def` 路由里混入了同步阻塞操作（`time.sleep`、`requests`、同步数据库驱动、CPU 密集计算），阻塞了事件循环。排查：检查慢接口是不是 `async def` + 同步阻塞；改用 `await` 异步库，或把函数改成普通 `def`（进线程池），CPU 密集任务用 `run_in_threadpool` 或任务队列。可用请求耗时中间件定位慢接口。

**Q13.4 ⭐⭐ 如何保证敏感字段（如密码）不会从接口泄露？**

多重防线：①输入/输出/数据库模型分离（读写分离），`response_model` 只声明可返回字段；②数据库存哈希而非明文；③即使函数返回了完整对象，`response_model` 也会自动过滤掉未声明字段。

**Q13.5 ⭐⭐ 422 和 400 有什么区别？分别什么时候出现？**

- 422：**请求参数校验失败**，由 FastAPI/Pydantic **自动**返回（类型不对、缺必填、约束不满足）。
- 400：**业务逻辑校验失败**，由开发者**手动** `raise HTTPException(400)`（如库存不足、优惠券过期）。

一个是「请求格式不合法」，一个是「格式合法但业务规则不允许」。

---

> **使用建议**：面试前按章节自测，重点关注带 ⭐⭐ / ⭐⭐⭐ 的进阶题（依赖注入、async/await 陷阱、读写分离、JWT 认证、分层架构），这些是 FastAPI 区别于其他框架、也最容易被深挖的考点。
