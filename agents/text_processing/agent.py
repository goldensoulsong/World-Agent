import os
import json
from datetime import datetime, timezone
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage

class AgentState(TypedDict):
    """全局状态大白板"""
    messages: Annotated[Sequence[BaseMessage], add_messages]

class TextProcessingAgent:
    def __init__(self, system_prompt: str = None, max_loops: int = 20):
        # 内部导入专属工具和公用工具
        from .tools import TEXT_PROCESSING_TOOLS_SCHEMA, TEXT_PROCESSING_AVAILABLE_TOOLS
        from .skills import TEXT_PROCESSING_SKILLS
        from common.tools import TOOLS_SCHEMA as COMMON_TOOLS_SCHEMA, AVAILABLE_TOOLS as COMMON_AVAILABLE_TOOLS, register_skills, clear_skills
        
        # 组装完整的工具集
        self.available_tools = {**TEXT_PROCESSING_AVAILABLE_TOOLS, **COMMON_AVAILABLE_TOOLS}
        tools_schema = TEXT_PROCESSING_TOOLS_SCHEMA + COMMON_TOOLS_SCHEMA
        
        # 注册当前 Agent 的技能到通用 load_skill 中
        clear_skills()
        register_skills(TEXT_PROCESSING_SKILLS)
        
        # 如果未传入，则使用默认的
        if not system_prompt:
            from .prompts import TEXT_PROCESSING_AGENT_PROMPT
            system_prompt = TEXT_PROCESSING_AGENT_PROMPT

        # 组装 System Prompt (注入 Skills)
        skills = TEXT_PROCESSING_SKILLS
        if system_prompt:
            if "{skills_injection}" in system_prompt:
                if skills:
                    skills_text = "【高级智能工作流 (Skills) 目录】：\n当你扫描到用户的真实需求匹配以下技能的触发条件时，你【必须】第一时间调用 `load_skill_sop` 工具，传入对应的内部标识名称，下载并阅读该技能的完整操作手册 (SOP) 后再开始干活！绝不允许在没有装载 SOP 的情况下盲目执行！\n\n"
                    for idx, skill in enumerate(skills):
                        skills_text += f"{idx + 1}. {skill['display_name']}\n"
                        skills_text += f"   - 内部标识：{skill['name']}\n"
                        skills_text += f"   - 触发条件：{skill['trigger_condition']}\n\n"
                    system_prompt = system_prompt.replace("{skills_injection}", skills_text)
                else:
                    system_prompt = system_prompt.replace("{skills_injection}", "")
            self.system_prompt = system_prompt
        else:
            self.system_prompt = "You are a helpful AI assistant."

        # 初始化大模型 (LangChain 封装)
        model_name = os.getenv("MODEL_NAME", "deepseek-chat")
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")
        
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url if base_url else None,
            streaming=True
        )
        
        # 绑定工具
        if tools_schema:
            self.llm_with_tools = self.llm.bind_tools(tools_schema)
        else:
            self.llm_with_tools = self.llm
            
        # 构建 LangGraph
        self.graph = self._build_graph()
        
    def _build_graph(self):
        workflow = StateGraph(AgentState)
        
        # 节点：调用模型
        async def call_model(state: AgentState):
            messages = list(state["messages"])
            # 强制用最新的 system_prompt 替换记忆中的旧提示词，确保热更新生效
            if messages and isinstance(messages[0], SystemMessage):
                messages[0] = SystemMessage(content=self.system_prompt)
            else:
                messages.insert(0, SystemMessage(content=self.system_prompt))
            
            response = await self.llm_with_tools.ainvoke(messages)
            return {"messages": [response]}
            
        # 节点：执行工具
        async def execute_tools(state: AgentState):
            last_message = state["messages"][-1]
            tool_messages = []
            
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                for tool_call in last_message.tool_calls:
                    func_name = tool_call["name"]
                    args = tool_call["args"]
                    tool_call_id = tool_call["id"]
                    
                    if func_name in self.available_tools:
                        func_to_call = self.available_tools[func_name]
                        try:
                            # 过滤掉意图拆解辅助参数
                            valid_args = {k: v for k, v in args.items() if k != 'intent_analysis'}
                            tool_result = func_to_call(**valid_args)
                        except Exception as e:
                            tool_result = f"调用工具时发生错误: {str(e)}"
                            
                        # 安全截断，防止显存爆炸
                        if isinstance(tool_result, str) and len(tool_result) > 100000:
                            tool_result = tool_result[:100000] + f"\n\n...[截断]"
                            
                        tool_messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_call_id, name=func_name))
                    else:
                        tool_messages.append(ToolMessage(content=f"错误：未找到名为 {func_name} 的工具", tool_call_id=tool_call_id, name=func_name))
            
            return {"messages": tool_messages}
            
        # 路由函数
        def should_continue(state: AgentState) -> str:
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return "end"
            
        # 组装图
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", execute_tools)
        
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()

    def _load_history_from_json(self, session_id: str):
        filepath = os.path.join("data", "chats", f"{session_id}.json")
        history_messages = []
        if os.path.exists(filepath):
            try:
                import re
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                messages = data.get("messages", [])
                for msg in messages:
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    
                    # 用户明确要求：加载历史时剥离旧的思维链
                    content = re.sub(r'<thought>.*?</thought>', '', content, flags=re.DOTALL).strip()
                    if not content:
                        continue
                        
                    if role == "user":
                        history_messages.append(HumanMessage(content=content))
                    elif role == "assistant":
                        history_messages.append(AIMessage(content=content))
            except Exception as e:
                print(f"Failed to load history for {session_id}: {e}")
        return history_messages

    def _write_log(self, session_id: str, direction: str, content):
        """写入原始 I/O 日志到 data/logs/{session_id}.jsonl"""
        log_dir = os.path.join("data", "logs")
        os.makedirs(log_dir, exist_ok=True)
        filepath = os.path.join(log_dir, f"{session_id}.jsonl")
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "direction": direction,
            "raw_content": content
        }
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[LOG] Failed to write log: {e}")

    def _write_trace(self, session_id: str, round_id: str, event_type: str, content, metadata=None):
        """写入追踪事件到 data/traces/{session_id}.jsonl"""
        trace_dir = os.path.join("data", "traces")
        os.makedirs(trace_dir, exist_ok=True)
        filepath = os.path.join(trace_dir, f"{session_id}.jsonl")
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "round_id": round_id,
            "event_type": event_type,
            "content": content,
            "metadata": metadata or {}
        }
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[TRACE] Failed to write trace: {e}")

    def _serialize_messages(self, messages):
        """将 LangChain message 对象序列化为可读的 dict 列表"""
        result = []
        for msg in messages:
            role = "unknown"
            if isinstance(msg, SystemMessage):
                role = "system"
            elif isinstance(msg, HumanMessage):
                role = "user"
            elif isinstance(msg, AIMessage):
                role = "assistant"
            elif isinstance(msg, ToolMessage):
                role = "tool"
            result.append({"role": role, "content": msg.content})
        return result

    async def run_generator(self, user_query: str, session_id: str = "default"):
        """SSE 格式流式输出，完全兼容老前端"""
        config = {"configurable": {"thread_id": session_id}}
        history = self._load_history_from_json(session_id)
        inputs = {"messages": history + [HumanMessage(content=user_query)]}
        
        # 生成本轮唯一标识 (用于追踪分组)
        round_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "_" + str(id(inputs))[-6:]
        
        # ====== 日志：记录发给 LLM 的完整 messages 数组 ======
        full_messages_for_log = [SystemMessage(content=self.system_prompt)] + list(inputs["messages"])
        self._write_log(session_id, "sent", self._serialize_messages(full_messages_for_log))
        
        # ====== 追踪：记录本轮开始 ======
        self._write_trace(session_id, round_id, "round_start", user_query)
        
        final_answer = ""
        accumulated_thought = ""
        
        try:
            # 监听 LangGraph 底层事件
            async for event in self.graph.astream_events(inputs, config, version="v2"):
                kind = event["event"]
                
                # LLM 在思考输出文本
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        accumulated_thought += chunk.content
                        yield f"data: {json.dumps({'type': 'thought', 'content': chunk.content}, ensure_ascii=False)}\n\n"
                        
                # 触发工具调用动作
                elif kind == "on_tool_start":
                    tool_name = event["name"]
                    inputs_data = event.get("data", {}).get("input", {})
                    # 过滤 intent_analysis，保持前端清爽
                    clean_args = {k: v for k, v in inputs_data.items() if k != 'intent_analysis'}
                    yield f"data: {json.dumps({'type': 'action', 'function': tool_name, 'args': clean_args}, ensure_ascii=False)}\n\n"
                    
                    # ====== 追踪：工具调用 ======
                    self._write_trace(session_id, round_id, "tool_call", tool_name, {"args": clean_args})
                    
                # 工具执行完毕得到观察结果
                elif kind == "on_tool_end":
                    output_data = event.get("data", {}).get("output", "")
                    tool_name = event.get("name", "unknown")
                    
                    if isinstance(output_data, ToolMessage):
                        result_content = output_data.content
                    else:
                        result_content = str(output_data)
                    
                    # ====== 追踪：工具返回 ======
                    # 追踪文件记录完整结果（截断到10000字符防止文件过大）
                    trace_result = result_content[:10000] if len(result_content) > 10000 else result_content
                    self._write_trace(session_id, round_id, "tool_result", trace_result, {"tool_name": tool_name})
                        
                    # 对极长内容在返回前端时做折叠，防止前端崩溃 (仅做展示折叠，后台模型能看到全量，比如10万字)
                    if len(result_content) > 1000:
                        display_content = result_content[:1000] + "...[内容过长已折叠]"
                    else:
                        display_content = result_content
                        
                elif kind == "on_chat_model_end":
                    output = event.get("data", {}).get("output", "")
                    if hasattr(output, "content"):
                        final_answer = output.content
                        
                        # ====== 追踪：思考完成 (每次 model end 时记录累积的思考) ======
                        if accumulated_thought:
                            self._write_trace(session_id, round_id, "thought_complete", accumulated_thought)
                            accumulated_thought = ""
                        
            # 运行结束，从最后一次模型的完整输出中提取答案
            import re
            if final_answer:
                # ====== 追踪：最终回答 ======
                self._write_trace(session_id, round_id, "answer", final_answer)
                
                # ====== 日志：记录 AI 返回的原始内容 ======
                self._write_log(session_id, "received", final_answer)
                
                # 剥离隐藏的思维链标签，只输出纯净文本给前端
                clean_content = re.sub(r'<thought>.*?</thought>', '', final_answer, flags=re.DOTALL).strip()
                if clean_content:
                    yield f"data: {json.dumps({'type': 'answer', 'content': clean_content}, ensure_ascii=False)}\n\n"
                
        except Exception as e:
            self._write_trace(session_id, round_id, "error", str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': f'内部错误: {str(e)}'}, ensure_ascii=False)}\n\n"

    async def run(self, user_query: str, session_id: str = "default") -> str:
        """终端兼容接口"""
        config = {"configurable": {"thread_id": session_id}}
        history = self._load_history_from_json(session_id)
        inputs = {"messages": history + [HumanMessage(content=user_query)]}
        result = await self.graph.ainvoke(inputs, config)
        return result["messages"][-1].content
