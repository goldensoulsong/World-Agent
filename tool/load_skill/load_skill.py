import json

LOAD_SKILL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_skill_sop",
        "description": "当你在系统提示词的【高级智能工作流 (Skills) 目录】中发现与用户意图匹配的技能时，必须第一时间调用本工具！本工具能为你下载该技能的完整操作手册 (SOP)。仔细阅读返回的 SOP 后再执行任务。",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "需要装载的技能内部标识名称（例如 'smart_chunking' 或 'data_cleaning'）"
                }
            },
            "required": ["skill_name"],
        },
    }
}

def load_skill_sop(skill_name: str) -> str:
    """
    检索并返回技能的详细操作手册。
    """
    try:
        from skill import ALL_SKILLS
        
        for skill in ALL_SKILLS:
            if skill.get("name") == skill_name:
                sop = skill.get("sop", "")
                display_name = skill.get("display_name", skill_name)
                return f"✅ 成功装载技能手册【{display_name}】。\n\n【SOP 严格执行指南】：\n{sop}\n\n请仔细阅读上述步骤，并在你的下一个 Thought 中规划执行步骤！"
                
        return json.dumps({"error": f"未找到名为 '{skill_name}' 的技能，请检查名称是否拼写正确。"}, ensure_ascii=False)
    except Exception as e:
         return json.dumps({"error": f"装载技能失败: {str(e)}"}, ensure_ascii=False)
