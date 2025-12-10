# -*- coding: utf-8 -*-
"""
QuarkPanTool FastAPI 应用主入口
"""
import os
import sys
import time
import asyncio
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.config import settings
from api.models import (
    ResponseModel,
    LoginRequest,
    LoginResponse,
    CreateDirRequest,
    CreateDirResponse,
    TransferAndShareRequest,
    TransferAndShareResponse,
    TaskStatusRequest,
    TaskStatusResponse,
    BatchTransferAndShareRequest,
    BatchTransferAndShareResponse,
)
from api.session_manager import session_manager
from api.quark_service import QuarkService


# ==================== 生命周期管理 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    print(f"🚀 {settings.APP_NAME} 正在启动...")
    print(f"📝 API 文档地址: http://{settings.HOST}:{settings.PORT}/docs")

    # 启动 Session 清理任务
    cleanup_task = asyncio.create_task(session_manager.start_cleanup_task())

    yield

    # 关闭时执行
    print(f"👋 {settings.APP_NAME} 正在关闭...")
    cleanup_task.cancel()


# ==================== FastAPI 应用初始化 ====================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="夸克网盘 API 服务 - 支持转存、分享、目录管理等功能",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 依赖注入 ====================

async def get_current_service(authorization: Optional[str] = Header(None)) -> QuarkService:
    """
    从请求头中获取 Token 并返回对应的 QuarkService

    Args:
        authorization: 请求头中的 Authorization

    Returns:
        QuarkService 实例

    Raises:
        HTTPException: Token 无效或已过期
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization 请求头")

    # 解析 Bearer Token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization 格式错误，应为: Bearer <token>")

    token = parts[1]

    # 获取 Session
    session = session_manager.get_session(token)
    if session is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    # 返回 QuarkService 实例
    if session.manager is None:
        session.manager = QuarkService(cookies=session.cookies)

    return session.manager


# ==================== 全局异常处理 ====================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": str(exc),
            "data": None
        }
    )


# ==================== 健康检查接口 ====================

@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return ResponseModel(
        code=200,
        message="服务运行正常",
        data={
            "status": "healthy",
            "version": settings.APP_VERSION,
            "session_count": session_manager.get_session_count(),
        }
    )


# ==================== 认证相关接口 ====================

@app.post(
    f"{settings.API_PREFIX}/auth/login",
    response_model=ResponseModel,
    tags=["认证管理"],
    summary="用户登录",
    description="通过传入 Cookie 信息实现网盘登录，返回访问令牌"
)
async def login(request: LoginRequest):
    """
    用户登录接口

    - **cookies**: Cookie 字符串（必填）
    - **user_id**: 可选的用户标识
    """
    try:
        # 创建 QuarkService 实例
        service = QuarkService(cookies=request.cookies)

        # 验证 Cookies 并获取用户信息
        user_info = await service.verify_cookies()

        # 创建 Session
        token, session = await session_manager.create_session(
            cookies=request.cookies,
            user_id=request.user_id
        )

        # 将 service 实例存储到 session 中
        session.manager = service

        # 返回登录结果
        response_data = LoginResponse(
            access_token=token,
            user_info=user_info,
            expire_time=int(session.expire_at)
        )

        return ResponseModel(
            code=200,
            message="登录成功",
            data=response_data.model_dump()
        )

    except Exception as e:
        return ResponseModel(
            code=400,
            message=f"登录失败: {str(e)}",
            data=None
        )


@app.get(
    f"{settings.API_PREFIX}/auth/session",
    response_model=ResponseModel,
    tags=["认证管理"],
    summary="获取 Session 信息",
    description="获取当前 Token 的 Session 信息"
)
async def get_session_info(authorization: Optional[str] = Header(None)):
    """获取 Session 信息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少 Authorization 请求头")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Authorization 格式错误")

    token = parts[1]
    info = session_manager.get_session_info(token)

    if info is None:
        raise HTTPException(status_code=401, detail="Token 无效或已过期")

    return ResponseModel(
        code=200,
        message="获取成功",
        data=info
    )


@app.get(
    f"{settings.API_PREFIX}/auth/verify",
    response_model=ResponseModel,
    tags=["认证管理"],
    summary="验证登录状态",
    description="验证当前 Token 对应的夸克网盘登录状态是否有效"
)
async def verify_login_status(service: QuarkService = Depends(get_current_service)):
    """
    验证登录状态接口

    通过重新调用夸克网盘的用户信息接口来验证 Cookie 是否仍然有效

    Returns:
        - 登录状态有效：返回用户信息
        - 登录状态无效：返回错误信息
    """
    try:
        # 重新验证 Cookie 是否有效
        user_info = await service.verify_cookies()

        return ResponseModel(
            code=200,
            message="登录状态有效",
            data={
                "is_valid": True,
                "user_info": user_info.model_dump()
            }
        )

    except Exception as e:
        return ResponseModel(
            code=401,
            message=f"登录状态无效: {str(e)}",
            data={
                "is_valid": False,
                "error": str(e)
            }
        )


# ==================== 目录管理接口 ====================

@app.post(
    f"{settings.API_PREFIX}/directory/create",
    response_model=ResponseModel,
    tags=["目录管理"],
    summary="创建网盘目录",
    description="在指定位置创建新的网盘目录"
)
async def create_directory(
    request: CreateDirRequest,
    service: QuarkService = Depends(get_current_service)
):
    """
    创建网盘目录

    - **dir_name**: 目录名称（必填）
    - **parent_dir_id**: 父目录 ID，默认为根目录 "0"
    """
    try:
        result = await service.create_directory(
            dir_name=request.dir_name,
            parent_dir_id=request.parent_dir_id
        )

        return ResponseModel(
            code=200,
            message="目录创建成功",
            data=result.model_dump()
        )

    except Exception as e:
        return ResponseModel(
            code=400,
            message=f"创建目录失败: {str(e)}",
            data=None
        )


# ==================== 转存和分享接口 ====================

@app.post(
    f"{settings.API_PREFIX}/share/transfer-and-share",
    response_model=ResponseModel,
    tags=["转存分享"],
    summary="转存并生成分享链接",
    description="将分享链接的文件转存到网盘，然后生成新的分享链接"
)
async def transfer_and_share(
    request: TransferAndShareRequest,
    service: QuarkService = Depends(get_current_service)
):
    """
    转存并生成分享链接

    - **share_url**: 要转存的分享链接（必填）
    - **save_dir_id**: 转存到的目录 ID，默认为根目录 "0"
    - **share_expire_type**: 分享时长（1=永久 2=1天 3=7天 4=30天）
    - **share_url_type**: 分享类型（1=公开 2=加密）
    - **share_password**: 分享密码（加密时需要）
    """
    try:
        result = await service.transfer_and_share(
            share_url=request.share_url,
            save_dir_id=request.save_dir_id,
            share_expire_type=request.share_expire_type,
            share_url_type=request.share_url_type,
            share_password=request.share_password
        )

        return ResponseModel(
            code=200,
            message="转存并分享成功",
            data=result.model_dump()
        )

    except Exception as e:
        return ResponseModel(
            code=400,
            message=f"操作失败: {str(e)}",
            data=None
        )


@app.post(
    f"{settings.API_PREFIX}/share/batch-transfer-and-share",
    response_model=ResponseModel,
    tags=["转存分享"],
    summary="批量转存并生成分享链接",
    description="批量将多个分享链接的文件转存到网盘，然后为每个转存的文件生成新的分享链接"
)
async def batch_transfer_and_share(
    request: BatchTransferAndShareRequest,
    service: QuarkService = Depends(get_current_service)
):
    """
    批量转存并生成分享链接

    - **share_urls**: 要转存的分享链接列表（必填，至少一个）
    - **save_dir_id**: 转存到的目录 ID，默认为根目录 "0"
    - **share_expire_type**: 分享时长（1=永久 2=1天 3=7天 4=30天）
    - **share_url_type**: 分享类型（1=公开 2=加密）
    - **share_password**: 分享密码（加密时需要）

    返回每个链接的转存结果，包括原始链接和新生成的分享链接的对应关系
    """
    try:
        result = await service.batch_transfer_and_share(
            share_urls=request.share_urls,
            save_dir_id=request.save_dir_id,
            share_expire_type=request.share_expire_type,
            share_url_type=request.share_url_type,
            share_password=request.share_password
        )

        return ResponseModel(
            code=200,
            message=f"批量转存完成：成功 {result.success_count} 个，失败 {result.failed_count} 个",
            data=result.model_dump()
        )

    except Exception as e:
        return ResponseModel(
            code=400,
            message=f"批量操作失败: {str(e)}",
            data=None
        )


# ==================== 任务状态查询接口 ====================

@app.post(
    f"{settings.API_PREFIX}/task/status",
    response_model=ResponseModel,
    tags=["任务管理"],
    summary="查询任务状态",
    description="查询转存或分享任务的执行状态"
)
async def get_task_status(
    request: TaskStatusRequest,
    service: QuarkService = Depends(get_current_service)
):
    """
    查询任务状态

    - **task_id**: 任务 ID（必填）
    """
    try:
        result = await service.get_task_status(task_id=request.task_id)

        return ResponseModel(
            code=200,
            message="查询成功",
            data=result.model_dump()
        )

    except Exception as e:
        return ResponseModel(
            code=400,
            message=f"查询失败: {str(e)}",
            data=None
        )


# ==================== 根路径 ====================

@app.get("/", tags=["首页"])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
    }


# ==================== 启动入口 ====================

if __name__ == "__main__":
    import uvicorn

    # 创建日志目录
    if settings.LOG_FILE:
        os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)

    # 启动服务
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )
