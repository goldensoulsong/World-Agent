import re
import os
import json

CHUNK_TEXT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "chunk_text",
        "description": "当文本内容里面存在格式化的章节标题（如“第一章”等）时，必定使用该工具！它可以对长篇小说或设定集进行按章节的自动化切块，提取标题与正文，并智能合并同章节的拆分内容。通过传入 split_pattern，它也可以作为通用切刀切分任何格式文本。",
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
                },
                "split_pattern": {
                    "type": "string",
                    "description": "自定义的正则表达式切分规则。如果为空，则默认使用网文专用的 r'(第[一二三四五六七八九十百千零\\d]+章.*?)\\n' 模式。如果正则带捕获组()，则捕获内容作为 title；否则不提取 title。"
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

def chunk_text(file_path: str, project_name: str, save_filename: str, split_pattern: str = None) -> str:
    """
    按章节对小说/设定集进行切块，并保存为 JSON 格式，统一放在 output/项目名称 文件夹下。
    支持自定义正则表达式 split_pattern，成为通用切块工具。
    """
    try:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="gbk", errors="ignore") as f:
                text = f.read()

        chunks = []
        
        if split_pattern:
            # 启用了自定义正则
            try:
                # 检查正则中是否包含显式的捕获组 ()
                # 粗略判断，如果有真实的 '(' 则认为有捕获组
                has_capture_group = '(' in split_pattern and ')' in split_pattern and r'\(' not in split_pattern
                
                parts = re.split(split_pattern, text)
                
                if has_capture_group and len(parts) > 1:
                    # 如果有捕获组，re.split 会返回: [之前的内容, 匹配组1, 之后的内容, 匹配组2, 之后的内容...]
                    # 索引0是开头的可能无标题内容
                    if parts[0].strip():
                        chunks.append({
                            "id": f"chunk_0",
                            "title": "前言/引子",
                            "content": clean_content(parts[0].strip())
                        })
                    
                    for i in range(1, len(parts), 2):
                        chunk_title = parts[i].strip() if parts[i] else ""
                        chunk_content = parts[i+1].strip() if i+1 < len(parts) and parts[i+1] else ""
                        if chunk_title or chunk_content:
                            chunks.append({
                                "id": f"chunk_{len(chunks)}",
                                "title": chunk_title,
                                "content": clean_content(chunk_content)
                            })
                else:
                    # 没有捕获组，re.split 仅仅去掉分隔符，返回纯内容数组
                    for i, part in enumerate(parts):
                        if part.strip():
                            chunks.append({
                                "id": f"chunk_{len(chunks)}",
                                "title": f"区块 {len(chunks)+1}",
                                "content": clean_content(part.strip())
                            })
            except Exception as e:
                return json.dumps({"error": f"自定义正则切片执行失败: {str(e)}"}, ensure_ascii=False)
                
        else:
            # 原有默认网文专用切分逻辑
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
