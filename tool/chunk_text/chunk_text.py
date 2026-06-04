import re
import os
import json

CHUNK_TEXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "chunk_text",
        "description": "当文本内容里面存在格式化的章节标题（如“第一章”等）时，必定使用该工具！它可以对长篇小说或设定集进行按章节的自动化切块，提取标题与正文，并智能合并同章节的拆分内容。",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要切块的源文件路径（绝对路径）"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称（例如：斗罗大陆2绝世唐门），用于在 output 目录下创建专门的文件夹进行管理"
                },
                "save_filename": {
                    "type": "string",
                    "description": "保存的文件名（例如：切块结果.json）"
                }
            },
            "required": ["file_path", "project_name", "save_filename"],
        },
    }
}

def clean_content(text: str) -> str:
    """仅保留最基础的排版清理：合并多余的空行，去除首尾空白。具体的去广告等逻辑交由专用的 clean_text 工具。"""
    # 重组并替换多余的空行
    cleaned_text = re.sub(r'\n{2,}', '\n', text)
    return cleaned_text.strip()

def chunk_text(file_path: str, project_name: str, save_filename: str) -> str:
    """
    按章节对小说/设定集进行切块，并保存为 JSON 格式，统一放在 output/项目名称 文件夹下。
    """
    try:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                text = f.read()

        # 按照正则进行切分。
        pattern = r'(第[一二三四五六七八九十百千零\d]+章.*?)\n'
        parts = re.split(pattern, text)
        
        raw_chunks = []
        if parts[0].strip():
            raw_chunks.append({
                "title": "前言/引子",
                "content": clean_content(parts[0].strip())
            })
            
        for i in range(1, len(parts), 2):
            chapter_title = parts[i].strip()
            chapter_content = parts[i+1].strip() if i+1 < len(parts) else ""
            if chapter_content:
                raw_chunks.append({
                    "title": chapter_title,
                    "content": clean_content(chapter_content)
                })
                
        # 合并同一章的多个部分
        chunks = []
        chapter_prefix_pattern = re.compile(r'^(第[一二三四五六七八九十百千零\d]+章)')
        
        for chunk in raw_chunks:
            if not chunks:
                clean_title = re.sub(r'[（\(][一二三四五六七八九十上中下]+[）\)]$', '', chunk['title']).strip()
                chunk['title'] = clean_title
                chunk['id'] = f"chunk_{len(chunks)}"
                chunks.append(chunk)
                continue
                
            prev_chunk = chunks[-1]
            match_curr = chapter_prefix_pattern.search(chunk['title'])
            match_prev = chapter_prefix_pattern.search(prev_chunk['title'])
            
            # 安全合并逻辑：只有明确找到“第xxx章”前缀，并且前缀完全一致，才合并。否则作为新块。
            if match_curr and match_prev and match_curr.group(1) == match_prev.group(1):
                prev_chunk['content'] += "\n" + chunk['content']
            else:
                clean_title = re.sub(r'[（\(][一二三四五六七八九十上中下]+[）\)]$', '', chunk['title']).strip()
                chunk['title'] = clean_title
                chunk['id'] = f"chunk_{len(chunks)}"
                chunks.append(chunk)

        output_dir = os.path.abspath(os.path.join(os.getcwd(), "output", project_name))
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, save_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
            
        return json.dumps({"status": "success", "message": f"切块成功，共合并生成了 {len(chunks)} 个章节块，已保存至 {output_path}。"}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": f"切块失败: {str(e)}"}, ensure_ascii=False)
