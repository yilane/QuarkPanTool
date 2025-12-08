# -*- coding: utf-8 -*-
"""
Session 管理器 - 基于内存的 Token 和 Session 管理
"""
import uuid
import time
import asyncio
import threading
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from api.config import settings


class Session:
    """Session 对象"""

    def __init__(self, cookies: str, user_id: Optional[str] = None):
        self.cookies = cookies
        self.user_id = user_id
        self.created_at = time.time()
        self.expire_at = time.time() + (settings.TOKEN_EXPIRE_HOURS * 3600)
        self.last_access = time.time()
        self.manager = None  # QuarkPanFileManager 实例

    def is_expired(self) -> bool:
        """检查 Session 是否过期"""
        return time.time() > self.expire_at

    def update_access(self):
        """更新最后访问时间"""
        self.last_access = time.time()


class SessionManager:
    """Session 管理器 - 单例模式"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.sessions: Dict[str, Session] = {}
        self._cleanup_task = None
        self._initialized = True

    def generate_token(self) -> str:
        """生成唯一 Token"""
        return str(uuid.uuid4())

    async def create_session(
        self,
        cookies: str,
        user_id: Optional[str] = None
    ) -> Tuple[str, Session]:
        """
        创建新的 Session

        Args:
            cookies: Cookie 字符串
            user_id: 用户 ID（可选）

        Returns:
            (token, session) 元组
        """
        token = self.generate_token()
        session = Session(cookies=cookies, user_id=user_id)

        # 存储 Session
        self.sessions[token] = session

        return token, session

    def get_session(self, token: str) -> Optional[Session]:
        """
        获取 Session

        Args:
            token: Token 字符串

        Returns:
            Session 对象或 None
        """
        session = self.sessions.get(token)

        if session is None:
            return None

        # 检查是否过期
        if session.is_expired():
            self.delete_session(token)
            return None

        # 更新访问时间
        session.update_access()
        return session

    def delete_session(self, token: str) -> bool:
        """
        删除 Session

        Args:
            token: Token 字符串

        Returns:
            是否删除成功
        """
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False

    def cleanup_expired_sessions(self):
        """清理过期的 Session"""
        current_time = time.time()
        expired_tokens = [
            token for token, session in self.sessions.items()
            if session.is_expired()
        ]

        for token in expired_tokens:
            del self.sessions[token]

        if expired_tokens:
            print(f"[{datetime.now()}] 清理了 {len(expired_tokens)} 个过期 Session")

    async def start_cleanup_task(self):
        """启动定期清理任务"""
        while True:
            await asyncio.sleep(settings.TOKEN_CLEANUP_INTERVAL)
            self.cleanup_expired_sessions()

    def get_session_count(self) -> int:
        """获取当前 Session 数量"""
        return len(self.sessions)

    def get_session_info(self, token: str) -> Optional[Dict]:
        """获取 Session 信息"""
        session = self.sessions.get(token)
        if session is None:
            return None

        return {
            "token": token,
            "user_id": session.user_id,
            "created_at": datetime.fromtimestamp(session.created_at).isoformat(),
            "expire_at": datetime.fromtimestamp(session.expire_at).isoformat(),
            "last_access": datetime.fromtimestamp(session.last_access).isoformat(),
            "is_expired": session.is_expired(),
        }


# 创建全局 SessionManager 实例
session_manager = SessionManager()
