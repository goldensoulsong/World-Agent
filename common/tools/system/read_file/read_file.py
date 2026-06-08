import os
import json

READ_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "读取本地文件的内容。如果需要分析本地文档或读取代码文件，请使用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "intent_analysis": {
                    "type": "string",
                    "description": "【第一步意图拆解(必须)】：为什么要读这个文件？想要从中获取什么信息？"
                },
                "file_path": {
                    "type": "string",
                    "description": "文件的绝对路径或相对路径",
                },
                "force_read": {
                    "type": "boolean",
                    "description": "【二次确认开关】如果你已知文件非常大（>100KB）且确实需要一口气读完它，请设为 true 强行读取。默认 false。"
                }
            },
            "required": ["intent_analysis", "file_path"],
        },
    }
}

def read_file(file_path: str, force_read: bool = False) -> str:
    """
    读取本地文件的内容（已加入安全沙箱机制）
    """
    try:
        # 【安全边界限制】：防止路径穿越（Path Traversal）攻击
        # 强制将目标路径转为绝对路径，并检查是否在当前项目根目录下
        base_dir = os.path.abspath(os.getcwd())
        
        # 智能防呆补全
        clean_path = file_path.strip(" /\\")
        if clean_path.startswith("input/") or clean_path.startswith("output/") or clean_path in ["input", "output"]:
            file_path = os.path.join("workspace", file_path)
            
        target_path = os.path.abspath(file_path)
        
        if not target_path.startswith(base_dir):
            return json.dumps({"error": "【安全拦截】：越权访问！你只能读取当前项目根目录下的文件，禁止访问系统其他目录！"}, ensure_ascii=False)
            
        if not os.path.exists(target_path):
            return json.dumps({"error": f"文件/文件夹不存在: {target_path}"}, ensure_ascii=False)
            
        # 如果是文件夹，则返回目录下的文件列表
        if os.path.isdir(target_path):
            files = os.listdir(target_path)
            return json.dumps({"type": "directory", "path": target_path, "contents": files}, ensure_ascii=False)
            
        # 如果是普通文件，检查文件大小
        file_size = os.path.getsize(target_path)
        is_large = file_size > 100 * 1024
        
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                if is_large and not force_read:
                    preview_content = f.read(1000)
                    return json.dumps({
                        "error": f"【二次确认拦截】：文件过大 ({file_size / 1024 / 1024:.2f} MB)！为了防止撑爆大模型内存，我暂时拦截了全量读取。",
                        "preview": f"{preview_content}\n\n... [文件太长，后续内容已截断] ...",
                        "suggestion": "这只是文件开头的 1000 个字符预览。如果你确定要强行读取全部内容，请增加参数 `force_read: true` 再次调用；如果只需要局部读取，请改用 read_chunk 等工具。"
                    }, ensure_ascii=False)
                else:
                    content = f.read()
                    return json.dumps({"type": "file", "file_path": file_path, "content": content}, ensure_ascii=False)
                    
        except UnicodeDecodeError:
            # 捕获二进制文件或非 utf-8 编码文件
            return json.dumps({
                "type": "binary_or_unknown_file", 
                "file_path": file_path, 
                "info": f"⚠️ 这是一个二进制文件（例如图片、音频、压缩包）或非 UTF-8 编码的文件。文件大小：{file_size} bytes。无法以纯文本模式读取内容。"
            }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"读取失败: {str(e)}"}, ensure_ascii=False)
