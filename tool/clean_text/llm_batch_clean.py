import json
import os
import concurrent.futures
from openai import OpenAI
from typing import List

LLM_BATCH_CLEAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "llm_batch_clean_text",
        "description": "【高级工具，耗时极长且耗费Token】当常规的 remove_keywords 或 replace_dict 无法清理复杂的牛皮癣广告或防盗版文本时，使用此工具。它会通过多线程并发，将所有语料切块逐一发送给大模型进行语义级别的深度清理。使用前务必向用户确认是否愿意等待并承担Token消耗。",
        "parameters": {
            "type": "object",
            "properties": {
                "input_json_path": {
                    "type": "string",
                    "description": "要精洗的源 JSON 文件路径（格式需为包含 title 和 content 的对象数组）"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称（例如：斗罗大陆2绝世唐门），用于在 output 目录下创建专门的文件夹进行管理"
                },
                "save_filename": {
                    "type": "string",
                    "description": "清洗后输出保存的 JSON 文件名（建议命名为：大模型精洗后.json）"
                },
                "clean_instruction": {
                    "type": "string",
                    "description": "给大模型的精准清洗指令。例如：'剔除文中的求票、作者碎碎念、双十二广告、防盗版乱码(如R1152)，不改变原始正文语义。'"
                }
            },
            "required": ["input_json_path", "project_name", "save_filename", "clean_instruction"],
        },
    }
}

def _process_chunk_with_llm(chunk: dict, instruction: str, api_key: str, base_url: str, model_name: str) -> dict:
    """内部函数：处理单个区块"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    title = chunk.get("title", "")
    content = chunk.get("content", "")
    if not content:
        return chunk
        
    prompt = f"""你是一个智能小说语料清洗助手。你的任务是严格遵循以下指令清理这段文本中的垃圾信息。
【清理指令】：{instruction}
【原标题】：{title}
【原文内容】：
{content}

【严格要求】：
1. 仅输出清理后的文本，禁止输出任何分析过程或对话（如“好的，这是清理后的文本”）。
2. 如果标题里有垃圾信息，在第一行输出清理后的标题（如果标题彻底无效，则第一行留空）。
3. 从第二行开始输出清理后的正文。
4. 不要删减正常的剧情和描写。
"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1 # 低温度，保证不随便篡改内容
        )
        cleaned_text = response.choices[0].message.content.strip()
        
        # 分离出标题和正文
        lines = cleaned_text.split("\n")
        new_title = lines[0].strip() if lines else title
        new_content = "\n".join(lines[1:]).strip() if len(lines) > 1 else cleaned_text
        
        return {
            "id": chunk.get("id"),
            "title": new_title,
            "content": new_content
        }
    except Exception as e:
        print(f"  [警告] Chunk {chunk.get('id')} 清洗失败: {e}")
        return chunk

def llm_batch_clean_text(input_json_path: str, project_name: str, save_filename: str, clean_instruction: str) -> str:
    """
    并发调用大模型对 JSON 中的每个区块进行清洗
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        return json.dumps({"error": "未配置 API_KEY，无法使用大模型全量精洗功能。"}, ensure_ascii=False)
        
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        total_chunks = len(chunks)
        print(f"\n[大模型并发精洗] 开始处理 {total_chunks} 个区块...")
        print(f"[大模型并发精洗] 指令: {clean_instruction}")
        
        cleaned_chunks = [None] * total_chunks
        
        # 使用并发执行，限制最大并发以防触发 429 Rate Limit
        max_workers = 10 
        completed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务，并附带索引以保证结果顺序一致
            future_to_index = {
                executor.submit(_process_chunk_with_llm, chunks[i], clean_instruction, api_key, base_url, model_name): i
                for i in range(total_chunks)
            }
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    cleaned_chunks[index] = future.result()
                except Exception as exc:
                    cleaned_chunks[index] = chunks[index]
                    
                completed_count += 1
                if completed_count % 10 == 0 or completed_count == total_chunks:
                    print(f"  -> 进度: {completed_count} / {total_chunks}")
                    
        # 确保没有 None
        cleaned_chunks = [c if c is not None else chunks[i] for i, c in enumerate(cleaned_chunks)]
        
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "output", project_name))
        os.makedirs(output_dir, exist_ok=True)
        output_json_path = os.path.join(output_dir, save_filename)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_chunks, f, ensure_ascii=False, indent=2)
            
        return json.dumps({
            "status": "success", 
            "message": f"大模型全量精洗成功！共处理了 {total_chunks} 个区块，已保存至 {output_json_path}。"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"大模型并发精洗失败: {str(e)}"}, ensure_ascii=False)
