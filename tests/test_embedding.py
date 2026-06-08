import os
from dotenv import load_dotenv

# 确保加载 .env 文件中的 GOOGLE_API_KEY
load_dotenv(override=True)

from common.rag.embeddings import get_embeddings_model

def test_embeddings():
    print("正在初始化 Google Embedding 模型...")
    try:
        embeddings_model = get_embeddings_model()
    except Exception as e:
        print(f"初始化失败，请检查是否配置了 GOOGLE_API_KEY。错误信息: {e}")
        return

    text1 = "苹果是一种非常健康的水果。"
    text2 = "香蕉也富含维生素，对身体好。"
    text3 = "Python 是一门非常流行的编程语言。"

    print("\n开始请求谷歌大模型将文字转为向量...")
    
    # 将文本转为向量
    vec1 = embeddings_model.embed_query(text1)
    vec2 = embeddings_model.embed_query(text2)
    vec3 = embeddings_model.embed_query(text3)

    print(f"\n[成功] 转换成功！")
    print(f"一段文本会被转换成 {len(vec1)} 维的浮点数数组 (例如前5个数字: {vec1[:5]})")
    
    # 简单计算一下余弦相似度（不需要数据库，直接在内存算）
    import numpy as np
    from numpy.linalg import norm
    
    def cosine_similarity(A, B):
        return np.dot(A, B) / (norm(A) * norm(B))

    sim_1_2 = cosine_similarity(vec1, vec2)
    sim_1_3 = cosine_similarity(vec1, vec3)

    print("\n=== 相似度对比结果 (越接近1越相似) ===")
    print(f"文本1: {text1}")
    print(f"文本2: {text2}")
    print(f"文本3: {text3}")
    print(f"----------------------------------")
    print(f"文本1 和 文本2 的相似度 (水果): {sim_1_2:.4f}")
    print(f"文本1 和 文本3 的相似度 (跨界): {sim_1_3:.4f}")
    
    print("\n这就是向量库实现【模糊语义检索】的底层原理！")

if __name__ == "__main__":
    test_embeddings()
