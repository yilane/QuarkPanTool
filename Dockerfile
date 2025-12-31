# 使用官方 Python 3.11 镜像（基于 Debian Bookworm，更稳定）
FROM python:3.11-slim-bookworm

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# 安装基础工具和 Playwright 依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    # 基础工具
    curl \
    wget \
    ca-certificates \
    tzdata \
    # 清理
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 安装 Playwright 浏览器依赖（自动安装所需的系统包）
# 这会自动安装所有 Firefox 需要的系统依赖
RUN playwright install-deps firefox && \
    playwright install firefox

# 清理 apt 缓存以减小镜像大小
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/config \
    /app/share \
    /app/downloads \
    /app/logs && \
    chmod -R 755 /app

# 创建空的配置文件（可选，避免挂载时报错）
RUN touch /app/config/.gitkeep

# 创建非 root 用户运行应用（可选，提高安全性）
# RUN useradd -m -u 1000 quark && \
#     chown -R quark:quark /app
# USER quark

# 暴露端口
EXPOSE 8007

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8007/api/health || exit 1

# 启动命令
CMD ["python", "api/main.py"]
