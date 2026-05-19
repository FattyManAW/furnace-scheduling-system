#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  干式套管最佳化排爐系統 — 一鍵啟動腳本
#  適用: macOS / Linux（需安裝 Docker）
#  用法: chmod +x start.sh && ./start.sh
# ─────────────────────────────────────────────────────────────────
set -euo pipefail

BOLD=$(tput bold 2>/dev/null || echo "")
GREEN=$(tput setaf 2 2>/dev/null || echo "")
CYAN=$(tput setaf 6 2>/dev/null || echo "")
YELLOW=$(tput setaf 3 2>/dev/null || echo "")
RESET=$(tput sgr0 2>/dev/null || echo "")
NC="$RESET"

REPO_URL="https://github.com/FattyManAW/furnace-scheduling-system.git"
REPO_DIR="furnace-scheduling-system"
FRONTEND_URL="https://fattymanaw.github.io/furnace-scheduling-system/"

echo "${BOLD}${CYAN}╔══════════════════════════════════════════════╗${NC}"
echo "${BOLD}${CYAN}║   干式套管最佳化排爐系統 — 一鍵啟動器     ║${NC}"
echo "${BOLD}${CYAN}╚══════════════════════════════════════════════╝${NC}"
echo ""

# ── 0) 檢查 Docker ──────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "${YELLOW}❌ 未安裝 Docker。請先安裝：https://docs.docker.com/get-docker/${NC}"
  exit 1
fi
echo "${GREEN}✅ Docker 已就緒${NC}"

# ── 1) Clone / 更新 Repo ─────────────────────────────────
if [ -d "$REPO_DIR/.git" ]; then
  echo "📦 目錄已存在，更新中..."
  cd "$REPO_DIR" && git pull --ff-only 2>/dev/null || true
else
  echo "📦 下載專案..."
  git clone "$REPO_URL" "$REPO_DIR"
  cd "$REPO_DIR"
fi
echo "${GREEN}✅ 原始碼已就緒${NC}"

# ── 2) 設定 ALLOWED_ORIGINS ───────────────────────────────
if [ ! -f .env ]; then
  cat > .env <<'EOF'
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,https://fattymanaw.github.io,http://100.107.36.80:8002
PORT=8002
TZ=Asia/Taipei
EOF
  echo "${GREEN}✅ .env 已建立${NC}"
fi

# ── 3) 關閉舊容器（如有）────────────────────────────────
docker compose down 2>/dev/null || true

# ── 4) 啟動 ──────────────────────────────────────────────
echo "🐳 建置並啟動容器..."
docker compose up -d --build
echo ""

# ── 5) 等待健康檢查 ─────────────────────────────────────
echo "⏳ 等待服務啟動..."
for i in $(seq 1 20); do
  if curl -sf "http://localhost:8002/health" &>/dev/null; then
    break
  fi
  sleep 1
done

# ── 6) 印出結果 ──────────────────────────────────────────
IP="<本機 IP>"
if command -v ifconfig &>/dev/null; then
  IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
fi

echo ""
echo "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo "${BOLD}${GREEN}   🎉 排爐系統啟動成功！${NC}"
echo "${BOLD}${GREEN}═══════════════════════════════════════════${NC}"
echo ""
echo "  ${BOLD}後端 API${NC}       http://localhost:8002"
echo "  ${BOLD}Swagger 文件${NC}   http://localhost:8002/docs"
echo "  ${BOLD}前端 SPA${NC}       ${FRONTEND_URL}"
echo "  ${BOLD}API 文件${NC}       ${FRONTEND_URL} (已串接後端)"
echo ""
echo "  ${BOLD}${CYAN}💡 前端已自動串接到後端 API，打開網頁即可使用${NC}"
echo ""

# 健康檢查結果
if curl -sf "http://localhost:8002/health" &>/dev/null; then
  echo "${GREEN}✅ 健康檢查通過${NC}"
  curl -s "http://localhost:8002/api/v1/orders/count" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'   訂單數: {d[\"count\"]}')" 2>/dev/null || true
else
  echo "${YELLOW}⚠️  服務尚未就緒，查看 docker compose logs${NC}"
fi
echo ""
echo "  停止: docker compose down"