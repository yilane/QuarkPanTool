#!/bin/bash

# QuarkPanTool Docker 启动脚本
# 使用方法: ./start_docker.sh [命令]
# 命令: build, up, down, restart, logs, ps

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    QuarkPanTool Docker 管理脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装，请先安装 Docker${NC}"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}错误: docker-compose 未安装，请先安装 docker-compose${NC}"
    exit 1
fi

# 兼容 docker-compose 和 docker compose 两种命令
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo -e "${YELLOW}警告: .env 文件不存在，将使用默认配置${NC}"
    echo -e "${YELLOW}提示: 你可以复制 .env.example 为 .env 并修改配置${NC}"
fi

# 获取命令参数
COMMAND=${1:-help}

case "$COMMAND" in
    build)
        echo -e "${GREEN}正在构建 Docker 镜像...${NC}"
        $COMPOSE_CMD build --no-cache
        echo -e "${GREEN}✓ 镜像构建完成${NC}"
        ;;

    build-cn)
        echo -e "${GREEN}正在使用国内镜像源构建 Docker 镜像...${NC}"
        docker-compose -f docker-compose.cn.yml build --no-cache
        echo -e "${GREEN}✓ 镜像构建完成（使用国内镜像源）${NC}"
        ;;

    up)
        echo -e "${GREEN}正在启动服务...${NC}"
        $COMPOSE_CMD up -d
        echo -e "${GREEN}✓ 服务已启动${NC}"
        echo -e "${GREEN}访问地址: http://localhost:8007/docs${NC}"
        ;;

    down)
        echo -e "${YELLOW}正在停止服务...${NC}"
        $COMPOSE_CMD down
        echo -e "${GREEN}✓ 服务已停止${NC}"
        ;;

    restart)
        echo -e "${YELLOW}正在重启服务...${NC}"
        $COMPOSE_CMD restart
        echo -e "${GREEN}✓ 服务已重启${NC}"
        ;;

    logs)
        echo -e "${GREEN}查看日志 (Ctrl+C 退出)...${NC}"
        $COMPOSE_CMD logs -f
        ;;

    ps)
        echo -e "${GREEN}当前运行的容器:${NC}"
        $COMPOSE_CMD ps
        ;;

    clean)
        echo -e "${YELLOW}正在清理容器、镜像和数据卷...${NC}"
        $COMPOSE_CMD down -v --rmi all
        echo -e "${GREEN}✓ 清理完成${NC}"
        ;;

    shell)
        echo -e "${GREEN}进入容器 Shell...${NC}"
        docker exec -it quarkpantool /bin/bash
        ;;

    help|*)
        echo -e "${GREEN}使用方法: ./start_docker.sh [命令]${NC}"
        echo ""
        echo "可用命令:"
        echo "  build      - 构建 Docker 镜像（国际版）"
        echo "  build-cn   - 构建 Docker 镜像（使用国内镜像源，网络慢时推荐）"
        echo "  up         - 启动服务（后台运行）"
        echo "  down       - 停止服务"
        echo "  restart    - 重启服务"
        echo "  logs       - 查看实时日志"
        echo "  ps         - 查看运行状态"
        echo "  clean      - 清理所有容器和镜像"
        echo "  shell      - 进入容器 Shell"
        echo "  help       - 显示此帮助信息"
        echo ""
        echo "快速开始:"
        echo "  1. ./start_docker.sh build      # 首次使用需要构建镜像"
        echo "     或"
        echo "     ./start_docker.sh build-cn   # 国内网络环境推荐使用"
        echo "  2. ./start_docker.sh up         # 启动服务"
        echo "  3. 访问 http://localhost:8007/docs"
        echo ""
        echo "故障排查:"
        echo "  - 如果构建失败，尝试: ./start_docker.sh build-cn"
        echo "  - 查看日志: ./start_docker.sh logs"
        echo "  - 完全清理后重建: ./start_docker.sh clean && ./start_docker.sh build"
        ;;
esac
