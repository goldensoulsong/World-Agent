import os
import sys
from dotenv import load_dotenv

# 优雅地解决 Windows 终端打印大模型表情包报错的问题，同时防止中文变成乱码
sys.stdout.reconfigure(errors='replace')

# 从核心层引入封装好的 ReAct Agent
from core.react_agent import ReActAgent

def main():
    # 1. 加载 .env 环境变量配置（需要在初始化 Agent 之前加载）
    load_dotenv(override=True)
    
    # 引导小白用户配置 API 密钥（避免硬编码）
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("\n[系统提示] 未检测到 API_KEY。这是您第一次运行，请进行基础配置。")
        print("（如果您没有密钥，请前往相关大模型厂商官网申请）")
        api_key = input("请输入您的 API_KEY: ").strip()
        base_url = input("请输入 BASE_URL (默认: https://api.deepseek.com，直接回车跳过): ").strip()
        model_name = input("请输入模型名称 (默认: deepseek-chat，直接回车跳过): ").strip()
        
        with open(".env", "a", encoding="utf-8") as f:
            f.write(f"\nAPI_KEY={api_key}")
            if base_url:
                f.write(f"\nBASE_URL={base_url}")
            if model_name:
                f.write(f"\nMODEL_NAME={model_name}")
                
        os.environ["API_KEY"] = api_key
        if base_url:
            os.environ["BASE_URL"] = base_url
        if model_name:
            os.environ["MODEL_NAME"] = model_name
            
        print("[系统提示] 配置已成功保存到 .env 文件中，下次启动将自动加载！\n")
    
    from core.prompts import REACT_SYSTEM_PROMPT, MASTER_AGENT_PROMPT
    from tool import TOOLS_SCHEMA, AVAILABLE_TOOLS
    
    # 2. 实例化 Agent
    agent = ReActAgent(
        system_prompt=MASTER_AGENT_PROMPT, 
        tools_schema=TOOLS_SCHEMA,
        available_tools=AVAILABLE_TOOLS,
        max_loops=20
    )
    
    print("=== 欢迎进入 ReAct Agent 终端 ===")
    
    while True:
        user_input = input("\n请输入你的问题 (输入 q 退出): ")
        if user_input.lower() == 'q':
            break
        
        if user_input.strip():
            # 4. 把问题交给 Agent 对象去处理
            result = agent.run(user_input)
            print(f"\n[Agent 最终回答]:\n{result}\n")

if __name__ == "__main__":
    main()
