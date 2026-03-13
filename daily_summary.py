#!/usr/bin/env python3
"""
저녁 11시 자동 기록 시스템
오늘 작업한 내용을 4곳에 자동 정리:
1. work_log.json (이미 있음, 여기서 추출)
2. session_log.md
3. shared_context.md
4. 옵시디언 데일리 노트
"""

import json
from pathlib import Path
from datetime import datetime, date

# 경로 설정
WORK_LOG = Path.home() / ".claude" / "work_log.json"
SESSION_LOG = Path.home() / ".claude" / "session_log.md"
SHARED_CONTEXT = Path.home() / ".claude-unified" / "shared_context.md"
OBSIDIAN_DAILY = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수/30. 자원 상자/01. 데일리 노트"

def get_todays_work():
    """오늘 작업 로그 추출"""
    if not WORK_LOG.exists():
        return []

    with open(WORK_LOG) as f:
        data = json.load(f)

    today = date.today().strftime("%Y-%m-%d")
    logs = data.get("current_session", [])

    # 오늘 작업만 필터링
    todays = []
    for log in logs:
        if log.get("status") == "완료":
            todays.append(log)

    return todays

def create_summary(todays_work):
    """오늘 작업 요약 생성"""
    if not todays_work:
        return "오늘 완료된 작업이 없습니다."

    summary_lines = [f"## {date.today().strftime('%Y년 %m월 %d일')} 작업 요약\n"]
    summary_lines.append(f"총 {len(todays_work)}개 작업 완료\n")

    # 중복 제거 (description 기준)
    seen = set()
    unique_work = []
    for work in todays_work:
        desc = work.get("description", "")
        if desc not in seen:
            seen.add(desc)
            unique_work.append(work)

    for i, work in enumerate(unique_work, 1):
        time_str = work.get("time", "")
        desc = work.get("description", "")
        summary_lines.append(f"{i}. **{time_str}**: {desc}")

    return "\n".join(summary_lines)

def append_to_session_log(summary):
    """세션 로그에 추가"""
    with open(SESSION_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n\n{summary}\n")
    print("✅ session_log.md에 기록 완료")

def append_to_shared_context(summary):
    """공유 컨텍스트에 추가"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n## {timestamp}\n{summary}\n"

    with open(SHARED_CONTEXT, "a", encoding="utf-8") as f:
        f.write(entry)
    print("✅ shared_context.md에 기록 완료")

def append_to_obsidian(summary):
    """옵시디언 데일리 노트에 추가"""
    today_file = OBSIDIAN_DAILY / f"{date.today().strftime('%Y-%m-%d')}.md"

    # 오늘 날짜 파일이 없으면 생성
    if not today_file.exists():
        today_file.write_text(f"# {date.today().strftime('%Y-%m-%d')}\n\n", encoding="utf-8")

    # 추가
    with open(today_file, "a", encoding="utf-8") as f:
        f.write(f"\n{summary}\n")
    print(f"✅ 옵시디언 데일리 노트에 기록 완료: {today_file.name}")

def main():
    """메인 실행"""
    print(f"🌙 저녁 11시 자동 기록 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    # 1. 오늘 작업 추출
    todays_work = get_todays_work()
    print(f"📋 오늘 작업 {len(todays_work)}개 발견")

    if not todays_work:
        print("기록할 작업이 없습니다.")
        return

    # 2. 요약 생성
    summary = create_summary(todays_work)

    # 3. 4곳에 기록
    print("\n기록 시작...")
    append_to_session_log(summary)
    append_to_shared_context(summary)
    append_to_obsidian(summary)
    print("\n✅ 모든 기록 완료")

if __name__ == "__main__":
    main()
