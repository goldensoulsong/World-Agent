import os
import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI

from core.react_agent import ReActAgent
from core.prompts import MASTER_AGENT_PROMPT
from skill import ALL_SKILLS
from tool import TOOLS_SCHEMA, AVAILABLE_TOOLS

load_dotenv(override=True)

app = FastAPI(title="World-Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
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

# 全局单例 Agent
agent_instance = None

def get_agent():
    global agent_instance
    if agent_instance is None:
        agent_instance = ReActAgent(
            system_prompt=MASTER_AGENT_PROMPT,
            tools_schema=TOOLS_SCHEMA,
            available_tools=AVAILABLE_TOOLS,
            max_loops=20,
            skills=ALL_SKILLS
        )
    return agent_instance

@app.get("/api/files")
def list_files():
    """获取 workspace 目录下的文件树（包含子文件夹）"""
    def get_dir_files(dir_path):
        if not os.path.exists(dir_path): return []
        file_list = []
        for root, _, files in os.walk(dir_path):
            for file in files:
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
    file_location = f"workspace/input/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(await file.read())
    return {"info": f"文件 '{file.filename}' 保存成功。"}

@app.get("/api/chat")
async def chat_stream(query: str):
    """SSE 流式对话接口"""
    agent = get_agent()
    return StreamingResponse(agent.run_generator(query), media_type="text/event-stream")

@app.get("/api/context")
def get_context():
    """获取当前的上下文记忆"""
    agent = get_agent()
    # 过滤掉内容过长的数据，防止传输爆炸
    clean_history = []
    for msg in agent.chat_history:
        if isinstance(msg, dict):
            # dict格式
            content = msg.get("content", "")
            if isinstance(content, str) and len(content) > 500:
                msg_copy = msg.copy()
                msg_copy["content"] = content[:500] + "...[内容过长已折叠]"
                clean_history.append(msg_copy)
            else:
                clean_history.append(msg)
        else:
            # Pydantic model (ChatCompletionMessage)
            msg_dict = msg.model_dump()
            content = msg_dict.get("content") or ""
            if len(content) > 500:
                msg_dict["content"] = content[:500] + "...[内容过长已折叠]"
            clean_history.append(msg_dict)
            
    return {"history": clean_history}

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
        
    # 3. 销毁全局 Agent 实例，强制下次请求时重建
    global agent_instance
    agent_instance = None
    
    return {"status": "success", "message": "配置已保存并热重载生效"}

@app.get("/api/models")
def get_models(api_key: str = "", base_url: str = ""):
    """动态拉取模型列表"""
    if not api_key:
        api_key = os.getenv("API_KEY", "")
    if not base_url:
        base_url = os.getenv("BASE_URL", "")
        
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        models = client.models.list()
        # OpenAI 返回的模型列表在 data 属性里
        model_names = [m.id for m in models.data]
        return {"models": model_names}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": f"拉取失败: {str(e)}"})

if __name__ == "__main__":
    print("启动 Web 界面，访问 http://127.0.0.1:8080/static/index.html")
    uvicorn.run(app, host="127.0.0.1", port=8080)
