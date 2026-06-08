# World-Agent 源码更改解析记录 (Modification Record)

> **文档说明**：
> 本文档用于持续追踪和记录对 World-Agent 源码的每一次重要修改。后续的每一次重构、修复或功能开发，都将在此文档中新增记录，以确保代码演进的透明性和可追溯性。

---

## [2026-06-06] 架构升级与安全漏洞修复

### 1. 核心架构重构 (异步并发与会话隔离)
- **修改文件**：`core/text_processing_agent.py`
  - **更改解析**：将底层的同步 `OpenAI` 客户端整体替换为 `AsyncOpenAI`，并将 `run` 和 `run_generator` 方法升级为 `async def` 协程，解决了高并发场景下事件循环阻塞的问题。同时引入了长度限制为 30 的滑动窗口记忆截断机制，防止 Token 消耗过大。
- **修改文件**：`server.py`
  - **更改解析**：移除了全局单例 `agent_instance`，采用 `sessions = {}` 字典池对多用户请求进行状态隔离，解决了多用户上下文串流的问题。
- **修改文件**：`main.py`
  - **更改解析**：为兼容底层异步化修改，引入了 `asyncio` 事件循环（`asyncio.run`），确保命令行界面（CLI）能够正确 `await` Agent 的返回结果。

### 2. 安全漏洞防范 (越权与 XSS)
- **修改文件**：`server.py`
  - **更改解析**：修复了 CORS 配置冲突（`allow_credentials` 设为 `False`）。在 `/api/upload` 路由中强制使用 `os.path.basename` 处理上传文件名，防止恶意构造 `../` 的路径穿越攻击。
- **修改文件**：`tool/system/read_file/read_file.py` & `tool/system/list_dir/list_dir.py`
  - **更改解析**：将原本薄弱的前缀匹配防御升级为严格的物理路径计算：`os.path.commonpath([base_dir, target_path])`，彻底阻断了 Agent 操作 `workspace` 之外系统文件的可能性。
- **修改文件**：`static/app.js`
  - **更改解析**：新增 `escapeHTML` 转义函数，在渲染大模型返回的文本前，对 `<`、`>`、`&` 等 HTML 元字符进行过滤，杜绝前端跨站脚本注入（XSS）风险。同时引入了基于 `sessionStorage` 的身份标识生成逻辑。

### 3. 环境配置标准化
- **修改文件**：`pyproject.toml` & `requirements.txt`
  - **更改解析**：将缺失的 `fastapi`、`uvicorn`、`python-multipart` 补齐至正规的包管理清单中，实现依赖的声明式固化，防止不同环境下因手动安装遗漏而导致的启动失败。

---

## [2026-06-06] LangGraph 状态机重构与 PostgreSQL 混合交火基座建设

### 1. 核心底座重构 (LangGraph StateGraph 引入)
- **修改文件**：`core/text_processing_agent.py`
  - **更改解析**：彻底废弃原基于 `while` 循环的原生 ReAct 机制。引入 `langgraph` 与 `langchain-openai`，将底座重构为标准的 `StateGraph`。定义了 `AgentState` 作为多 Agent 共享的全局大白板（包含 `messages` 归约器）；定义了 `call_model`（大模型节点）与 `execute_tools`（工具节点），并通过条件边（Conditional Edges）实现循环与退出判断。
- **修改文件**：`server.py`
  - **更改解析**：重构会话隔离逻辑。移除庞大的 `sessions = {}` 字典池，改为全局单例 `global_agent`。多用户并发与记忆隔离交由 LangGraph 的 `MemorySaver`（Checkpointer）基于 `thread_id` 自动管理。

### 2. SSE 前端全兼容适配
- **修改文件**：`core/text_processing_agent.py`
  - **更改解析**：重写 `run_generator` 方法。不再拦截原生 OpenAI SDK 输出，而是拦截 `workflow.astream_events(version="v2")` 的图运行底层事件。将 `on_chat_model_stream`, `on_tool_start`, `on_tool_end` 等事件解包，翻译并封装回旧版前端识别的 `thought`, `action`, `observation` JSON 格式，实现了前后端剥离下的零感知平滑升级。

### 3. RAG 混合交火数据库基座 (基础设施部署)
- **新增文件**：`docker-compose.yml`
  - **更改解析**：引入官方 `pgvector/pgvector:pg16` 镜像部署 PostgreSQL 环境。设置安全数据卷挂载至工程根目录下的隐藏目录 `.docker/pgdata`，避免数据库内部物理文件暴露在前端静态挂载目录（`workspace/`）中引发越权下载漏洞。
- **修改文件**：`pyproject.toml` & `requirements.txt` & `.env`
  - **更改解析**：引入 `sqlalchemy`, `psycopg[binary]`, `pgvector` 等依赖，并在 `.env` 中初始化 `DATABASE_URL`，为下一阶段 RAG 开发中“关系型表与向量表双写分离与物理聚合”的方案打牢基座。
- **新增文件**：`database/connection.py`
  - **更改解析**：实现带有自动重连、连接池机制的 SQLAlchemy Engine 与 Session 工厂配置。

---

*(后续更改将在此基础之上继续追加)*
