@echo off
chcp 65001 >nul
REM QuarkPanTool Docker 启动脚本 (Windows)
REM 使用方法: start_docker.bat [命令]

echo ========================================
echo     QuarkPanTool Docker 管理脚本
echo ========================================
echo.

REM 检查 Docker 是否安装
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未安装，请先安装 Docker Desktop
    pause
    exit /b 1
)

REM 检查 docker-compose 是否可用
docker-compose --version >nul 2>&1
if errorlevel 1 (
    docker compose version >nul 2>&1
    if errorlevel 1 (
        echo [错误] docker-compose 未安装或不可用
        pause
        exit /b 1
    )
    set COMPOSE_CMD=docker compose
) else (
    set COMPOSE_CMD=docker-compose
)

REM 检查 .env 文件
if not exist .env (
    echo [警告] .env 文件不存在，将使用默认配置
    echo [提示] 你可以复制 .env.example 为 .env 并修改配置
    echo.
)

REM 获取命令参数
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=help

if /i "%COMMAND%"=="build" (
    echo [执行] 正在构建 Docker 镜像...
    %COMPOSE_CMD% build --no-cache
    if errorlevel 1 (
        echo [失败] 镜像构建失败
        pause
        exit /b 1
    )
    echo [成功] 镜像构建完成
    goto :end
)

if /i "%COMMAND%"=="build-cn" (
    echo [执行] 正在使用国内镜像源构建 Docker 镜像...
    docker-compose -f docker-compose.cn.yml build --no-cache
    if errorlevel 1 (
        echo [失败] 镜像构建失败
        pause
        exit /b 1
    )
    echo [成功] 镜像构建完成（使用国内镜像源）
    goto :end
)

if /i "%COMMAND%"=="up" (
    echo [执行] 正在启动服务...
    %COMPOSE_CMD% up -d
    if errorlevel 1 (
        echo [失败] 服务启动失败
        pause
        exit /b 1
    )
    echo [成功] 服务已启动
    echo [访问] http://localhost:8007/docs
    goto :end
)

if /i "%COMMAND%"=="down" (
    echo [执行] 正在停止服务...
    %COMPOSE_CMD% down
    echo [成功] 服务已停止
    goto :end
)

if /i "%COMMAND%"=="restart" (
    echo [执行] 正在重启服务...
    %COMPOSE_CMD% restart
    echo [成功] 服务已重启
    goto :end
)

if /i "%COMMAND%"=="logs" (
    echo [执行] 查看日志 (Ctrl+C 退出)...
    %COMPOSE_CMD% logs -f
    goto :end
)

if /i "%COMMAND%"=="ps" (
    echo [执行] 当前运行的容器:
    %COMPOSE_CMD% ps
    goto :end
)

if /i "%COMMAND%"=="clean" (
    echo [执行] 正在清理容器、镜像和数据卷...
    %COMPOSE_CMD% down -v --rmi all
    echo [成功] 清理完成
    goto :end
)

if /i "%COMMAND%"=="shell" (
    echo [执行] 进入容器 Shell...
    docker exec -it quarkpantool /bin/bash
    goto :end
)

REM 显示帮助信息
echo 使用方法: start_docker.bat [命令]
echo.
echo 可用命令:
echo   build      - 构建 Docker 镜像（国际版）
echo   build-cn   - 构建 Docker 镜像（使用国内镜像源，网络慢时推荐）
echo   up         - 启动服务（后台运行）
echo   down       - 停止服务
echo   restart    - 重启服务
echo   logs       - 查看实时日志
echo   ps         - 查看运行状态
echo   clean      - 清理所有容器和镜像
echo   shell      - 进入容器 Shell
echo   help       - 显示此帮助信息
echo.
echo 快速开始:
echo   1. start_docker.bat build      # 首次使用需要构建镜像
echo      或
echo      start_docker.bat build-cn   # 国内网络环境推荐使用
echo   2. start_docker.bat up         # 启动服务
echo   3. 访问 http://localhost:8007/docs
echo.
echo 故障排查:
echo   - 如果构建失败，尝试: start_docker.bat build-cn
echo   - 查看日志: start_docker.bat logs
echo   - 完全清理后重建: start_docker.bat clean 然后 start_docker.bat build

:end
echo.
pause
