@echo off
chcp 65001 >nul
cls

echo ==========================================
echo   QuarkPanTool API 服务启动脚本
echo ==========================================
echo.

REM 检查是否安装了依赖
echo 📦 检查依赖...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ❌ 检测到缺少依赖，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败，请手动执行: pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo ✅ 依赖安装成功
) else (
    echo ✅ 依赖已安装
)

echo.

REM 创建日志目录
if not exist logs mkdir logs

REM 启动 API 服务
echo 🚀 正在启动 API 服务...
echo.
echo 📝 API 文档地址:
echo    - Swagger UI: http://localhost:8007/docs
echo    - ReDoc:      http://localhost:8007/redoc
echo.
echo 按 Ctrl+C 停止服务
echo.
echo ==========================================
echo.

REM 使用 uvicorn 启动
python -m uvicorn api.main:app --host 0.0.0.0 --port 8007 --reload

pause
