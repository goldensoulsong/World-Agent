import os
import json
from openai import OpenAI

# 导入工具库
from tool import search_web

class ReActAgent:
    """
    ReAct 模式下的 Agent
    具备：
    1. 上下文记忆 (chat_history)
    2. 工具调用与解析能力 (tools / tool_calls)
    3. 自我思考循环 (Thought -> Action -> Observation)
    """
    def __init__(self, system_prompt: str = None, tools_schema: list = None, available_tools: dict = None, max_loops: int = 20):
        # 1. 初始化客户端
        print(f"[DEBUG] API_KEY: {os.getenv('API_KEY')}")
        print(f"[DEBUG] BASE_URL: {os.getenv('BASE_URL')}")
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        self.model_name = os.getenv("MODEL_NAME", "deepseek-chat")
        self.max_loops = max_loops
        
        # 2. 初始化记忆窗口
        self.chat_history = []
        if system_prompt:
            self.chat_history.append({"role": "system", "content": system_prompt})
            
        # 3. 注册给大模型的工具 JSON Schema
        self.tools = tools_schema or []
        
        # 4. 本地实际执行函数的映射字典，为了未来能方便扩展多个工具
        self.available_tools = available_tools or {}

    def run(self, user_query: str) -> str:
        """
        开始运行 ReAct 思考与执行循环
        """
        print(f"\n[ReActAgent] 收到用户任务: {user_query}")
        
        # 将用户问题加入记忆
        self.chat_history.append({"role": "user", "content": user_query})
        
        for loop_count in range(self.max_loops):
            print(f"\n--- 第 {loop_count+1} 轮思考 ---")
            
            # Step 1: 让大模型根据历史记录进行思考 (Thought/Action)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=self.chat_history,
                tools=self.tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            # 记录模型的内部想法和请求
            self.chat_history.append(message)
            
            # 💡 完美还原 ReAct：把模型在工具调用外层写的 Thought 给打印出来
            if message.content:
                print(f"\n[大模型内心独白 (Thought)]:\n{message.content}")
            
            # Step 2: 观察模型的输出，决定是否要执行动作 (Observation)
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    
                    if func_name in self.available_tools:
                        # 获取模型要求传入的参数
                        args = json.loads(tool_call.function.arguments)
                        
                        # 💡 完美还原 ReAct：强制提取并打印大模型填写在工具里的“意图拆解”
                        if "intent_analysis" in args:
                            print(f"\n[第一步意图拆解 (Reason)]:\n{args['intent_analysis']}")
                            
                        # 准备打印用的参数（过滤掉意图拆解字段，保持界面清爽）
                        args_to_print = {k: v for k, v in args.items() if k != 'intent_analysis'}
                        print(f"[第二步执行动作 (Action)]: 决定调用 '{func_name}', 传入参数: {json.dumps(args_to_print, ensure_ascii=False)}")
                        
                        # 动态调用对应的 Python 函数
                        func_to_call = self.available_tools[func_name]
                        try:
                            # 过滤掉辅助参数，只把真正的业务参数传给底层函数
                            valid_args = {k: v for k, v in args.items() if k != 'intent_analysis'}
                            tool_result = func_to_call(**valid_args)
                        except Exception as e:
                            tool_result = f"调用工具时发生错误: {str(e)}"
                            
                        # 【安全防爆保护】：如果工具返回的结果太长（如一次性读取了几百万字），强行截断，防止大模型爆内存
                        if isinstance(tool_result, str) and len(tool_result) > 100000:
                            print(f"[警告] 工具 {func_name} 返回的结果过长 ({len(tool_result)} 字符)，已进行安全截断。")
                            tool_result = tool_result[:100000] + f"\n\n...[警告：内容过长已被强行截断，原长度 {len(tool_result)} 字符。为防止上下文爆炸，只保留前十万字。请使用更精确的工具参数（如分块、检索）！]"
                        
                        # 记录工具执行的结果
                        self.chat_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": tool_result
                        })
                    else:
                        # 防御性编程：万一模型幻觉，调用了不存在的工具
                        print(f"[警告] 模型试图调用不存在的工具: {func_name}")
                        self.chat_history.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": f"错误：未找到名为 {func_name} 的工具"
                        })
                        
                # 循环未结束，让模型带上刚查到的资料继续下一轮思考
                continue
                
            else:
                # Step 3: 模型判定已经有足够信息，生成了最终答案
                return message.content
                
        return "已达到最大思考次数，ReAct 循环被强制终止"
