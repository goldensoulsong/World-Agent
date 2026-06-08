import os
import uvicorn
import mimetypes
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from agents.text_processing import TextProcessingAgent

# Fix MIME types for Windows registry issues
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

load_dotenv(override=True)

app = FastAPI(title="World-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保工作区目录存在
os.makedirs("workspace/input", exist_ok=True)
os.makedirs("workspace/output", exist_ok=True)

# 挂载前端静态文件
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static", html=True), name="static")
app.mount("/workspace", StaticFiles(directory="workspace"), name="workspace")

# 全局唯一的 Graph Agent 实例 (多用户通过 thread_id 隔离)
global_agent = None

def get_agent():
    global global_agent
    if global_agent is None:
        global_agent = TextProcessingAgent(max_loops=20)
    return global_agent

@app.get("/api/files")
def list_files():
    """获取 workspace 目录下的文件树（包含子文件夹）"""
    def get_dir_files(dir_path):
        if not os.path.exists(dir_path): return []
        file_list = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file == ".gitkeep" or file.startswith(".git"):
                    continue
                # 把 windows 的反斜杠转成正斜杠，用于 URL
                rel_path = os.path.relpath(os.path.join(root, file), start=".")
                rel_path = rel_path.replace("\\", "/")
                file_list.append({"name": file, "path": rel_path})
        return file_list
        
    return {
        "input": get_dir_files("workspace/input"),
        "output": get_dir_files("workspace/output")
    }

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件到 workspace/input"""
    safe_filename = os.path.basename(file.filename)
    file_location = f"workspace/input/{safe_filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    return {"info": f"文件 '{safe_filename}' 保存成功。"}

@app.delete("/api/files")
async def delete_file(path: str):
    """删除 workspace 目录下的文件"""
    # 防止路径穿越
    if ".." in path or not path.startswith("workspace/"):
        return JSONResponse(status_code=400, content={"error": "无效或不允许的文件路径。"})
    
    file_path = os.path.abspath(path)
    workspace_dir = os.path.abspath("workspace")
    if not file_path.startswith(workspace_dir):
        return JSONResponse(status_code=400, content={"error": "越权访问拒绝。"})
        
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return {"info": "文件删除成功。"}
        else:
            return JSONResponse(status_code=404, content={"error": "文件不存在。"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"删除失败: {str(e)}"})

class ChatRequest(BaseModel):
    query: str
    session_id: str = "default"

@app.post("/api/chat")
async def chat_stream(request: ChatRequest):
    """SSE 流式对话接口"""
    agent = get_agent()
    return StreamingResponse(agent.run_generator(request.query, session_id=request.session_id), media_type="text/event-stream")

@app.get("/api/context")
def get_context(session_id: str = "default"):
    """获取当前的上下文记忆，展现完整的 I/O 级别 Input（不做任何截断）"""
    filepath = os.path.join("data", "chats", f"{session_id}.json")
    clean_history = []
    
    # 1. 提取当前真正在底层生效的总 System Prompt
    try:
        agent = get_agent()
        system_prompt = getattr(agent, "system_prompt", "")
        if system_prompt:
            clean_history.append({
                "role": "system",
                "content": system_prompt
            })
    except Exception as e:
        print(f"Failed to load system prompt: {e}")
        
    # 2. 提取后续的历史对话（完整内容，不截断）
    if os.path.exists(filepath):
        try:
            import json
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            messages = data.get("messages", [])
            for msg in messages:
                role = msg.get("role", "user")
                if role == "human": role = "user"
                elif role == "ai": role = "assistant"
                
                content = msg.get("content", "")
                clean_history.append({"role": role, "content": content})
        except Exception as e:
            print(f"Failed to load context for {session_id}: {e}")
            
    return {"history": clean_history}


@app.get("/api/logs/{session_id}")
def get_logs(session_id: str):
    """获取原始 I/O 日志（完整的发送/接收内容）"""
    filepath = os.path.join("data", "logs", f"{session_id}.jsonl")
    if not os.path.exists(filepath):
        return {"logs": []}
    
    try:
        import json
        logs = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    logs.append(json.loads(line))
        return {"logs": logs}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"读取日志失败: {str(e)}"})


@app.get("/api/trace/{session_id}")
def get_trace(session_id: str):
    """获取完整交互追踪（所有轮次的关键节点事件）"""
    filepath = os.path.join("data", "traces", f"{session_id}.jsonl")
    if not os.path.exists(filepath):
        return {"traces": [], "rounds": []}
    
    try:
        import json
        all_events = []
        rounds = {}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    event = json.loads(line)
                    all_events.append(event)
                    # 按 round_id 分组
                    rid = event.get("round_id", "unknown")
                    if rid not in rounds:
                        rounds[rid] = []
                    rounds[rid].append(event)
        
        # 将 rounds 转为有序列表
        round_list = []
        for rid, events in rounds.items():
            round_list.append({
                "round_id": rid,
                "events": events,
                "started_at": events[0]["timestamp"] if events else ""
            })
        
        return {"traces": all_events, "rounds": round_list}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"读取追踪失败: {str(e)}"})


# ----------------- Chat History APIs -----------------

CHATS_DIR = "data/chats"
os.makedirs(CHATS_DIR, exist_ok=True)

class ChatSessionData(BaseModel):
    title: str
    updated_at: str
    messages: list

@app.get("/api/chats")
def list_chats():
    """获取所有本地保存的聊天记录"""
    chats = []
    if not os.path.exists(CHATS_DIR):
        return {"chats": chats}
        
    for filename in os.listdir(CHATS_DIR):
        if filename.endswith(".json"):
            session_id = filename[:-5]
            filepath = os.path.join(CHATS_DIR, filename)
            try:
                import json
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                chats.append({
                    "id": session_id,
                    "title": data.get("title", "新对话"),
                    "updated_at": data.get("updated_at", "")
                })
            except Exception as e:
                print(f"Error loading {filepath}: {e}")
                
    # 按时间倒序排序
    chats.sort(key=lambda x: x["updated_at"], reverse=True)
    return {"chats": chats}

@app.get("/api/chats/{session_id}")
def get_chat(session_id: str):
    """获取单个聊天记录明细"""
    filepath = os.path.join(CHATS_DIR, f"{session_id}.json")
    if os.path.exists(filepath):
        try:
            import json
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": f"加载失败: {str(e)}"})
    return JSONResponse(status_code=404, content={"error": "记录不存在"})

@app.post("/api/chats/{session_id}")
def save_chat(session_id: str, data: ChatSessionData):
    """保存聊天记录"""
    filepath = os.path.join(CHATS_DIR, f"{session_id}.json")
    try:
        import json
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data.model_dump(), f, ensure_ascii=False, indent=2)
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"保存失败: {str(e)}"})

@app.delete("/api/chats/{session_id}")
def delete_chat(session_id: str):
    """删除聊天记录"""
    filepath = os.path.join(CHATS_DIR, f"{session_id}.json")
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return {"status": "success"}
        return JSONResponse(status_code=404, content={"error": "记录不存在"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"删除失败: {str(e)}"})



# ----------------- Settings APIs -----------------

class ConfigData(BaseModel):
    api_key: str
    base_url: str
    model_name: str

@app.get("/api/config")
def get_config():
    """获取当前配置"""
    return {
        "api_key": os.getenv("API_KEY", ""),
        "base_url": os.getenv("BASE_URL", ""),
        "model_name": os.getenv("MODEL_NAME", "deepseek-chat")
    }

@app.post("/api/config")
def update_config(data: ConfigData):
    """更新配置并热重载 Agent"""
    # 1. 更新当前进程环境变量
    os.environ["API_KEY"] = data.api_key
    os.environ["BASE_URL"] = data.base_url
    os.environ["MODEL_NAME"] = data.model_name
    
    # 2. 写入 .env 文件持久化
    with open(".env", "w", encoding="utf-8") as f:
        f.write(f'API_KEY="{data.api_key}"\n')
        f.write(f'BASE_URL="{data.base_url}"\n')
        f.write(f'MODEL_NAME="{data.model_name}"\n')
        
    # 3. 清空全局 Agent 实例，强制下次请求时重建（使新配置生效）
    global global_agent
    global_agent = None
    
    return {"status": "success", "message": "配置已保存并热重载生效"}

class ModelsRequest(BaseModel):
    api_key: str = ""
    base_url: str = ""

@app.post("/api/models")
def get_models(data: ModelsRequest):
    """动态拉取模型列表"""
    api_key = data.api_key if data.api_key else os.getenv("API_KEY", "")
    base_url = data.base_url if data.base_url else os.getenv("BASE_URL", "")
        
    try:
        client = OpenAI(
            api_key=api_key, 
            base_url=base_url if base_url else None
        )
        models = client.models.list()
        # OpenAI 返回的模型列表在 data 属性里
        model_names = [m.id for m in models.data]
        return {"models": model_names}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"拉取失败: {str(e)}"})

if __name__ == "__main__":
    print("启动 Web 界面，访问 http://127.0.0.1:8080/static/index.html")
    uvicorn.run(app, host="127.0.0.1", port=8080)
