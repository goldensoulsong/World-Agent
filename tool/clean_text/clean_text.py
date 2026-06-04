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
                }
            },
            "required": ["input_json_path", "project_name", "save_filename"],
        },
    }
}

def clean_text(input_json_path: str, project_name: str, save_filename: str, remove_keywords: List[str] = None, remove_patterns: List[str] = None, replace_dict: dict = None) -> str:
    """
    根据传入的关键词和正则表达式，对 JSON 中的 content 进行逐行清洗，并替换指定的词汇。
    """
    if remove_keywords is None:
        remove_keywords = []
    if remove_patterns is None:
        remove_patterns = []
    if replace_dict is None:
        replace_dict = {}

    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        compiled_patterns = [re.compile(p) for p in remove_patterns]
        
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
                lines = content.split('\n')
                cleaned_lines = []
                
                for line in lines:
                    line_stripped = line.strip()
                    # 检查是否需要整行删除
                    if any(kw.lower() in line_stripped.lower() for kw in remove_keywords):
                        continue
                    if any(p.search(line_stripped) for p in compiled_patterns):
                        continue
                    
                    # 替换拼音/敏感词/无意义字符
                    for old_str, new_str in replace_dict.items():
                        line = line.replace(old_str, new_str)
                        
                    cleaned_lines.append(line)
                    
                cleaned_content = '\n'.join(cleaned_lines)
                # 压缩多余空行
                cleaned_content = re.sub(r'\n{2,}', '\n', cleaned_content)
                chunk['content'] = cleaned_content.strip()
            
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "output", project_name))
        os.makedirs(output_dir, exist_ok=True)
        output_json_path = os.path.join(output_dir, save_filename)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
        return json.dumps({"status": "success", "message": f"清洗成功！移除了包含关键词 {remove_keywords} 及正则 {remove_patterns} 的行，并替换了 {len(replace_dict)} 个词汇规则。已保存至 {output_json_path}。"}, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"清洗失败: {str(e)}"}, ensure_ascii=False)
