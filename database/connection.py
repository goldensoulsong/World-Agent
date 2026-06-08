import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 从环境变量获取数据库连接字符串
# 如果本地运行没读取到，提供一个默认值防止报错
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:worldagentpassword@localhost:5432/world_agent_db")

# 创建 SQLAlchemy 引擎
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True  # 自动检测断开的连接并重连
)

# 创建可重用的 Session 工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_session():
    """
    获取数据库 Session 的基础函数。
    可以配合 FastAPI 的 Depends() 使用，或者在 Agent 节点中手动调取。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
