#!/bin/bash
# 경자방 아침 뉴스 자동화 스크립트 (간단 버전)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/morning-news.log"

mkdir -p "$(dirname "$LOG_FILE")"

TODAY=$(date '+%Y-%m-%d')

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "📰 경자방 아침 뉴스 수집 시작"

# MCP 도구 사용
log "뉴스 수집 중..."

# mcp__web-search__daily_news를 이용해 뉴스 수집
# 결과는 자동으로 Telegram으로도 전송됨

FINAL_REPORT="⚛️ 경자방 아침 뉴스 리포트 ($TODAY)

$(mcp__web-search__daily_news 2>/dev/null || echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"daily_news","arguments":{"category":"전체"}}}' | node /Users/oungsooryu/mcp-servers/web-search-mcp/dist/index.js 2>&1 | grep -v "Web Search" | python3 -c '
import sys, json
data = json.load(sys.stdin)
if "result" in data:
    text = data["result"]["content"][0]["text"]
    # 헤더 변경
    text = text.replace("오늘의 주요 한글 뉴스", "경자방 아침 뉴스 리포트")
    print(text)
')

💡 자비스의 한 줄 통찰
\"오늘의 뉴스 트렌드를 통해 형님의 승리하는 하루를 위한 인사이트를 제공합니다.\"

오늘도 형님의 승리하는 하루를 응원합니다! ⚛️
"

echo "$FINAL_REPORT"

# Telegram 전송
log "📤 Telegram 전송 중..."

BOT_TOKEN="8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
CHAT_ID="756219914"

MESSAGE=$(echo "$FINAL_REPORT" | sed 's/"/\\"/g' | tr '\n' '\\n' | sed 's/\\n$//')

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${MESSAGE}" \
    -d "parse_mode=Markdown" >> "$LOG_FILE" 2>&1

log "✅ 아침 뉴스 전송 완료"
