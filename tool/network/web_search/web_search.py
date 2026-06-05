from ddgs import DDGS
import json

SEARCH_WEB_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "使用 DuckDuckGo 执行免费的联网搜索获取实时信息，当你需要查询最新的新闻、知识时非常有用。",
        "parameters": {
            "type": "object",
            "properties": {
                "intent_analysis": {
                    "type": "string",
                    "description": "【第一步意图拆解(必须)】：用户想让我做什么？我的预期是什么？所要查询的有什么强调的？我应该如何构造高质量的查询词？"
                },
                "query": {
                    "type": "string",
                    "description": "需要搜索的关键词",
                }
            },
            "required": ["intent_analysis", "query"],
        },
    }
}

def search_web(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo 执行免费的联网搜索并返回结果
    
    :param query: 搜索关键词
    :param max_results: 最大返回结果数量，默认返回前 5 条
    :return: 包含标题、链接、摘要的 JSON 字符串
    """
    try:
        # DDGS().text 会返回包含 {'title': '...', 'href': '...', 'body': '...'} 的列表
        results = DDGS().text(query, max_results=max_results)
        
        if not results:
            return json.dumps({"error": "未找到相关搜索结果"}, ensure_ascii=False)
            
        formatted_results = []
        for res in results:
            formatted_results.append({
                "title": res.get("title", ""),
                "url": res.get("href", ""),
                "snippet": res.get("body", "")
            })
            
        return json.dumps(formatted_results, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"搜索发生错误: {str(e)}"}, ensure_ascii=False)

# 本地测试代码
if __name__ == "__main__":
    print("【测试】正在搜索 'Python 3.12 新特性'...")
    res = search_web("Python 3.12 新特性", max_results=2)
    print("搜索结果如下：")
    print(res)
