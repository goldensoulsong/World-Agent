from common.rag.vector_store import process_and_store_document, search_similar_documents

def add_to_knowledge_base(content: str, source: str = "user_input") -> str:
    """
    将文本内容分块并存入知识库
    """
    success = process_and_store_document(content, source)
    if success:
        return f"成功将内容存入知识库 (来源: {source})"
    return "存入知识库失败"

def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    从知识库中检索与问题相关的信息
    """
    results = search_similar_documents(query, top_k)
    return "\n\n".join(results)

# 大模型函数调用 SCHEMA 定义
ADD_TO_KB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "add_to_knowledge_base",
        "description": "将有价值的事实、记忆或文档片段存入长期知识库。当你认为某些信息在未来可能会被用到时，调用此工具。",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要存入的完整文本内容"
                },
                "source": {
                    "type": "string",
                    "description": "该内容的来源描述（如 '用户的口头告知'，'文件:/path'）"
                }
            },
            "required": ["content"]
        }
    }
}

SEARCH_KB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "从知识库中检索相关事实或过往记录。当用户询问你不知道的知识，或你觉得需要参考过往记忆时调用。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "用于检索的查询语句，通常是自然语言问题"
                },
                "top_k": {
                    "type": "integer",
                    "description": "需要返回的最相关结果数量，默认3"
                }
            },
            "required": ["query"]
        }
    }
}
