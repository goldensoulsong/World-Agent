# World-Agent 项目开发规则 (Project Rules)

> **文档定位**：本文档是 World-Agent 项目的权威开发规范。所有贡献者（包括人类开发者和 AI 编码助手）在修改代码之前**必须**阅读并遵守本文档。

---

## 1. 项目概览

World-Agent 是一个基于 LangGraph ReAct 架构的 AI Agent 框架，支持文本处理、RAG 知识库、Web 搜索等能力。项目采用 Python 后端 (FastAPI) + React 前端 (Vite) 的分离架构。

### 技术栈

| 层级 | 技术 | 版本要求 |
|------|------|----------|
| 运行时 | Python | >= 3.12 |
| 包管理 | uv + pyproject.toml | 唯一依赖声明源 |
| 后端框架 | FastAPI + Uvicorn | >= 0.110.0 |
| Agent 框架 | LangGraph + LangChain | >= 0.2.0 |
| 数据库 | PostgreSQL 16 + pgvector | Docker 部署 |
| 前端 | React 18 + Vite 5 | JSX (非 TypeScript) |
| 前端样式 | 原生 CSS | 单文件 `index.css` |

---

## 2. 目录结构规范

```
World-Agent/
│
├── main.py                  # CLI 终端入口（仅用于终端交互调试）
├── server.py                # Web 服务入口（FastAPI，生产入口）
├── start.bat                # Windows 一键启动脚本
├── pyproject.toml           # 唯一的依赖声明文件
├── uv.lock                  # uv 锁文件
├── docker-compose.yml       # 数据库容器编排
├── .env                     # 环境变量（不提交 Git）
├── .env.example             # 环境变量模板（提交 Git）
│
├── agents/                  # 🧠 领域 Agent 模块（每个 Agent 一个子目录）
│   └── <agent_name>/
│       ├── __init__.py
│       ├── agent.py         # Agent 核心（StateGraph 构建）
│       ├── prompts.py       # 提示词集中管理
│       ├── skills/          # 专属技能 SOP（自然语言）
│       └── tools/           # 专属工具（仅本 Agent 可用）
│
├── common/                  # 🔧 跨 Agent 公共模块
│   ├── rag/                 # RAG 底层能力（Embedding、向量存储）
│   └── tools/               # 公共工具库
│       ├── system/          # 系统工具（文件读写、目录浏览、技能加载）
│       ├── network/         # 网络工具（Web 搜索）
│       └── rag/             # RAG 工具（知识库增删查）
│
├── database/                # 🗄️ 数据库层
│   ├── connection.py        # SQLAlchemy 连接与会话工厂
│   ├── models.py            # ORM 模型定义
│   └── alembic/             # 数据库迁移
│
├── data/                    # 📦 运行时数据（不提交 Git）
│   └── chats/               # 聊天记录 JSON 文件
│
├── workspace/               # 📂 用户工作区（不提交 Git）
│   ├── input/               # 用户上传的原始文件
│   └── output/              # Agent 处理后的输出文件
│
├── frontend/                # 🎨 前端源码
│   └── src/
│       ├── App.jsx          # 根组件
│       ├── main.jsx         # ReactDOM 入口
│       ├── index.css        # 全局样式
│       └── components/      # UI 组件
│
├── static/                  # 📤 前端构建产物（Vite build 输出）
│
├── tests/                   # 🧪 测试文件
│
└── docs/                    # 📖 项目文档
```

### 目录职责边界（严禁违反）

| 规则 | 说明 |
|------|------|
| `agents/<name>/tools/` | 仅存放该 Agent **专属**的工具，不可被其他 Agent 导入 |
| `common/tools/` | 仅存放**所有 Agent 共享**的工具 |
| `workspace/input/` | **只读**区域，Agent 禁止对原始文件进行任何写操作 |
| `workspace/output/` | **唯一写入**区域，Agent 所有输出必须写入此处 |
| `static/` | 由 `frontend/` 构建自动生成，**禁止手动修改** |
| `data/` | 运行时数据，禁止提交到 Git |

---

## 3. 新增 Agent 规范

当需要创建新的 Agent 时，必须按以下模板操作：

### 3.1 目录结构

```
agents/
└── <new_agent_name>/
    ├── __init__.py           # 导出 Agent 类
    ├── agent.py              # 核心：继承 StateGraph 模式
    ├── prompts.py            # 所有提示词集中存放
    ├── skills/               # 可选：SOP 技能文件
    │   └── __init__.py
    └── tools/                # 可选：专属工具
        └── __init__.py
```

### 3.2 必须遵守的模式

1. **内聚自组装**：Agent 在 `__init__` 中自主导入自己的 tools 和 skills，再与 `common/tools` 合并
2. **注册到顶层**：在 `agents/__init__.py` 中导出新 Agent 类
3. **提示词分离**：禁止在 `agent.py` 中写大段提示词字符串，必须放在 `prompts.py`
4. **技能隔离**：调用 `clear_skills()` + `register_skills()` 确保不同 Agent 技能不交叉污染

### 3.3 代码模板

```python
# agents/<new_agent>/agent.py
class NewAgent:
    def __init__(self, system_prompt: str = None, max_loops: int = 20):
        # 1. 导入专属 + 公共工具
        from .tools import MY_TOOLS_SCHEMA, MY_AVAILABLE_TOOLS
        from common.tools import COMMON_TOOLS_SCHEMA, COMMON_AVAILABLE_TOOLS, register_skills, clear_skills
        
        # 2. 合并工具集
        self.available_tools = {**MY_AVAILABLE_TOOLS, **COMMON_AVAILABLE_TOOLS}
        tools_schema = MY_TOOLS_SCHEMA + COMMON_TOOLS_SCHEMA
        
        # 3. 注册专属技能（可选）
        clear_skills()
        register_skills(MY_SKILLS)
        
        # 4. 构建 LangGraph StateGraph...
```

---

## 4. 新增工具规范

### 4.1 工具结构

每个工具是一个独立子目录，包含：

```
tools/
└── <tool_name>/
    ├── __init__.py           # 导出函数和 Schema
    └── <tool_name>.py        # 实现代码
```

### 4.2 Schema 标准格式

```python
TOOL_NAME_SCHEMA = {
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "工具的用途描述（中文，给大模型看的）",
        "parameters": {
            "type": "object",
            "properties": {
                "intent_analysis": {
                    "type": "string",
                    "description": "【第一步意图拆解(必须)】：为什么要调用这个工具？"
                },
                # ... 业务参数
            },
            "required": ["intent_analysis", ...],
        },
    }
}
```

### 4.3 工具开发规则

| 规则 | 详情 |
|------|------|
| **意图拆解字段** | 所有工具 Schema 必须包含 `intent_analysis` 参数，强制大模型先思考再调用 |
| **返回值格式** | 统一返回 `json.dumps({...}, ensure_ascii=False)` 字符串 |
| **路径安全** | 涉及文件操作的工具，必须使用 `os.path.commonpath` 做路径穿越防御 |
| **大数据截断** | 返回内容超过 100KB 时，必须截断并附加 `[截断]` 提示 |
| **大文件保护** | 读取文件超过 100KB 时，需要 `force_read=True` 参数确认 |
| **注册到 `__init__.py`** | 工具函数和 Schema 必须在 `__init__.py` 中统一导出 |

---

## 5. 安全规则（红线）

> [!CAUTION]
> 以下规则为安全底线，任何代码修改不得违反。

### 5.1 文件系统安全

- Agent 的写操作**必须**被沙箱限制在 `workspace/output/` 内
- 所有路径验证使用 `os.path.commonpath()`，禁止仅用 `startswith()` 做防御
- 上传文件必须经过 `os.path.basename()` 清洗文件名
- 禁止 Agent 读取 `.env`、`database/` 等敏感目录

### 5.2 前端安全

- 所有大模型输出在插入 DOM 前，必须经过 HTML 转义（防 XSS）
- 使用 `marked` 等 Markdown 渲染库时，必须关闭 HTML 直出
- 前端只信任 SSE 流中 `type: answer` 的最终结果

### 5.3 密钥与凭证

- API Key 只能存放在 `.env` 文件中，禁止硬编码
- `.env` 已被 `.gitignore` 排除，提交前务必确认
- `docker-compose.yml` 中的数据库密码使用 `${ENV_VAR:-default}` 语法
- 对外提供 `.env.example` 模板，占位符值不得包含真实密钥

### 5.4 数据防爆

- Agent 工具层：返回内容超 100,000 字符时强制截断
- SSE 流式层：发送前端的 observation 超 1,000 字符时做展示折叠
- Context API：历史消息中单条超 500 字符时截断
- 正则操作：单行超 5,000 字符时跳过正则（防 ReDoS）

---

## 6. 前端开发规范

### 6.1 架构约定

| 项目 | 约定 |
|------|------|
| 构建工具 | Vite 5，配置在 `frontend/vite.config.js` |
| 构建输出 | `../static/` (即项目根目录的 `static/` 文件夹) |
| 静态路径前缀 | `/static/` |
| API 代理 | 开发模式下 Vite 代理 `/api` 和 `/workspace` 到 `http://127.0.0.1:8080` |
| 样式方案 | 单一 `index.css` 文件，原生 CSS 变量驱动主题 |

### 6.2 组件规范

- 所有组件放在 `frontend/src/components/` 下
- 一个文件一个组件，文件名使用 PascalCase（如 `ChatTerminal.jsx`）
- 禁止在组件中直接写内联样式，所有样式走 `index.css` 的 CSS 类

### 6.3 构建与部署

```bash
# 开发模式（热重载）
cd frontend && npm run dev

# 构建生产版本（输出到 static/）
cd frontend && npm run build

# 生产运行（后端提供静态服务）
python server.py
# 或双击 start.bat
```

---

## 7. 后端 API 规范

### 7.1 路由命名

| 前缀 | 用途 | 示例 |
|------|------|------|
| `/api/` | 所有业务 API | `/api/chat`, `/api/files` |
| `/static/` | 前端静态资源 | `/static/index.html` |
| `/workspace/` | 用户文件访问 | `/workspace/output/result.txt` |

### 7.2 SSE 流式协议

后端 `/api/chat` 返回 SSE 流，每条消息格式为：

```
data: {"type": "<type>", "content": "<content>"}\n\n
```

| type | 含义 | 前端处理 |
|------|------|----------|
| `thought` | 大模型思考过程的文本 Token | 实时刷新思考区 |
| `action` | 工具调用事件（含 function 和 args） | 展示工具调用提示 |
| `observation` | 工具返回结果 | 展示工具结果（可折叠） |
| `answer` | 最终清洗后的回答 | 写入主对话区 |
| `error` | 运行错误 | 展示错误提示 |

---

## 8. 依赖管理规则

### 8.1 Python 依赖

- **唯一声明源**：`pyproject.toml`，禁止单独维护 `requirements.txt`
- **包管理器**：推荐使用 `uv`，兼容 `pip install -e .`
- **新增依赖**：修改 `pyproject.toml` → 运行 `uv lock` → 提交 `uv.lock`

```bash
# 添加新依赖
uv add <package_name>

# 同步环境
uv sync
```

### 8.2 前端依赖

- 使用 `npm` 管理
- 新增依赖后提交 `package-lock.json`
- `node_modules/` 永远不提交

---

## 9. Git 提交规范

### 9.1 绝不提交的内容

以下内容已在 `.gitignore` 中配置，确保永不泄露：

```
.env                    # API 密钥
__pycache__/            # Python 缓存
.venv/                  # 虚拟环境
node_modules/           # 前端依赖
frontend/dist/          # 前端中间产物
static/assets/          # 构建产物
.docker/                # 数据库持久化数据
data/chats/             # 聊天记录
workspace/input/*       # 用户上传文件
workspace/output/*      # Agent 输出文件
```

### 9.2 Commit Message 格式

```
<类型>: <简要描述>

<可选的详细说明>
```

**类型列表**：

| 类型 | 用途 |
|------|------|
| `feat` | 新功能 |
| `fix` | 修复 bug |
| `refactor` | 重构（不改变外部行为） |
| `security` | 安全相关修改 |
| `docs` | 文档变更 |
| `style` | 代码格式、CSS 样式 |
| `chore` | 构建工具、依赖管理等杂务 |

### 9.3 文档同步

- 重要代码修改必须在 `docs/Modification_Record.md` 中追加记录
- 架构变更后需同步更新 `docs/World_Agent_Codebase_Analysis.md`
- 本文档 (`docs/PROJECT_RULES.md`) 在规则发生变化时必须同步更新

---

## 10. 测试规范

- 测试文件统一放在 `tests/` 目录下
- 文件命名：`test_<模块名>.py`
- 临时调试脚本也放在 `tests/` 下，命名加 `scratch_` 前缀

---

## 11. 环境配置清单

### 首次搭建

```bash
# 1. 复制环境变量模板
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 2. 启动数据库
docker compose up -d

# 3. 安装 Python 依赖
uv sync

# 4. 安装前端依赖 & 构建
cd frontend && npm install && npm run build && cd ..

# 5. 启动服务
uv run server.py
# 或直接双击 start.bat
```

### 访问地址

| 环境 | URL |
|------|-----|
| 生产模式 | `http://127.0.0.1:8080/static/index.html` |
| 前端开发模式 | `http://localhost:5173` |

---

*最后更新：2026-06-08*
