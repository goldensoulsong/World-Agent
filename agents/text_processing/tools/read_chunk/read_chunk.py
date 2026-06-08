import json
import os

READ_CHUNK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_chunk",
        "description": "专门用于分页/分块读取已经切块好的 JSON 语料文件。为了避免一次性读取过大数据导致上下文超限，必须使用此工具配合 start_index 和 count 进行分批抽样阅读。",
        "parameters": {
            "type": "object",
            "properties": {
                "json_path": {
                    "type": "string",
                    "description": "需要读取的 JSON 文件路径"
                },
                "start_index": {
                    "type": "integer",
                    "description": "起始读取的 chunk 索引，从 0 开始"
                },
                "count": {
                    "type": "integer",
                    "description": "期望读取的 chunk 数量，建议每次读取不超过 30 个以保证处理质量"
                }
            },
            "required": ["json_path", "start_index", "count"],
        },
    }
}

def read_chunk(json_path: str, start_index: int, count: int) -> str:
    """
    分批读取 JSON 块文件，返回指定范围的块列表的 JSON 字符串形式。
    """
    try:
        # 强制检查读取路径是否在 workspace 内
        abs_file_path = os.path.abspath(json_path)
        workspace_path = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
        if os.path.commonpath([workspace_path, abs_file_path]) != workspace_path:
            return json.dumps({"error": "安全拦截：禁止读取操作区 workspace 之外的文件！"}, ensure_ascii=False)
            
        if not os.path.exists(json_path):
            return json.dumps({"error": f"文件不存在: {json_path}"}, ensure_ascii=False)
            
        with open(json_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        if not isinstance(chunks, list):
            return json.dumps({"error": "JSON 格式不正确，期望是一个数组"}, ensure_ascii=False)
            
        total_chunks = len(chunks)
        
        if start_index >= total_chunks or start_index < 0:
            return json.dumps({
                "status": "warning", 
                "message": f"起始索引 {start_index} 越界。文件共有 {total_chunks} 个块。"
            }, ensure_ascii=False)
            
        end_index = min(start_index + count, total_chunks)
        selected_chunks = chunks[start_index:end_index]
        
        result = {
            "status": "success",
            "total_chunks_in_file": total_chunks,
            "current_range": f"{start_index} 到 {end_index - 1}",
            "returned_count": len(selected_chunks),
            "data": selected_chunks
        }
        
        return json.dumps(result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"读取失败: {str(e)}"}, ensure_ascii=False)
