"""
测试配置文件（使用SQLite，无需MySQL）
"""
import os
from pydantic_settings import BaseSettings

class TestSettings(BaseSettings):
    # 数据库配置 - 使用SQLite进行测试
    DATABASE_URL: str = "sqlite:///./test.db"
    
    # JWT配置
    SECRET_KEY: str = "test-secret-key-for-development-only"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 豆包API配置（测试时可以不填，但分析功能会失败）
    DOUBAO_API_KEY: str = os.getenv("DOUBAO_API_KEY", "")
    DOUBAO_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL: str = os.getenv("DOUBAO_MODEL", "doubao-seed-1-6-flash-250828")
    
    # 云存储配置（测试时使用本地存储）
    TOS_ACCESS_KEY: str = ""
    TOS_SECRET_KEY: str = ""
    TOS_ENDPOINT: str = ""
    TOS_BUCKET: str = ""
    STORAGE_BACKEND: str = "local"  # local | tos
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MIN_IMAGES: int = 5
    MAX_IMAGES: int = 20
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".webp"]
    
    # 用户限制
    DAILY_ANALYSIS_LIMIT: int = 3

    # 成本估算与预警（可选）
    COST_INPUT_PER_1K_TOKENS: float = 0.0
    COST_OUTPUT_PER_1K_TOKENS: float = 0.0
    DAILY_COST_WARN_THRESHOLD: float = 0.0
    MONTHLY_COST_WARN_THRESHOLD: float = 0.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

# 测试时使用TestSettings
settings = TestSettings()
