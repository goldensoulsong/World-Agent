import json
import os
import re
import concurrent.futures
from openai import OpenAI
from typing import List

LLM_BATCH_CLEAN_SCHEMA = {
    "type": "function",
    "function": {
        "name": "llm_batch_clean_text",
        "description": "【高级工具，耗时极长且耗费Token】全量并发精洗工具，支持多切片物理合并以及底层思维链防错护盾。必须在向用户明确背景、抽检并获得最终“执行”口令后才能调用此终极工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "input_json_path": {
                    "type": "string",
                    "description": "要精洗的源 JSON 文件路径"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称，用于在 output 目录下创建专门的文件夹进行管理"
                },
                "save_filename": {
                    "type": "string",
                    "description": "清洗后输出保存的 JSON 文件名"
                },
                "concurrency": {
                    "type": "integer",
                    "description": "请求并发数（默认建议 5）"
                },
                "chunks_per_batch": {
                    "type": "integer",
                    "description": "单次合并发给大模型的切片数（默认建议 20）"
                },
                "clean_instruction": {
                    "type": "string",
                    "description": "给大模型的精准清洗指令"
                }
            },
            "required": ["input_json_path", "project_name", "save_filename", "concurrency", "chunks_per_batch", "clean_instruction"],
        },
    }
}

def _process_batch_with_llm(batch_chunks: List[dict], instruction: str, api_key: str, base_url: str, model_name: str) -> List[dict]:
    """内部函数：处理合并的一个批次"""
    client = OpenAI(api_key=api_key, base_url=base_url)
    
    merged_text_parts = []
    for c in batch_chunks:
        chunk_id = c.get("id", "unknown")
        content = c.get("content", "")
        if content:
            merged_text_parts.append(f'<chunk id="{chunk_id}">\n{content}\n</chunk>')
            
    if not merged_text_parts:
        return batch_chunks
        
    merged_text = "\n".join(merged_text_parts)
    
    prompt = f"""【角色与任务】
你是一个无损级的小说文本精洗引擎。你将接收到由多个连续小说切片合并而成的极长文本。
为了区分切片，原文中插入了 <chunk id="..."> 的标签标记。

【用户的核心清洗指令】
{instruction}

【严禁触碰的最高红线（违者将导致系统崩溃）】
1. 禁止偷懒与省略：无论原文有多长，绝对不准自行总结、缩写剧情！绝对不能出现“...（后略）”等情况！必须全量且无损地保留所有剧情文字！
2. 保护标签：必须原样保留文本中所有的 <chunk id="..."> 和 </chunk> 标签，绝对不准删除或打乱它们的顺序！
3. 纯净输出：清洗完成后，除了外层必须包含的 <thought> 标签外，严禁输出任何废话。

【思维链与输出格式约束】
在处理这海量的文本前，你【必须】先开启一段思考。
请使用 <thought> 和 </thought> 标签包裹你的思考过程。在思考中，请分析清洗规则，并扫视一遍文本，找出符合特征的垃圾数据位置并说明你要怎么做。
思考结束后，你必须严格按照原有的切片顺序，逐个输出清理好的带有标签的文本。

【待清洗原文】
{merged_text}
"""

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        cleaned_text = response.choices[0].message.content.strip()
        
        # 提取切片
        pattern = r'<chunk id="(.*?)">\s*([\s\S]*?)\s*</chunk>'
        matches = re.findall(pattern, cleaned_text)
        
        if not matches:
            print(f"  [严重警告] 批次处理失败，大模型未能返回有效标签，已原样退回保障数据安全！")
            return batch_chunks
            
        # 根据匹配结果重新组装
        result_chunks = []
        # 构建一个以 id 为 key 的字典加速查找，同时保留顺序
        match_dict = {m[0]: m[1] for m in matches}
        
        for c in batch_chunks:
            chunk_id = str(c.get("id"))
            if chunk_id in match_dict:
                c["content"] = match_dict[chunk_id]
            else:
                print(f"  [警告] 批次处理遗漏了切片 {chunk_id}，该切片将保留原样。")
            result_chunks.append(c)
            
        return result_chunks
        
    except Exception as e:
        print(f"  [警告] 批次网络或执行失败: {e}")
        return batch_chunks

def llm_batch_clean_text(input_json_path: str, project_name: str, save_filename: str, concurrency: int, chunks_per_batch: int, clean_instruction: str) -> str:
    """并发调用大模型对 JSON 进行全量清洗 (支持批量合并与无损拆分)"""
    api_key = os.getenv("API_KEY")
    if not api_key:
        return json.dumps({"error": "未配置 API_KEY，无法使用大模型全量精洗功能。"}, ensure_ascii=False)
        
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME", "deepseek-chat")
    
    safe_project_name = os.path.basename(project_name.replace("..", "").replace("/", "").replace("\\", ""))
    safe_filename = os.path.basename(save_filename.replace("..", "").replace("/", "").replace("\\", ""))
    
    if not safe_project_name: safe_project_name = "default_project"
    if not safe_filename: safe_filename = "llm_cleaned_data.json"
    
    try:
        abs_file_path = os.path.abspath(input_json_path)
        workspace_path = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        if os.path.commonpath([workspace_path, abs_file_path]) != workspace_path:
            raise ValueError("安全拦截：禁止读取操作区 workspace 之外的文件！")

        with open(input_json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        total_chunks = len(chunks)
        # 将切片按 chunks_per_batch 进行分组
        batches = [chunks[i:i + chunks_per_batch] for i in range(0, total_chunks, chunks_per_batch)]
        total_batches = len(batches)
        
        print(f"\n[大模型并发精洗] 开始处理 {total_chunks} 个区块，划分为 {total_batches} 个批次...")
        print(f"[大模型并发精洗] 并发数: {concurrency}, 单批合并数: {chunks_per_batch}")
        
        # 预分配结果列表
        cleaned_chunks_result = []
        
        # 为了保证顺序，使用字典存储批次结果
        batch_results = {}
        
        completed_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_index = {
                executor.submit(_process_batch_with_llm, batches[i], clean_instruction, api_key, base_url, model_name): i
                for i in range(total_batches)
            }
            
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    batch_results[index] = future.result()
                except Exception as exc:
                    batch_results[index] = batches[index]
                    
                completed_count += 1
                if completed_count % 5 == 0 or completed_count == total_batches:
                    print(f"  -> 批次进度: {completed_count} / {total_batches}")
                    
        # 按原本顺序拼接所有的 chunk
        for i in range(total_batches):
            if i in batch_results:
                cleaned_chunks_result.extend(batch_results[i])
            else:
                cleaned_chunks_result.extend(batches[i])
                
        output_dir = os.path.abspath(os.path.join(os.getcwd(), "workspace", "output", safe_project_name))
        base_output_path = os.path.abspath(os.path.join(os.getcwd(), "workspace", "output"))
        
        if os.path.commonpath([base_output_path, output_dir]) != base_output_path:
            raise ValueError("安全拦截：检测到非法的路径越界尝试！")
            
        os.makedirs(output_dir, exist_ok=True)
        output_json_path = os.path.join(output_dir, safe_filename)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_chunks_result, f, ensure_ascii=False, indent=2)
            
        return json.dumps({
            "status": "success", 
            "message": f"大模型并发全量精洗成功！共处理了 {total_chunks} 个区块（{total_batches}批次），已完好无损重组并保存至 {output_json_path}。"
        }, ensure_ascii=False)
        
    except Exception as e:
        return json.dumps({"error": f"大模型并发精洗失败: {str(e)}"}, ensure_ascii=False)
