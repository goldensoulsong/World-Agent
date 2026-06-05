import os
import json

WRITE_FILE_SCHEMA = {
    "type": "function",
    "function": {
        "name": "write_file",
        "description": "将内容写入本地文件（支持新建或覆盖）。当用户要求保存报告、生成文件或保存代码时调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "intent_analysis": {
                    "type": "string",
                    "description": "【第一步意图拆解(必须)】：为什么要写入这个文件？想要保存什么内容？"
                },
                "file_path": {
                    "type": "string",
                    "description": "目标文件名或相对路径（注意：系统已强制规定必须存放在 output 目录下，你只需要传相对路径如 result.md 即可）",
                },
                "content": {
                    "type": "string",
                    "description": "要写入的完整内容（如 Markdown 格式的报告）",
                }
            },
            "required": ["intent_analysis", "file_path", "content"],
        },
    }
}

def write_file(file_path: str, content: str) -> str:
    """
    将内容写入本地文件（已加入安全沙箱，强制输出到 workspace/output 目录）
    """
    try:
        # 【强制归档机制】：确定 output 目录的绝对路径
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "workspace", "output"))
        
        # 如果模型传的是相对路径，自动拼接到 output 目录下
        if not os.path.isabs(file_path):
            target_path = os.path.abspath(os.path.join(output_dir, file_path))
        else:
            target_path = os.path.abspath(file_path)
            
        # 【安全拦截】：终极防御！使用 commonpath 避免 startswith 漏洞
        if os.path.commonpath([output_dir, target_path]) != output_dir:
            return json.dumps({"error": "【安全拦截】：为保持项目整洁且防范非法越权操作，你只能将文件写入 workspace/output/ 文件夹下！"}, ensure_ascii=False)
            
        # 自动创建 output 目录及父级子目录
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return json.dumps({"success": True, "message": f"内容已成功保存至文件: {target_path}"}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": f"文件写入失败: {str(e)}"}, ensure_ascii=False)
