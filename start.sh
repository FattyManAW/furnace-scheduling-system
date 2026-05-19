#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  干式套管最佳化排爐系統 — 一鍵啟動腳本 v3.0
#  整合：docker compose 啟動 / 健康檢查 / 日誌追蹤 / 一鍵重置
#
#  用法:
#    ./start.sh              # 一鍵啟動（首次自動 clone + build）
#    ./start.sh --logs       # 啟動後自動追蹤日誌
#    ./start.sh --rebuild    # 強制重新 build
#    ./start.sh --reset      # 清除所有資料 + 重新初始化
#    ./start.sh --stop       # 停止所有服務
#    ./start.sh --status     # 顯示服務狀態
#    ./start.sh --help       # 顯示說明
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── 顏色 ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

# ── 常數 ────────────────────────────────────────────────────────
REPO_URL="https://github.com/FattyManAW/furnace-scheduling-system.git"
REPO_DIR="furnace-scheduling-system"
API_PORT="${PORT:-8002}"
NGINX_PORT="${NGINX_PORT:-8030}"
API_URL="http://localhost:${API_PORT}"
HEALTH_URL="${API_URL}/health"
TZ="${TZ:-Asia/Taipei}"

# ── 輔助函數 ────────────────────────────────────────────────────
print_banner() {
  echo ""
  echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
  echo -e "${BOLD}${CYAN}║   干式套管最佳化排爐系統 — 一鍵啟動器 v3   ║${NC}"
  echo -e "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
  echo ""
}

check_docker() {
  if ! command -v docker &>/dev/null; then
    echo -e "${RED}❌ Docker 未安裝${NC}"
    echo "   macOS: brew install --cask docker"
    echo "   或下載: https://docs.docker.com/get-docker/"
    exit 1
  fi
  if ! docker info &>/dev/null; then
    echo -e "${RED}❌ Docker daemon 未運行，請先啟動 Docker Desktop${NC}"
    exit 1
  fi
  echo -e "${GREEN}✅ Docker ${BOLD}$(docker --version | cut -d' ' -f3 | tr -d ',')${NC}${GREEN} 已就緒${NC}"
}

health_check() {
  local max_retries=${1:-30}
  local delay=${2:-2}
  echo -e "${CYAN}⏳ 等待服務就緒...${NC}"
  for i in $(seq 1 $max_retries); do
    if curl -sf "${HEALTH_URL}" &>/dev/null; then
      echo -e "${GREEN}✅ 健康檢查通過 (${i}s)${NC}"
      return 0
    fi
    printf "."
    sleep $delay
  done
  echo ""
  echo -e "${RED}❌ 健康檢查失敗（${max_retries} 次重試）${NC}"
  echo -e "   ${YELLOW}查看日誌: docker compose logs api${NC}"
  return 1
}

verify_api() {
  echo ""
  echo -e "${BOLD}📊 API 端點驗證${NC}"
  local endpoints=(
    "/health|健康檢查"
    "/api/v1/orders/count|訂單統計"
    "/api/v1/molds/|模具列表"
    "/api/v1/kilns/|干燥罐列表"
    "/docs|Swagger 文件"
  )
  for ep in "${endpoints[@]}"; do
    path="${ep%%|*}"
    label="${ep##*|}"
    if curl -sf "${API_URL}${path}" &>/dev/null; then
      echo -e "   ${GREEN}✓${NC} ${label} ${API_URL}${path}"
    else
      echo -e "   ${RED}✗${NC} ${label} ${API_URL}${path}"
    fi
  done
}

show_status() {
  echo -e "${BOLD}📡 服務狀態${NC}"
  if curl -sf "${HEALTH_URL}" &>/dev/null; then
    echo -e "   ${GREEN}●${NC} API   → ${API_URL}"
    echo -e "   ${GREEN}●${NC} Docs  → ${API_URL}/docs"
    local count=$(curl -sf "${API_URL}/api/v1/orders/count" | python3 -c "import sys,json; print(json.load(sys.stdin).get('count','?'))" 2>/dev/null || echo "?")
    echo -e "   ${GREEN}●${NC} 訂單數: ${count}"
    echo -e "   ${GREEN}●${NC} 前端  → http://localhost:${NGINX_PORT}"
  else
    echo -e "   ${RED}●${NC} 服務未運行 — 執行 ./start.sh 啟動"
  fi
  echo ""
}

# ── 命令解析 ────────────────────────────────────────────────────
CMD="${1:-start}"

case "$CMD" in
  --help|-h)
    print_banner
    echo "用法: ./start.sh [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  (無)        一鍵啟動服務（預設）"
    echo "  --logs      啟動後自動追蹤日誌"
    echo "  --rebuild   強制重新 build Docker 映像"
    echo "  --reset     清除所有資料 + 重新初始化"
    echo "  --stop      停止所有服務"
    echo "  --status    顯示服務狀態"
    echo "  --help      顯示此說明"
    echo ""
    echo "環境變數:"
    echo "  PORT=8002         後端 API port"
    echo "  NGINX_PORT=8030   前端 nginx port"
    echo "  TZ=Asia/Taipei    時區"
    exit 0
    ;;

  --status)
    show_status
    exit 0
    ;;

  --stop)
    if [ -d "$REPO_DIR" ]; then
      cd "$REPO_DIR"
      docker compose down 2>/dev/null || true
      echo -e "${GREEN}✅ 服務已停止${NC}"
    fi
    exit 0
    ;;
esac

# ── 主流程 ──────────────────────────────────────────────────────
print_banner
check_docker

# ── Clone / 更新 ────────────────────────────────────────────────
if [ -d "$REPO_DIR/.git" ]; then
  echo -e "${BLUE}📦 更新專案...${NC}"
  cd "$REPO_DIR"
  git fetch origin 2>/dev/null
  LOCAL=$(git rev-parse HEAD)
  REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "$LOCAL")
  if [ "$LOCAL" != "$REMOTE" ]; then
    echo -e "   有新版本，更新中..."
    git pull --rebase origin main
  else
    echo -e "   已是最新版本"
  fi
else
  echo -e "${BLUE}📦 下載專案...${NC}"
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi
echo -e "${GREEN}✅ 原始碼已就緒${NC}"

# ── 設定環境變數 ────────────────────────────────────────────────
export PORT="$API_PORT"
export TZ="$TZ"
if [ ! -f .env ]; then
  cat > .env <<EOF
PORT=${API_PORT}
TZ=${TZ}
EOF
  echo -e "${GREEN}✅ .env 已建立${NC}"
fi

# ── 停止舊容器 ──────────────────────────────────────────────────
docker compose down 2>/dev/null || true

# ── Build & 啟動 ────────────────────────────────────────────────
BUILD_FLAG=""
if [ "$CMD" = "--rebuild" ] || [ "$CMD" = "--reset" ]; then
  BUILD_FLAG="--build --no-cache"
  echo -e "${YELLOW}🔄 強制重新 build...${NC}"
fi

echo -e "${CYAN}🐳 啟動容器...${NC}"
docker compose up -d $BUILD_FLAG

# ── 健康檢查 ────────────────────────────────────────────────────
health_check 30 2
verify_api

# ── 結果摘要 ────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}   🎉 排爐系統啟動成功！${NC}"
echo -e "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}後端 API${NC}     ${API_URL}"
echo -e "  ${BOLD}Swagger 文件${NC} ${API_URL}/docs"
echo -e "  ${BOLD}前端 SPA${NC}     http://localhost:${NGINX_PORT}"
echo ""
echo -e "  ${BOLD}常用指令${NC}"
echo -e "  ${CYAN}./start.sh --logs${NC}    即時日誌追蹤"
echo -e "  ${CYAN}./start.sh --status${NC}  服務狀態"
echo -e "  ${CYAN}./start.sh --stop${NC}   停止服務"
echo -e "  ${CYAN}./start.sh --rebuild${NC} 重新建置"
echo ""

# ── 日誌模式 ────────────────────────────────────────────────────
if [ "$CMD" = "--logs" ]; then
  echo -e "${CYAN}📋 即時日誌 (Ctrl+C 退出)...${NC}"
  docker compose logs -f
fi