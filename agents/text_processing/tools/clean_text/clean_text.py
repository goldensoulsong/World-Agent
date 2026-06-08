import json
import re
import os
from typing import List

CLEAN_TEXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "clean_text",
        "description": "当在处理的小说/语料文本中发现规律性的广告、无意义站内互动词、分隔符等脏数据时，使用此工具进行批量清洗。请先观察原始数据，并提取出合理的 remove_keywords 或 remove_patterns 再调用此工具。\n【注意】：设计 remove_patterns 时，务必兼容匹配全角英文/数字（如 Ｗｗ、８⒈）及特殊符号（如 ㈧㈠），避免变体网址和广告漏洗。",
        "parameters": {
            "type": "object",
            "properties": {
                "input_json_path": {
                    "type": "string",
                    "description": "要清洗的源 JSON 文件路径（格式需为包含 title 和 content 的对象数组）"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称（例如：斗罗大陆2绝世唐门），用于在 output 目录下创建专门的文件夹进行管理"
                },
                "save_filename": {
                    "type": "string",
                    "description": "清洗后输出保存的 JSON 文件名（例如：清洗后.json）"
                },
                "remove_keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要整行删除的关键词列表，例如 ['MOHEBOOK', '求推荐票', '求收藏']"
                },
                "remove_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要整行删除的正则表达式列表，例如 ['^[-－—=]{10,}$', '^☆、.*', '^\\\\s*;\\\\s*$']"
                },
                "replace_dict": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "需要替换的字典映射，例如 {'ri月': '日月', 'jing神': '精神'}"
                },
                "remove_chunk_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "需要整块删除的区块 ID 列表，例如 ['chunk_0', 'chunk_15']。被指定的区块将被完整移除。"
                }
            },
            "required": ["input_json_path", "project_name", "save_filename"],
        },
    }
}

def clean_text(input_json_path: str, project_name: str, save_filename: str, remove_keywords: List[str] = None, remove_patterns: List[str] = None, replace_dict: dict = None, remove_chunk_ids: List[str] = None) -> str:
    """
    根据传入的关键词和正则表达式，对 JSON 中的 content 进行逐行清洗，并替换指定的词汇。
    """
    if remove_keywords is None:
        remove_keywords = []
    if remove_patterns is None:
        remove_patterns = []
    if replace_dict is None:
        replace_dict = {}
    if remove_chunk_ids is None:
        remove_chunk_ids = []

    # 1. 强制安全过滤：防路径穿越漏洞 (Path Traversal)
    safe_project_name = os.path.basename(project_name.replace("..", "").replace("/", "").replace("\\", ""))
    safe_filename = os.path.basename(save_filename.replace("..", "").replace("/", "").replace("\\", ""))
    
    if not safe_project_name: safe_project_name = "default_project"
    if not safe_filename: safe_filename = "cleaned_data.json"

    try:
        # 强制检查读取路径是否在 workspace 内
        abs_file_path = os.path.abspath(input_json_path)
        workspace_path = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        if os.path.commonpath([workspace_path, abs_file_path]) != workspace_path:
            raise ValueError("安全拦截：禁止读取操作区 workspace 之外的文件！")

        with open(input_json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        compiled_patterns = [re.compile(p) for p in remove_patterns]
        
        # 1. 过滤掉被明确要求删除的块
        chunks = [c for c in chunks if c.get('id') not in remove_chunk_ids]
        
        final_chunks = []
        for chunk in chunks:
            title = chunk.get('title', '')
            content = chunk.get('content', '')
            
            # --- 处理 title ---
            if title:
                # 检查是否需要整行删除 title
                if any(kw.lower() in title.lower() for kw in remove_keywords) or any(p.search(title) for p in compiled_patterns):
                    chunk['title'] = ""
                else:
                    # 如果不需要整行删除，则应用替换规则
                    for old_str, new_str in replace_dict.items():
                        title = title.replace(old_str, new_str)
                    chunk['title'] = title.strip()
            
            # --- 处理 content ---
            if content:
                # 1. 全局精确替换（支持跨多行的原封不动替换/删除）
                for old_str, new_str in replace_dict.items():
                    content = content.replace(old_str, new_str)
                    
                # 2. 逐行处理正则和关键词
                lines = content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    line_stripped = line.strip()
                    
                    # 防止 ReDoS (灾难性回溯)，跳过超长行的正则匹配，仅做简单过滤
                    if len(line_stripped) > 5000:
                        if any(kw.lower() in line_stripped.lower() for kw in remove_keywords):
                            continue
                        cleaned_lines.append(line)
                        continue

                    # 检查是否需要整行删除
                    if any(kw.lower() in line_stripped.lower() for kw in remove_keywords):
                        continue
                    if any(p.search(line_stripped) for p in compiled_patterns):
                        continue
                        
                    cleaned_lines.append(line)
                    
                cleaned_content = '\n'.join(cleaned_lines)
                # 压缩多余空行
                cleaned_content = re.sub(r'\n{2,}', '\n', cleaned_content)
                chunk['content'] = cleaned_content.strip()
            
            # 如果清洗后区块不为空，则保留
            if chunk.get('title') or chunk.get('content'):
                final_chunks.append(chunk)
                
        # 重新为剩下的块按顺序分配 ID
        for i, chunk in enumerate(final_chunks):
            chunk['id'] = f"chunk_{i}"
            
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "workspace", "output", safe_project_name))
        base_output_path = os.path.abspath(os.path.join(os.getcwd(), "workspace", "output"))
        
        # 终极验证：确保 output_dir 必须在当前执行目录的 output 文件夹之下
        if os.path.commonpath([base_output_path, output_dir]) != base_output_path:
            raise ValueError("安全拦截：检测到非法的路径越界尝试！")
            
        os.makedirs(output_dir, exist_ok=True)
        output_json_path = os.path.join(output_dir, safe_filename)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(final_chunks, f, ensure_ascii=False, indent=2)
            
        return json.dumps({"status": "success", "message": f"清洗成功！移除了指定的 {len(remove_chunk_ids)} 个块，包含关键词 {remove_keywords} 及正则 {remove_patterns} 的行，并替换了 {len(replace_dict)} 个词汇规则。保留了 {len(final_chunks)} 个块。已保存至 {output_json_path}。"}, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"清洗失败: {str(e)}"}, ensure_ascii=False)
