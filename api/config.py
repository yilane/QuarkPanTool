# -*- coding: utf-8 -*-
"""
API 配置文件
"""
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # API 基本配置
    APP_NAME: str = "QuarkPanTool API"
    APP_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    DEBUG: bool = True

    # Token 配置
    TOKEN_EXPIRE_HOURS: int = 24  # Token 有效期（小时）
    TOKEN_CLEANUP_INTERVAL: int = 3600  # Session 清理间隔（秒）

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS 配置
    CORS_ORIGINS: list = ["*"]

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "logs/api.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
