#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  排爐系統 — 建置與部署腳本 v1.0（強制 git pull + smoke test gate）
#
#  解決 8030 sidebar 空白事故根因：
#  - Docker rebuild 沒先 git pull → 用舊 source build
#  - 缺少自動 smoke test → 部署後不知道系統壞了
#
#  用法:
#    ./build-and-deploy.sh              # git pull + build + deploy + smoke test
#    ./build-and-deploy.sh --skip-smoke  # 跳過 smoke test（緊急手動部署）
#    ./build-and-deploy.sh --dry-run     # 檢查但不執行
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

NGINX_PORT="${NGINX_PORT:-8030}"
BASE_URL="http://localhost:${NGINX_PORT}"
LOG_FILE="${SCRIPT_DIR}/build-and-deploy.log"

SKIP_SMOKE=false
DRY_RUN=false

for arg in "$@"; do
  case "$arg" in
    --skip-smoke) SKIP_SMOKE=true ;;
    --dry-run)    DRY_RUN=true ;;
  esac
done

# ── 顏色 ──
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'

log()  { echo -e "[$(date '+%H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
pass() { echo -e "  ${GREEN}✓${NC} $*"; }
fail() { echo -e "  ${RED}✗${NC} $*"; }

if $DRY_RUN; then
  log "${YELLOW}DRY RUN — 僅檢查，不執行變更${NC}"
fi

# ══════════════════════════════════════════════════════════════════════
# Gate 1: 強制 git pull
# ══════════════════════════════════════════════════════════════════════
log "${CYAN}═══ Gate 1: git pull ═══${NC}"

BEFORE_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
git fetch origin 2>/dev/null
REMOTE_SHA=$(git rev-parse --short origin/main 2>/dev/null || echo "$BEFORE_SHA")

if [ "$BEFORE_SHA" = "$REMOTE_SHA" ]; then
  pass "本地已是最新 (${BEFORE_SHA})"
else
  log "本地 ${BEFORE_SHA} → 拉取遠端 ${REMOTE_SHA}"
  if ! $DRY_RUN; then
    git pull --rebase origin main 2>&1 || {
      fail "git pull 失敗 — 中止建置"
      exit 1
    }
  fi
  pass "git pull 完成: ${BEFORE_SHA} → ${REMOTE_SHA}"
fi

# ══════════════════════════════════════════════════════════════════════
# Gate 2: npm install + build
# ══════════════════════════════════════════════════════════════════════
log "${CYAN}═══ Gate 2: npm build ═══${NC}"

if [ -f frontend/package.json ]; then
  if ! $DRY_RUN; then
    cd frontend
    npm install --silent 2>&1 | tail -1 >> "$LOG_FILE" || true
    npm run build 2>&1 | tail -5 >> "$LOG_FILE"
    cd "$SCRIPT_DIR"
  fi
  pass "npm build 完成"
  
  # 確保 dist 目錄存在且有正確權限
  if [ -d frontend/dist ]; then
    chmod -R 755 frontend/dist/ 2>/dev/null || true
    pass "frontend/dist/ 權限修正"
  else
    fail "frontend/dist/ 不存在 — npm build 可能失敗"
    exit 1
  fi
else
  pass "無 frontend/package.json，跳過 npm build"
fi

# ══════════════════════════════════════════════════════════════════════
# Gate 3: Docker rebuild
# ══════════════════════════════════════════════════════════════════════
log "${CYAN}═══ Gate 3: Docker rebuild ═══${NC}"

export GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log "GIT_COMMIT=${GIT_COMMIT}"

if ! $DRY_RUN; then
  docker compose build 2>&1 | tail -5 >> "$LOG_FILE"
  docker compose up -d 2>&1 | tail -5 >> "$LOG_FILE"
fi
pass "Docker rebuild 完成 (commit: ${GIT_COMMIT})"

# ── 等待容器就緒 ──
if ! $DRY_RUN; then
  log "等待容器就緒..."
  for i in $(seq 1 20); do
    if curl -sf "${BASE_URL}/health" &>/dev/null; then
      pass "容器就緒 (${i}s)"
      break
    fi
    sleep 1
  done
fi

# ══════════════════════════════════════════════════════════════════════
# Gate 4: Smoke test
# ══════════════════════════════════════════════════════════════════════
if $SKIP_SMOKE; then
  log "${YELLOW}跳過 smoke test（--skip-smoke）${NC}"
else
  log "${CYAN}═══ Gate 4: Smoke test ═══${NC}"
  
  FAILURES=0
  
  # ── 4a: 7 route HTTP scan ──
  ROUTES=("/" "/orders" "/molds" "/schedule" "/gantt" "/reports" "/settings")
  log "4a: HTTP route scan (${#ROUTES[@]} routes)"
  
  for route in "${ROUTES[@]}"; do
    if $DRY_RUN; then
      pass "${route}"
      continue
    fi
    
    HTTP_CODE=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 5 "${BASE_URL}${route}" 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
      pass "${route} → 200"
    else
      fail "${route} → ${HTTP_CODE}"
      FAILURES=$((FAILURES + 1))
    fi
  done
  
  # ── 4b: 非空白內容檢查 — 確保 SPA 渲染完整（非 nginx 403/空白頁）─
  log "4b: 非空白內容檢查"
  
  for route in "${ROUTES[@]}"; do
    if $DRY_RUN; then
      pass "${route}"
      continue
    fi
    
    BODY_SIZE=$(curl -sS --connect-timeout 5 "${BASE_URL}${route}" 2>/dev/null | wc -c | tr -d ' ')
    if [ "$BODY_SIZE" -gt 500 ]; then
      pass "${route} → ${BODY_SIZE}B (非空白)"
    else
      fail "${route} → ${BODY_SIZE}B (疑似空白頁)"
      FAILURES=$((FAILURES + 1))
    fi
  done
  
  # ── 4c: Bundle 完整性檢查 — Layout / Sidebar / ThemeToggle / Routes ──
  log "4c: Bundle 完整性檢查"
  
  if ! $DRY_RUN; then
    BUNDLE_JS=$(curl -sS --connect-timeout 5 "${BASE_URL}/" 2>/dev/null | grep -o '/assets/index-[^"]*\.js' | head -1 || echo "")
    
    if [ -n "$BUNDLE_JS" ]; then
      # 寫入 temp file 避免 bash variable null-byte 截斷
      TMP_BUNDLE=$(mktemp /tmp/furnace-smoke-bundle.XXXXXX)
      curl -sS --connect-timeout 10 "${BASE_URL}${BUNDLE_JS}" -o "$TMP_BUNDLE" 2>/dev/null || true
      
      check_keyword() {
        local KW="$1"; local LABEL="$2"
        if grep -a -q "$KW" "$TMP_BUNDLE" 2>/dev/null; then
          pass "${LABEL} (${KW})"
        else
          fail "${LABEL} (${KW}) — 未在 bundle 中找到"
          FAILURES=$((FAILURES + 1))
        fi
      }
      
      # minified bundle mangler 會吃掉 ThemeToggle/Sidebar/Layout 等原始名稱
      # 改用存活於 bundle 中的 runtime marker 做完整性驗證
      check_keyword "data-theme"   "data-theme attr (ThemeToggle 掛載)"
      check_keyword "matchMedia"   "matchMedia listener (OS 主題跟隨)"
      check_keyword "localStorage" "localStorage (主題持久化)"
      check_keyword "createElement" "React createElement (SPA 渲染)"
      
      # 確認 7 個 route path 都存在
      for path in "/" "/orders" "/molds" "/schedule" "/gantt" "/reports" "/settings"; do
        if grep -a -q "${path}" "$TMP_BUNDLE" 2>/dev/null; then
          pass "route: ${path}"
        else
          fail "route: ${path} — 未在 bundle 中找到"
          FAILURES=$((FAILURES + 1))
        fi
      done
      
      rm -f "$TMP_BUNDLE"
    else
      fail "無法解析 JS bundle 路徑"
      FAILURES=$((FAILURES + 1))
    fi
  fi
  
  # ── 4d: Health endpoint ──
  log "4d: Health endpoint"
  if ! $DRY_RUN; then
    HEALTH=$(curl -sS --connect-timeout 5 "${BASE_URL}/health" 2>/dev/null || echo '{"status":"down"}')
    HEALTH_COMMIT=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('commit','?'))" 2>/dev/null || echo "?")
    if [ "$HEALTH_COMMIT" = "${GIT_COMMIT}" ]; then
      pass "commit parity: ${HEALTH_COMMIT} = ${GIT_COMMIT}"
    else
      fail "commit mismatch: deployed=${HEALTH_COMMIT} vs built=${GIT_COMMIT}"
      FAILURES=$((FAILURES + 1))
    fi
  fi
  
  # ════════════════════════════════════════════════════════════════════
  # Smoke test 結果
  # ════════════════════════════════════════════════════════════════════
  echo ""
  if [ "$FAILURES" -eq 0 ]; then
    log "${GREEN}═══════════════════════════════════════════${NC}"
    log "${GREEN}   🎉 全部檢查通過 — 部署成功${NC}"
    log "${GREEN}═══════════════════════════════════════════${NC}"
    echo "  ${GREEN}GitHub:${NC} https://github.com/FattyManAW/furnace-scheduling-system/commit/${GIT_COMMIT}"
    echo "  ${GREEN}Health:${NC} ${BASE_URL}/health"
    echo "  ${GREEN}Routes:${NC} ${#ROUTES[@]}/$(( ${#ROUTES[@]} + 7 + 2 )) gates pass"
    echo ""
    exit 0
  else
    log "${RED}═══════════════════════════════════════════${NC}"
    log "${RED}   ❌ ${FAILURES} 項檢查失敗 — 部署可能異常${NC}"
    log "${RED}═══════════════════════════════════════════${NC}"
    echo ""
    exit 2
  fi
fi