import os
import json

LIST_DIR_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_dir",
        "description": "查询/列出指定目录下的文件和文件夹列表。",
        "parameters": {
            "type": "object",
            "properties": {
                "intent_analysis": {
                    "type": "string",
                    "description": "【第一步意图拆解(必须)】：为什么要列出这个目录？想要找什么？"
                },
                "dir_path": {
                    "type": "string",
                    "description": "目录的绝对路径或相对路径",
                }
            },
            "required": ["intent_analysis", "dir_path"],
        },
    }
}

def list_dir(dir_path: str) -> str:
    """
    列出目录内容
    """
    try:
        base_dir = os.path.abspath(os.getcwd())
        
        # 智能防呆补全：如果 Agent 偷懒只传了 input 或 output，自动映射到 workspace 下
        clean_path = dir_path.strip(" /\\")
        if clean_path in ["input", "output"] or clean_path.startswith("input/") or clean_path.startswith("output/"):
            dir_path = os.path.join("workspace", dir_path)
            
        target_path = os.path.abspath(dir_path)
        
        if not target_path.startswith(base_dir):
            return json.dumps({"error": "【安全拦截】：越权访问！你只能查询当前项目根目录下的目录！"}, ensure_ascii=False)
            
        if not os.path.exists(target_path):
            return json.dumps({"error": f"目录不存在: {target_path}"}, ensure_ascii=False)
            
        if not os.path.isdir(target_path):
            return json.dumps({"error": f"不是一个目录: {target_path}"}, ensure_ascii=False)
            
        files = os.listdir(target_path)
        return json.dumps({"type": "directory", "path": target_path, "contents": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"查询失败: {str(e)}"}, ensure_ascii=False)
