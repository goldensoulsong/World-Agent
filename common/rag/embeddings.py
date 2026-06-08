import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def get_embeddings_model():
    """
    初始化并返回 Google Gemini 的 Embedding 模型。
    依赖环境变量：GOOGLE_API_KEY
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[警告] 未配置 GOOGLE_API_KEY，Embedding 模型可能无法正常工作。")
        
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        google_api_key=api_key
    )
