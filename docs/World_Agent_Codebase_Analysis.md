# World-Agent 全量源码与架构深度解析文档

> **文档说明**：
> 本文档是对 World-Agent 项目当前全量源码的**纯粹深度剖析**（已更新至最新的领域驱动多 Agent 解耦架构）。严格按照物理文件目录结构展开，抛弃了一切修改流水账，直接透视每一个文件的内部真实运作逻辑、安全防范机制，以及文件之间的**调用链路 (Calling Relationships)**。

---

## 1. 系统入口与服务基石 (根目录)

### 1.1 `main.py` (命令行底层入口)
* **调用关系**：直接实例化 `agents.text_processing.TextProcessingAgent` 提供底层驱动。
* **逻辑深度剖析**：
  * **编码抗灾**：执行 `sys.stdout.reconfigure(errors='replace')`，解决 Windows 终端无法渲染大模型输出的特殊 Unicode (如 Emoji) 导致的系统级崩溃。
  * **零配置启动向导**：引入 `dotenv`。当检测到 `API_KEY` 为空时，交互式地接收输入，并利用官方 `openai.OpenAI` 客户端动态请求云端的 `models.list()`，将结果转化为终端选单供用户选择，最终将配置持久化追加至 `.env` 文件。
  * **极简解耦实例化**：在解耦架构下，不再向 Agent 强塞工具和技能列表，只需一行 `TextProcessingAgent()` 即可拉起具有完备专业能力的独立智能体。
  * **异步并发池封装**：利用 `asyncio.run()` 建立事件循环底座，使得传统的 CLI 同步终端能够 `await agent.run()`，实现与后端 LangGraph 的无缝对接。

### 1.2 `server.py` (RESTful 与流式 Web 服务)
* **调用关系**：依赖 `agents.text_processing.TextProcessingAgent`；对前端 `static/app.js` 暴露接口。
* **逻辑深度剖析**：
  * **静态路由隔离**：通过 `FastAPI` 挂载 `/static` 作为前端网页区，挂载 `/workspace` 作为用户文件区，实现系统代码与用户资料的权限分离。
  * **CORS与目录穿越防御**：中间件 `CORSMiddleware` 配置了全局跨域。在 `/api/upload` 接口中，强制使用 `os.path.basename` 抹除文件名中的所有路径层级符号，彻底封堵利用 `../` 进行的目录穿越 (Path Traversal) 渗透攻击。
  * **单例内存与图谱隔离**：维护了一个全局单例 `global_agent`。面对多用户并发，将 `session_id` 包装成 `configurable={"thread_id": session_id}` 交给 LangGraph 内部的 `Checkpointer` 处理状态寻址。
  * **数据爆炸防护**：在 `/api/context` 获取历史记忆时，拦截了过长的数据流，若 `content > 500` 字符则强行截断，防止海量上下文挤爆前端浏览器的 JSON 解析器。

### 1.3 `docker-compose.yml` & 环境配置文件
* **调用关系**：为 `database/connection.py` 提供网络与计算基座。
* **逻辑深度剖析**：
  * **物理隔离墙**：采用 `pgvector/pgvector:pg16` 部署数据库，但通过 `volumes` 将原生数据块死死锁定在隐藏文件夹 `/.docker/pgdata` 中。这避开了 `server.py` 中 `/workspace` 的静态目录暴露，从根本上防止了核心数据库文件被恶意下载。
  * `pyproject.toml` 等作为包管理器，锁死了 `langgraph`, `psycopg[binary]`, `sqlalchemy` 等生态基石。

---

## 2. 领域智能体引擎 (`/agents` 目录)

这是系统重构后的核心亮点，实现了“业务逻辑、专属提示词、专属工具、专属技能”的高度内聚。未来新增的 Agent（如 RAG 问答 Agent）也将以同等规格的独立文件夹并列在此。

### 2.1 文本处理专职模块 (`/agents/text_processing`)
* **定位**：系统的数据加工厂，专职负责对用户长文本进行清洗、切块和格式化，严禁越权处理其他业务。

#### 2.1.1 `agent.py` (核心大脑)
* **逻辑深度剖析 (StateGraph 图灵引擎)**：
  * **内部武器库自组装**：在 `__init__` 时，自主导入专属工具 `TEXT_PROCESSING_TOOLS` 与公用工具 `COMMON_TOOLS`，并向全局 `load_skill` 动态注册自己的专属 `SKILLS`，实现了“即插即用”。
  * **状态共享白板 (`AgentState`)**：继承 `TypedDict`，持有一个受 `add_messages` Reducer 控制的队列，强制每次对话追加而不覆盖。
  * **防 OOM 截断防御**：执行工具时，如果本地工具返回字符串超 10万 字符，会立刻暴力截断，防止大模型因 Token 爆炸引发内存溢出。
  * **自驱路由与流式解包**：通过 `should_continue` 构建 ReAct 闭环；通过 `run_generator` 截获图执行的 `on_chat_model_stream` 和 `on_tool_start`，将底层思维过程 JSON 化实时推给前端。

#### 2.1.2 `prompts.py`
* **逻辑深度剖析**：静态储存该 Agent 的人设。强制执行苛刻的 CoT (思维链)：【意图拆解 -> 技能匹配 -> 现状评估 -> 决断交互】。利用 `{skills_injection}` 占位符实现专属技能的动态装载。

#### 2.1.3 `skills/` (专属技能库)
* 包含 `data_cleaning.py` 与 `smart_chunking.py`。
* **逻辑深度剖析**：纯自然语言编写的 SOP（标准作业程序）。`data_cleaning` 规定了高警戒度的防盗版挂起逻辑；`smart_chunking` 规定了正则切分前必须进行沙盘推演。这些技能只对文本处理 Agent 可见。

#### 2.1.4 `tools/` (专属沙盒工具箱)
* 包含 `chunk_text`, `clean_text`, `json_to_txt`, `write_file` 等。
* **逻辑深度剖析**：
  * **写权限绝对沙箱**：如 `write_file.py`，底层通过 `os.path.commonpath` 严格拦截，**强制所有的加工结果只能写入 `workspace/output`**。彻底杜绝污染原始文件 (`workspace/input`)。
  * **反正则灾难 (`clean_text.py`)**：内嵌 Anti-ReDoS 防护，单行超过 5000 字符强制放弃正则比对，避免系统 CPU 死锁。

---

## 3. 公共基础设施 (`/common/tools` 目录)

为所有 Agent 提供的跨领域共享 API，相当于系统的底盘。

### 3.1 系统级干涉与动态加载 (`/system/`)
* **逻辑深度剖析**：
  * **`list_dir.py` & `read_file.py` (项目级读取)**：
    * 采用 `os.path.commonpath` 防止 `../` 目录穿越。其权限开放至整个项目根目录，允许 Agent 在必要时读取系统源码进行调试。
    * 文件过大 (100KB+) 时，`read_file` 强制锁死读取，要求模型出示 `force_read=True` 密令方可放行。
  * **`load_skill.py` (高阶动态装载机制)**：
    * **核心解耦点**：抛弃了旧版的硬编码全局导入。它维护了一个全局的空列表 `_REGISTERED_SKILLS`，暴露出 `register_skills()` 方法。
    * 当不同的 Agent（如文本 Agent 或未来的 RAG Agent）实例化时，会将自己的技能列表注入。因此大模型使用同一个 `load_skill_sop` 工具，就能精准地拿到**只属于自己领域的专属 SOP**。

### 3.2 外接网络感官 (`/network/`)
* **逻辑深度剖析**：包含 `web_search.py`，内部封装轻量级爬虫。在任一 Agent 遇到知识盲区需要公网数据补充时，均可调用发起嗅探。

---

## 4. 关系与向量混合存储引擎 (`/database` 目录)

为后续 RAG Agent 预留的海量语料存储枢纽。

### 4.1 `connection.py`
* **逻辑深度剖析**：
  * 采用 `SQLAlchemy` 对象关系映射器。
  * 开启了 `pool_pre_ping=True` 这一核心特性。即“悲观重连”，在每次检出连接前强制发送 `SELECT 1` 探测 PostgreSQL 服务是否健康。一旦探知 Docker 闪断，自动丢弃死连接重建，杜绝僵死。
  * 提供基于生成器的 `SessionLocal`，保障高并发事务。

---

## 5. 前端渲染控制台 (`/static` 目录)

系统的最终视觉与交互呈现。

### 5.1 `app.js` & `index.html`
* **逻辑深度剖析**：
  * **SSE 监听与解包机制**：针对后端的长连接流式 `type`：遇到 `thought` 则刷新思考进度；遇到 `action` 触发工具闪烁提示；只有遇到 `answer` 才写入屏幕主轨道，形成平滑的视觉心智模型。
  * **终极 XSS 防火墙 (`escapeHTML`)**：哪怕后端模型失控生成恶意的 `<script>`，在插入 DOM 树之前，都会被正则表达式洗刷为纯文本。前端安全性在此闭环。
