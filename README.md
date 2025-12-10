# QuarkPanTool

[![Python Version](https://img.shields.io/badge/python-3.11.6-blue.svg)](https://www.python.org/downloads/release/python-3116/)
[![Latest Release](https://img.shields.io/github/v/release/ihmily/QuarkPanTool)](https://github.com/ihmily/QuarkPanTool/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/ihmily/QuarkPanTool/total)](https://github.com/ihmily/QuarkPanTool/releases/latest)
![GitHub Repo stars](https://img.shields.io/github/stars/ihmily/QuarkPanTool?style=social)


QuarkPanTool 是一个简单易用的小工具，旨在帮助用户快速批量转存分享文件、批量生成分享链接和批量下载夸克网盘文件。支持命令行模式和 API 服务模式两种使用方式。

## 功能特点

- 🔐 运行稳定：基于 Playwright 支持网页登录夸克网盘，无需手动获取 Cookie。
- 🖥️ 轻松操作：简洁直观的命令行界面，方便快捷地完成文件转存。
- 📦 批量转存：支持一次性转存多个夸克网盘分享链接中的文件。
- 🔗 批量分享：支持一次性将某个文件夹内的所有文件夹批量生成分享链接，无需手动分享文件。
- 💾 本地下载：支持批量下载网盘文件夹中的文件，已绕过 web 端文件大小下载限制，无需 VIP。
- 🚀 API 服务：提供 RESTful API 接口，支持二次开发和集成。
- 🔄 批量转存分享：API 模式支持批量转存多个链接并自动生成新的分享链接。
- 🛡️ 网络重试机制：自动处理网络异常，提高任务执行成功率。

## 如何使用

如果不想自己部署环境，可以下载打包好的可执行文件(exe)压缩包 [QuarkPanTool](https://github.com/ihmily/QuarkPanTool/releases) ，解压后直接运行即可。

### 快速开始

**1. 下载代码**

```bash
git clone https://github.com/ihmily/QuarkPanTool.git
cd QuarkPanTool
```

**2. 安装依赖**

```bash
pip install -r requirements.txt
playwright install firefox
```

### 使用方式

#### 方式一：命令行模式（CLI）

适合个人使用，提供交互式界面。

```bash
python quark.py
```

运行后会使用 Playwright 进行登录操作，当然也可以自己手动获取 Cookie 填写到 `config/cookies.txt` 文件中。

更多说明请浏览 [wiki](https://github.com/ihmily/QuarkPanTool/wiki) 页面

#### 方式二：API 服务模式

适合二次开发和系统集成，提供 RESTful API 接口。

**1. 配置环境变量（可选）**

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

配置项说明：
- `HOST`: 服务监听地址（默认 `0.0.0.0`）
- `PORT`: 服务端口（默认 `8007`）
- `TOKEN_EXPIRE_HOURS`: Token 有效期（默认 `240` 小时）
- `TOKEN_CLEANUP_INTERVAL`: Session 清理间隔（默认 `3600` 秒）
- `LOG_LEVEL`: 日志级别（默认 `INFO`）
- `LOG_FILE`: 日志文件路径（默认 `logs/api.log`）
- `DEBUG`: 调试模式（默认 `True`）

**2. 启动服务**

```bash
# 方式1: 直接运行
python api/main.py

# 方式2: 使用启动脚本
./start_api.sh              # Linux/macOS
start_api.bat               # Windows
```

**3. 访问文档**

服务启动后，访问以下地址查看 API 文档：
- Swagger 文档：http://localhost:8007/docs
- ReDoc 文档：http://localhost:8007/redoc

> 注：默认端口为 8007，如需修改请在 `.env` 文件中配置 `PORT` 参数

**4. 使用示例**

```bash
# 登录获取 Token
curl -X POST "http://localhost:8007/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "cookies": "你的Cookie字符串"
  }'

# 使用 Token 调用 API（转存并分享）
curl -X POST "http://localhost:8007/api/v1/share/transfer-and-share" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "share_url": "https://pan.quark.cn/s/abcd?pwd=123456",
    "save_dir_id": "0",
    "share_expire_type": 2,
    "share_url_type": 1
  }'

# 创建网盘目录
curl -X POST "http://localhost:8007/api/v1/directory/create" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "dir_name": "我的文件夹",
    "parent_dir_id": "0"
  }'

# 批量转存并分享（一次处理多个链接）
curl -X POST "http://localhost:8007/api/v1/share/batch-transfer-and-share" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "share_urls": [
      "https://pan.quark.cn/s/abcd1?pwd=123456",
      "https://pan.quark.cn/s/abcd2?pwd=654321",
      "https://pan.quark.cn/s/abcd3"
    ],
    "save_dir_id": "0",
    "share_expire_type": 2,
    "share_url_type": 1
  }'
```

### API 接口列表

| 接口路径 | 方法 | 说明 |
|---------|------|------|
| `/api/v1/auth/login` | POST | 用户登录，获取访问令牌 |
| `/api/v1/auth/session` | GET | 获取当前 Session 信息 |
| `/api/v1/auth/verify` | GET | 验证登录状态是否有效 |
| `/api/v1/directory/create` | POST | 创建网盘目录 |
| `/api/v1/share/transfer-and-share` | POST | 转存分享链接并生成新的分享链接 |
| `/api/v1/share/batch-transfer-and-share` | POST | **批量转存并生成分享链接（新增）** |
| `/api/v1/task/status` | POST | 查询任务执行状态 |
| `/api/health` | GET | 健康检查 |

## 注意事项

### 通用注意事项

- **首次登录**：首次运行会比较缓慢，程序会自动打开浏览器让你登录夸克网盘。登录完成后，请不要手动关闭浏览器，回到软件界面按 Enter 键，浏览器会自动关闭并保存登录信息。
- **Linux 环境**：Linux 环境下无法使用 Playwright 自动登录，请自行在网页获取 Cookie 后填入 `config/cookies.txt` 文件使用。
- **分享链接格式**：如果分享地址有密码，需在地址末尾加上 `?pwd=提取码`。
  - 示例：`https://pan.quark.cn/s/abcd?pwd=123456`

### CLI 模式注意事项

- 执行批量转存之前，请先在 `url.txt` 文件中填写网盘分享地址（一行一个）。
- Cookie 过期后会自动触发重新登录流程。

### API 服务模式注意事项

- **认证机制**：所有 API 请求（除登录接口外）需在请求头中携带 `Authorization: Bearer <token>`。
- **Token 有效期**：Token 默认 240 小时（10天）有效期，过期后需重新登录获取新 Token。
- **Cookie 获取**：可通过浏览器开发者工具获取 Cookie 字符串，具体方法请参考 [wiki](https://github.com/ihmily/QuarkPanTool/wiki)。
- **批量转存**：使用批量转存接口时，系统会自动为每个链接添加 2-4 秒的延迟，避免触发服务器限制。
- **网络重试**：系统内置网络重试机制，单次请求失败会自动重试最多 3 次，提高成功率。

## 项目结构

```
QuarkPanTool/
├── api/                      # API 服务模块
│   ├── main.py              # FastAPI 应用主入口
│   ├── quark_service.py     # 业务逻辑封装层
│   ├── session_manager.py   # Session 管理
│   ├── models.py            # 数据模型定义
│   └── config.py            # 配置管理
├── config/                   # 配置文件目录
│   ├── cookies.txt          # Cookie 存储（CLI 模式）
│   └── config.json          # 用户配置
├── share/                    # 分享链接存储目录
│   ├── share_url.txt        # 生成的分享链接
│   └── retry.txt            # 失败重试列表
├── logs/                     # 日志目录
├── quark.py                 # CLI 主程序
├── quark_login.py           # 登录模块
├── utils.py                 # 工具函数
├── url.txt                  # 批量转存的链接列表
├── .env                     # 环境变量配置（需自行创建）
├── .env.example             # 环境变量配置示例
├── requirements.txt         # Python 依赖
├── start_api.sh            # Linux/macOS 启动脚本
└── start_api.bat           # Windows 启动脚本
```

## 技术栈

- **Python 3.11+**: 核心开发语言
- **Playwright**: 浏览器自动化，用于登录获取 Cookie
- **httpx**: 异步 HTTP 客户端
- **FastAPI**: RESTful API 框架
- **Pydantic**: 数据验证和序列化
- **uvicorn**: ASGI 服务器

## 效果演示

![ScreenShot1](./images/Snipaste_2024-09-23_19-02-03.jpg)

## 常见问题

### 1. 如何获取 Cookie？

**方法一：使用 Playwright 自动登录（推荐）**
- 运行 `python quark_login.py` 或 `python quark.py`
- 程序会自动打开浏览器，手动登录后按 Enter 键
- Cookie 会自动保存到 `config/cookies.txt`

**方法二：手动获取（适用于 Linux 或自动登录失败的情况）**
1. 使用浏览器访问 https://pan.quark.cn
2. 登录你的夸克网盘账号
3. 按 F12 打开开发者工具
4. 切换到 "Network"（网络）标签
5. 刷新页面，找到任意请求
6. 在请求头中找到 `Cookie` 字段，复制完整的 Cookie 字符串
7. 将 Cookie 粘贴到 `config/cookies.txt` 文件中

### 2. API 模式和 CLI 模式可以同时使用吗？

可以。两种模式使用独立的业务逻辑实现，不会互相干扰。但建议使用相同的 Cookie。

### 3. Token 过期了怎么办？

重新调用登录接口 `/api/v1/auth/login` 获取新的 Token。

### 4. 转存失败提示"网盘容量不足"怎么办？

需要清理网盘空间或升级网盘容量。错误码：32003

### 5. Linux 环境无法自动登录？

Linux 环境下 Playwright 可能无法正常启动浏览器，建议手动获取 Cookie 后填入配置文件。

### 6. 如何修改 API 服务端口？

在 `.env` 文件中修改 `PORT` 配置项，或直接修改 `api/config.py` 中的默认值。

### 7. 批量转存时为什么处理很慢？

为了避免触发服务器的频率限制，系统会在每个链接处理之间自动添加 2-4 秒的延迟。这是正常现象，可以提高成功率。

### 8. 网络请求失败会怎样？

系统内置了网络重试机制，单次请求失败会自动重试最多 3 次。如果 3 次都失败，会在批量处理结果中标记为失败，并返回错误信息。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发流程

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 添加必要的注释和文档字符串
- 确保代码通过测试

## 更新日志

### v0.0.5
- 绕过文件下载大小限制
- 改进错误处理

### v0.0.6
- 🚀 新增 FastAPI RESTful API 服务模式
- 🔐 支持 Token 认证和 Session 管理
- 📝 提供 Swagger 和 ReDoc API 文档
- 🔄 独立的 API 业务逻辑实现
- ⚙️ 支持环境变量配置

### v0.0.7（当前版本）
- ✨ **新增批量转存并分享接口** - 支持一次处理多个分享链接
- 🛡️ **增强网络重试机制** - 单次请求失败自动重试最多 3 次
- 📊 **改进错误处理** - 更详细的错误信息和调试日志
- ⚙️ **优化配置项** - 更新环境变量配置，延长默认 Token 有效期至 240 小时
- 🎯 **批量处理优化** - 自动添加请求延迟，避免触发服务器限制

## 许可证

QuarkPanTool 使用 [Apache-2.0 license](https://github.com/ihmily/QuarkPanTool#Apache-2.0-1-ov-file) 许可证，详情请参阅 LICENSE 文件。

------

**免责声明**：本工具仅供学习和研究使用，请勿用于非法目的。由使用本工具引起的任何法律责任，与本工具作者无关。
