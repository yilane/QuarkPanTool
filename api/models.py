# -*- coding: utf-8 -*-
"""
API 数据模型定义
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== 通用响应模型 ====================

class ResponseModel(BaseModel):
    """统一响应模型"""
    code: int = Field(200, description="状态码")
    message: str = Field("success", description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")


# ==================== 认证相关模型 ====================

class LoginRequest(BaseModel):
    """登录请求模型"""
    cookies: str = Field(..., description="Cookie 字符串", min_length=10)
    user_id: Optional[str] = Field(None, description="可选的用户标识")


class UserInfo(BaseModel):
    """用户信息模型"""
    nickname: str = Field(..., description="用户昵称")


class LoginResponse(BaseModel):
    """登录响应数据"""
    access_token: str = Field(..., description="访问令牌")
    user_info: UserInfo = Field(..., description="用户信息")
    expire_time: int = Field(..., description="Token 过期时间戳（秒）")


# ==================== 目录管理相关模型 ====================

class CreateDirRequest(BaseModel):
    """创建目录请求模型"""
    dir_name: str = Field(..., description="文件夹名称", min_length=1, max_length=255)
    parent_dir_id: str = Field("0", description="父目录 ID，默认为根目录")


class CreateDirResponse(BaseModel):
    """创建目录响应数据"""
    fid: str = Field(..., description="文件夹 ID")
    dir_name: str = Field(..., description="文件夹名称")
    parent_dir_id: str = Field(..., description="父目录 ID")


# ==================== 转存和分享相关模型 ====================

class TransferAndShareRequest(BaseModel):
    """转存并分享请求模型"""
    share_url: str = Field(..., description="要转存的分享链接", min_length=10)
    save_dir_id: str = Field("0", description="转存到的目录 ID，默认为根目录")
    share_expire_type: int = Field(2, description="分享时长：1=永久 2=1天 3=7天 4=30天", ge=1, le=4)
    share_url_type: int = Field(1, description="分享类型：1=公开 2=加密", ge=1, le=2)
    share_password: Optional[str] = Field("", description="分享密码（加密时需要）", max_length=6)


class TransferInfo(BaseModel):
    """转存信息"""
    file_count: int = Field(..., description="文件数量")
    folder_count: int = Field(..., description="文件夹数量")
    file_list: List[str] = Field(..., description="文件列表")
    folder_list: List[str] = Field(..., description="文件夹列表")
    save_dir_name: str = Field(..., description="保存目录名称")


class TransferAndShareResponse(BaseModel):
    """转存并分享响应数据"""
    transfer_info: TransferInfo = Field(..., description="转存信息")
    share_url: str = Field(..., description="生成的分享链接")
    share_title: str = Field(..., description="分享标题")


# ==================== 任务状态查询相关模型 ====================

class TaskStatusRequest(BaseModel):
    """任务状态查询请求模型"""
    task_id: str = Field(..., description="任务 ID", min_length=1)


class TaskStatusResponse(BaseModel):
    """任务状态响应数据"""
    task_id: str = Field(..., description="任务 ID")
    status: int = Field(..., description="任务状态：0=进行中 1=失败 2=成功")
    task_title: str = Field(..., description="任务标题")
    progress: Optional[int] = Field(None, description="任务进度（百分比）")
    message: Optional[str] = Field(None, description="任务消息")
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")


# ==================== 错误响应模型 ====================

class ErrorDetail(BaseModel):
    """错误详情"""
    error_code: str = Field(..., description="错误代码")
    error_message: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
