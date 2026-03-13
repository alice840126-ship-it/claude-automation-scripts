#!/bin/bash
# osascript로 터미널 열어서 실행 (권한 문제 회피)

/usr/bin/osascript << 'EOF'
tell application "Terminal"
    activate
    do script "python3 ~/.claude/scripts/daily_message_summary.py; exit"
end tell
EOF

# 이 방식은 터미널이 열리면서 실행됨 (사용자 세션 권한 사용)
