import os
import json

JSON_TO_TXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "json_to_txt",
        "description": "当清洗完成、数据准备好后，使用此工具将结构化的 JSON 文件（包含 title 和 content）重新合并并导出为一本纯净的 TXT 电子书文本。这通常是数据处理管线的最后一步。",
        "parameters": {
            "type": "object",
            "properties": {
                "input_json_path": {
                    "type": "string",
                    "description": "要转换的 JSON 文件路径（通常是清洗后的结果文件）"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称（例如：斗罗大陆2绝世唐门），用于定位 output 目录"
                },
                "save_filename": {
                    "type": "string",
                    "description": "最终导出的 txt 文件名（例如：斗罗大陆2纯净版.txt）"
                }
            },
            "required": ["input_json_path", "project_name", "save_filename"],
        },
    }
}

def json_to_txt(input_json_path: str, project_name: str, save_filename: str, **kwargs) -> str:
    """
    读取 JSON 文件，并将其合并导出为 TXT 纯文本。
    """
    if not os.path.exists(input_json_path):
        return json.dumps({"status": "error", "message": f"找不到输入文件: {input_json_path}"})
        
    # 构建输出路径，强制放入 output/project_name/ 下
    output_dir = os.path.join("output", project_name)
    os.makedirs(output_dir, exist_ok=True)
    
    # 确保扩展名是 .txt
    if not save_filename.lower().endswith(".txt"):
        save_filename += ".txt"
        
    output_txt_path = os.path.join(output_dir, save_filename)
    
    try:
        with open(input_json_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            
        if not isinstance(chunks, list):
            return json.dumps({"status": "error", "message": "JSON 格式不正确，期望是一个包含章节字典的列表。"})
            
        with open(output_txt_path, "w", encoding="utf-8") as f:
            for chunk in chunks:
                title = chunk.get("title", "")
                content = chunk.get("content", "")
                
                # 写入章节标题
                if title:
                    f.write(f"{title}\n\n")
                
                # 写入章节内容
                if content:
                    f.write(f"{content}\n\n")
                    
        return json.dumps({
            "status": "success", 
            "message": f"成功将 JSON 转换为纯文本 TXT，共合并了 {len(chunks)} 个章节，已保存至 {output_txt_path}。"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"status": "error", "message": f"转换过程中发生错误: {str(e)}"})
