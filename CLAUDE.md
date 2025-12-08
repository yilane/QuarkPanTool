# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

QuarkPanTool 是一个夸克网盘工具，用于批量转存分享文件、批量生成分享链接和批量下载夸克网盘文件。项目使用 Python 和 Playwright 实现，通过网页自动化登录获取 Cookie，无需手动操作。

## 环境设置与运行

### 安装依赖
```bash
pip install -r requirements.txt
playwright install firefox
```

### 运行方式

**命令行模式（CLI）**：
```bash
python quark.py              # 运行主程序
python quark_login.py        # 单独测试登录功能
```

**API 服务模式**：
```bash
python api/main.py           # 启动 FastAPI 服务
# 或使用启动脚本
./start_api.sh              # Linux/macOS
start_api.bat               # Windows
```

API 服务启动后可访问：
- Swagger 文档：`http://localhost:8080/docs`
- ReDoc 文档：`http://localhost:8080/redoc`

## 核心架构

### 主要模块

**命令行模式（CLI）**：

1. **quark_login.py** - 登录和 Cookie 管理
   - `QuarkLogin` 类：使用 Playwright 自动化浏览器登录夸克网盘
   - Cookie 存储路径：`config/cookies.txt`
   - 支持 Cookie 格式转换（字符串↔字典↔列表）

2. **quark.py** - CLI 核心业务逻辑
   - `QuarkPanFileManager` 类：管理所有网盘操作
   - 主要功能：
     - 分享链接转存文件（支持嵌套文件夹）
     - 批量生成分享链接（支持遍历深度配置）
     - 文件下载（已绕过 web 端文件大小限制）
     - 网盘目录管理
   - 使用 `asyncio` 处理异步 HTTP 请求

3. **utils.py** - 工具函数
   - 时间戳处理、日期格式化
   - 配置文件读写
   - 彩色日志输出
   - 随机码生成

**API 服务模式**：

4. **api/main.py** - FastAPI 应用主入口
   - 应用初始化、CORS 配置、生命周期管理
   - 路由定义：认证、目录管理、转存分享、任务查询
   - 基于 Bearer Token 的认证机制
   - 全局异常处理

5. **api/quark_service.py** - 业务逻辑封装层
   - `QuarkService` 类：独立实现，不依赖 `QuarkPanFileManager`
   - 核心方法：
     - `verify_cookies()` - 验证 Cookie 有效性
     - `create_directory()` - 创建网盘目录（自动处理同名冲突）
     - `transfer_and_share()` - 转存并生成分享链接
     - `get_task_status()` - 查询任务状态
   - 使用 `httpx.AsyncClient` 处理异步请求

6. **api/session_manager.py** - Session 管理
   - Token 生成与验证
   - Session 超时管理（默认 24 小时）
   - 定期清理过期 Session

7. **api/models.py** - Pydantic 数据模型
   - 请求/响应模型定义
   - 数据验证和序列化

8. **api/config.py** - 配置管理
   - 环境变量加载（基于 `.env` 文件）
   - API 服务配置（端口、CORS、日志等）

### 数据流程

**CLI 模式流程**：

1. **登录流程**：
   - Playwright 启动 Firefox 浏览器 → 用户手动登录 → 保存 Cookie → 后续请求使用 Cookie

2. **转存流程**：
   - 解析分享链接 → 获取 stoken → 获取文件详情 → 创建转存任务 → 轮询任务状态

3. **分享流程**：
   - 获取文件夹 ID → 创建分享任务 → 获取分享 ID → 提交分享 → 返回分享链接

4. **下载流程**：
   - 必须是用户自己网盘内的文件 → 获取下载 URL → 流式下载并显示进度条

**API 模式流程**：

1. **认证流程**：
   - 客户端提交 Cookie → 验证 Cookie 有效性 → 生成 Token → 返回 Token 和用户信息
   - 后续请求携带 `Authorization: Bearer <token>` 请求头

2. **转存并分享流程**：
   - 解析分享链接提取 pwd_id 和密码 → 获取 stoken → 获取文件详情
   - 创建转存任务 → 轮询任务状态直到完成 → 获取转存后的文件列表
   - 匹配转存的文件 FID → 创建分享任务 → 获取分享 ID → 提交分享 → 返回新分享链接

3. **目录创建流程**：
   - 调用创建目录 API → 如果同名冲突（错误码 23008）→ 查询已存在目录并返回 FID
   - 避免重复创建，自动返回已有目录信息

### 重要 API 端点

**夸克网盘 API**：
- 登录 Token: `https://drive-pc.quark.cn/1/clouddrive/share/sharepage/token`
- 文件详情: `https://drive-pc.quark.cn/1/clouddrive/share/sharepage/detail`
- 文件转存: `https://drive.quark.cn/1/clouddrive/share/sharepage/save`
- 文件下载: `https://drive-pc.quark.cn/1/clouddrive/file/download`
- 创建分享: `https://drive-pc.quark.cn/1/clouddrive/share`
- 任务查询: `https://drive-pc.quark.cn/1/clouddrive/task`
- 用户信息: `https://pan.quark.cn/account/info`
- 创建目录: `https://drive-pc.quark.cn/1/clouddrive/file`
- 文件列表: `https://drive-pc.quark.cn/1/clouddrive/file/sort`

**本地 FastAPI 服务端点**：
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/session` - 获取 Session 信息
- `GET /api/v1/auth/verify` - 验证登录状态
- `POST /api/v1/directory/create` - 创建网盘目录
- `POST /api/v1/share/transfer-and-share` - 转存并生成分享链接
- `POST /api/v1/task/status` - 查询任务状态
- `GET /api/health` - 健康检查

## 配置文件

**CLI 模式配置**：
- `config/cookies.txt` - 存储登录 Cookie
- `config/config.json` - 存储用户配置（用户名、保存目录ID、目录名称）
- `url.txt` - 批量转存/下载时的分享链接列表（一行一个）
- `share/share_url.txt` - 批量生成的分享链接保存位置
- `share/retry.txt` - 分享失败的重试列表

**API 服务配置**：
- `.env` - 环境变量配置文件（参考 `.env.example`）
  - `API_HOST` - 服务监听地址（默认 0.0.0.0）
  - `API_PORT` - 服务端口（默认 8080）
  - `SESSION_EXPIRE_HOURS` - Session 过期时间（默认 24 小时）
  - `CORS_ORIGINS` - CORS 允许的源（默认 *）
  - `LOG_LEVEL` - 日志级别（默认 INFO）

## 关键功能说明

### 分享链接格式
- 普通链接：`https://pan.quark.cn/s/abcd`
- 带密码链接：`https://pan.quark.cn/s/abcd?pwd=123456`

### 遍历深度选项（批量分享功能）
- 0：不遍历，只分享根目录
- 1：遍历并分享一级目录
- 2：遍历并分享两级目录

### 文件下载说明
- 下载的文件保存在 `downloads/` 目录
- 保持原始文件夹结构
- 使用 `tqdm` 显示下载进度

## 注意事项

### 通用注意事项
- Linux 环境下无法使用 Playwright 自动登录，需手动获取 Cookie 填入 `config/cookies.txt`
- Cookie 过期后会自动触发重新登录流程（CLI 模式）或返回 401 错误（API 模式）
- 网盘容量不足时转存会失败（错误码 32003）
- 下载功能仅支持自己网盘内的文件（`is_owner == 1`）
- 批量分享时会随机延迟 0.5-2 秒，避免请求过快被限制

### API 服务特定注意事项
- API 服务与 CLI 模式的业务逻辑独立实现，`QuarkService` 不依赖 `QuarkPanFileManager`
- Session Token 默认 24 小时有效期，过期后需重新登录
- 创建目录时自动处理同名冲突，返回已存在目录的 FID
- 转存并分享功能会自动匹配转存后的文件并生成分享链接
- 所有 API 请求需在请求头中携带 `Authorization: Bearer <token>`

### 常见错误码
- `23008` - 目录同名冲突（已自动处理）
- `32003` - 网盘容量不足
- `41013` - 目标文件夹不存在

## 开发建议

### 修改 API 业务逻辑时
- 修改 `api/quark_service.py` 中的 `QuarkService` 类
- 不要修改 `quark.py` 中的 `QuarkPanFileManager` 类，两者独立

### 添加新的 API 端点时
1. 在 `api/models.py` 中定义请求和响应模型
2. 在 `api/quark_service.py` 中实现业务逻辑
3. 在 `api/main.py` 中添加路由定义
4. 使用 `Depends(get_current_service)` 注入 `QuarkService` 实例

### 调试 API 服务
- 查看日志输出（控制台或 `logs/` 目录）
- 访问 `/docs` 查看 Swagger 文档并测试 API
- 调试信息会以 `[调试]` 前缀输出到控制台
