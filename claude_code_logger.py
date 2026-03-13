#!/usr/bin/env python3
"""
클로드 코드 작업 로그 기록 스크립트
작업 완료 후 실행하여 CLAUDE.md에 작업 요약 업데이트
"""

import os
import datetime
import json
from pathlib import Path

# 설정
CLAUDE_MD = "/Users/oungsooryu/CLAUDE.md"
WORK_LOG_FILE = "/Users/oungsooryu/.claude/work_log.json"
SESSION_LOG_FILE = "/Users/oungsooryu/.claude/session_log.md"

def add_work_entry(description: str, status: str = "진행중"):
    """작업 항목 추가"""
    work_data = {"current_session": [], "last_update": None}

    if os.path.exists(WORK_LOG_FILE):
        with open(WORK_LOG_FILE, 'r', encoding='utf-8') as f:
            work_data = json.load(f)

    now = datetime.datetime.now()
    entry = {
        "time": now.strftime("%H:%M"),
        "description": description,
        "status": status
    }

    work_data["current_session"].append(entry)
    work_data["last_update"] = now.isoformat()

    os.makedirs(os.path.dirname(WORK_LOG_FILE), exist_ok=True)
    with open(WORK_LOG_FILE, 'w', encoding='utf-8') as f:
        json.dump(work_data, f, ensure_ascii=False, indent=2)

    print(f"📝 작업 로그 추가: {description}")

def update_claude_md_with_session(summary: str):
    """CLAUDE.md에 세션 작업 요약 업데이트"""
    if not os.path.exists(CLAUDE_MD):
        print("⚠️ CLAUDE.md 파일 없음")
        return False

    # 현재 내용 읽기
    with open(CLAUDE_MD, 'r', encoding='utf-8') as f:
        content = f.read()

    # 작업 로그 섹션 찾기
    log_section = "## 최근 작업 로그"
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

    new_entry = f"\n### [{timestamp}] {summary}\n"

    if log_section in content:
        # 섹션 뒤에 추가
        parts = content.split(log_section)
        if len(parts) == 2:
            before = parts[0] + log_section
            after = parts[1]
            content = before + new_entry + after
    else:
        # 섹션이 없으면 추가
        content += f"\n{log_section}\n{new_entry}\n"

    # 파일 저장
    with open(CLAUDE_MD, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ CLAUDE.md 업데이트 완료")
    return True

def log_to_session_file(title: str, details: str):
    """별도 세션 로그 파일에 기록"""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    entry = f"\n## [{timestamp}] {title}\n\n{details}\n\n---\n"

    os.makedirs(os.path.dirname(SESSION_LOG_FILE), exist_ok=True)
    with open(SESSION_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(entry)

    print(f"📋 세션 로그 파일에 기록 완료")

# CLI 인터페이스
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법:")
        print("  python claude_code_logger.py add '작업 설명' [상태]")
        print("  python claude_code_logger.py summary '작업 요약'")
        print("  python claude_code_logger.py session '제목' '상세 내용'")
        sys.exit(1)

    command = sys.argv[1]

    if command == "add" and len(sys.argv) >= 3:
        desc = sys.argv[2]
        status = sys.argv[3] if len(sys.argv) >= 4 else "진행중"
        add_work_entry(desc, status)

    elif command == "summary" and len(sys.argv) >= 3:
        summary = sys.argv[2]
        update_claude_md_with_session(summary)

    elif command == "session" and len(sys.argv) >= 4:
        title = sys.argv[2]
        details = sys.argv[3]
        log_to_session_file(title, details)

    else:
        print("❌ 잘못된 명령")
        sys.exit(1)
