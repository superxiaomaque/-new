"""
配置文件
"""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://user:password@localhost:3306/friend_circle_analyzer"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    # 豆包API配置
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = "https://ark.cn-beijing.volces.com/api/v3"
    DOUBAO_MODEL: str = "doubao-seed-1.6-thinking"
    
    # 云存储配置（火山引擎TOS）
    TOS_ACCESS_KEY: str = ""
    TOS_SECRET_KEY: str = ""
    TOS_ENDPOINT: str = ""
    TOS_BUCKET: str = ""
    STORAGE_BACKEND: str = "local"  # local | tos
    
    # Redis配置（可选）
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # 文件上传配置
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    MIN_IMAGES: int = 5
    MAX_IMAGES: int = 20
    ALLOWED_EXTENSIONS: list = [".jpg", ".jpeg", ".png", ".webp"]
    
    # 用户限制
    DAILY_ANALYSIS_LIMIT: int = 3

    # 成本统计与预警（单位：人民币元，0表示不启用阈值）
    COST_INPUT_PER_1K_TOKENS: float = 0.0
    COST_OUTPUT_PER_1K_TOKENS: float = 0.0
    DAILY_COST_WARN_THRESHOLD: float = 0.0
    MONTHLY_COST_WARN_THRESHOLD: float = 0.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
