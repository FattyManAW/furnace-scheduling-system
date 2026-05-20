#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
#  排爐系統 — Docker 代碼新鮮度自動監控 v1.0
#  每 5 分鐘執行一次：比對 Docker health endpoint vs GitHub latest commit
#  檢測到落後 → 自動 git pull + rebuild + restart (或 alert)
#
#  用法:
#    ./auto-sync.sh              # 檢查 + 自動修復
#    ./auto-sync.sh --alert-only # 僅檢查，落後時 exit 1（供 cron alert 用）
# ═══════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

NGINX_PORT="${NGINX_PORT:-8030}"
HEALTH_URL="http://localhost:${NGINX_PORT}/health"
ALERT_ONLY=false
LOG_FILE="${SCRIPT_DIR}/auto-sync.log"

[ "${1:-}" = "--alert-only" ] && ALERT_ONLY=true

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# ── 取得 GitHub 最新 commit ──────────────────────────────────────
GITHUB_SHA=$(curl -sf "https://api.github.com/repos/FattyManAW/furnace-scheduling-system/commits/main" \
  -H "Accept: application/vnd.github.v3+json" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('sha','')[:8])" 2>/dev/null || echo "")

# Fallback: GitHub API rate limited → git ls-remote
if [ -z "$GITHUB_SHA" ]; then
  GITHUB_SHA=$(git ls-remote origin refs/heads/main 2>/dev/null | awk '{print substr($1,1,8)}' || echo "")
fi

if [ -z "$GITHUB_SHA" ]; then
  # Both GitHub API and git ls-remote failed — skip this round silently
  exit 0
fi

# ── 取得 Docker 內 commit ────────────────────────────────────────
DOCKER_RESP=$(curl -sf "$HEALTH_URL" 2>/dev/null || echo '{"status":"down"}')
DOCKER_COMMIT=$(echo "$DOCKER_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('commit','unknown'))" 2>/dev/null || echo "unknown")

# ── 比對（方向感知）────────────────────────────────────────────
if [ "$DOCKER_COMMIT" = "unknown" ] || [ "$DOCKER_COMMIT" = "offline" ]; then
  log "WARN: Docker 未回傳 commit hash (${DOCKER_COMMIT})，需要 rebuild"
  DOCKER_COMMIT="unknown"
fi

# Exact match → sync
DOCKER_SHORT=$(echo "$DOCKER_COMMIT" | cut -c1-7)
if [ "$DOCKER_SHORT" = "${GITHUB_SHA:0:7}" ] || [ "$DOCKER_COMMIT" = "${GITHUB_SHA}" ]; then
  exit 0
fi

# Direction-aware comparison: is GitHub ahead of Docker?
# git rev-list --count <DOCKER>..<GITHUB> → commits GitHub has that Docker doesn't
GITHUB_BEHIND=$(git rev-list --count "${DOCKER_COMMIT}..${GITHUB_SHA}" 2>/dev/null || echo "-1")
DOCKER_BEHIND=$(git rev-list --count "${GITHUB_SHA}..${DOCKER_COMMIT}" 2>/dev/null || echo "-1")

if [ "$GITHUB_BEHIND" = "-1" ] || [ "$DOCKER_BEHIND" = "-1" ]; then
  # Can't resolve one or both → unknown, skip
  exit 0
fi

if [ "$DOCKER_BEHIND" -gt 0 ]; then
  log "AHEAD: Docker=${DOCKER_COMMIT} ahead of GitHub=${GITHUB_SHA} by ${DOCKER_BEHIND} commit(s) — OK (local fix deployed before push)"
  exit 0
fi

if [ "$GITHUB_BEHIND" -eq 0 ] && [ "$DOCKER_BEHIND" -eq 0 ]; then
  # Equal (should have been caught above, but safety)
  exit 0
fi

# ── Docker 落後 GitHub ───────────────────────────────────────────
log "STALE: Docker=${DOCKER_COMMIT} behind GitHub=${GITHUB_SHA} by ${GITHUB_BEHIND} commit(s)"

if $ALERT_ONLY; then
  log "ALERT_ONLY mode — 需手動重建"
  exit 1
fi

# ── 自動修復 ─────────────────────────────────────────────────────
log "🔧 自動修復: git pull + npm build + docker rebuild..."

# git pull
git fetch origin 2>/dev/null
LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "$LOCAL")
if [ "$LOCAL" != "$REMOTE" ] && [ -n "$LOCAL" ]; then
  git pull --rebase origin main 2>&1 | tee -a "$LOG_FILE"
fi

# build frontend
if [ -f frontend/package.json ]; then
  log "npm install + build..."
  cd frontend && npm install --silent 2>&1 | tail -1 | tee -a "$LOG_FILE"
  npm run build 2>&1 | tail -3 | tee -a "$LOG_FILE"
  log "chmod -R 755 frontend/dist/ (fix npm 600 perms)"
  chmod -R 755 frontend/dist/
  cd "$SCRIPT_DIR"
fi

# docker rebuild
export GIT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
log "docker compose up -d --build (commit: ${GIT_COMMIT})..."
docker compose up -d --build 2>&1 | tail -5 | tee -a "$LOG_FILE"

log "✅ 自動修復完成"