#!/usr/bin/env python3
"""
자동 활동 로거
- Claude Code 사용 내역을 자동으로 수집
- 옵시디언 데일리 노트에 기록
"""

import os
import datetime
import subprocess
from pathlib import Path

DAILY_NOTE_DIR = "/Users/oungsooryu/Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수/30. 자원 상자/01. 데일리 노트"

def get_claude_activity() -> list:
    """Claude 활동 내역 수집"""
    activities = []

    # 1. 로그 파일 확인
    log_dir = "/Users/oungsooryu/.claude/logs"
    if os.path.exists(log_dir):
        for log_file in os.listdir(log_dir):
            if log_file.endswith('.log'):
                try:
                    full_path = os.path.join(log_dir, log_file)
                    # 파일 수정 시간 확인 (최근 1시간)
                    mtime = os.path.getmtime(full_path)
                    if (datetime.datetime.now().timestamp() - mtime) < 3600:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()[-10:]  # 최근 10줄
                        for line in lines:
                            if line.strip():
                                activities.append(f"📋 {log_file}: {line.strip()[:100]}")
                except:
                    pass

    # 2. 쉘 히스토리 확인 (Claude 관련 명령)
    try:
        result = subprocess.run(
            ['tail', '-20', os.path.expanduser('~/.zsh_history')],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if any(cmd in line for cmd in ['python3', 'claude', 'cokacdir', 'launchctl']):
                    activities.append(f"💻 {line[:80]}")
    except:
        pass

    return activities

def update_daily_note():
    """데일리 노트 업데이트"""
    now = datetime.datetime.now()
    date_str = now.strftime('%Y-%m-%d')
    filename = f"{date_str}.md"
    filepath = os.path.join(DAILY_NOTE_DIR, filename)

    # 활동 수집
    activities = get_claude_activity()

    if not activities:
        print("📭 활동 내역 없음")
        return

    # 데일리 노트 확인
    if not os.path.exists(filepath):
        print(f"⚠️ 데일리 노트 없음: {filename}")
        return

    # 노트 읽기
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 작업 로그 섹션 확인
    marker = "## 작업 로그"
    if marker not in content:
        # 섹션 추가
        content = content + f"\n\n## 작업 로그\n\n---\n\n## 아이디어 & 노트"

    # 시간대 생성
    hour = now.hour
    time_range = f"{hour:02d}:00~{hour+1:02d}:00"

    # 로그 엔트리 생성
    log_entry = f"\n### ⚛️ {time_range} 시스템 작업 내역\n"
    for activity in activities[:5]:  # 최대 5개
        log_entry += f"- {activity}\n"

    # 작업 로그 섹션 뒤에 추가
    parts = content.split(marker)
    if len(parts) == 2:
        before = parts[0]
        after = parts[1]

        # 다음 섹션 찾기
        next_section = None
        for possible in ["## 아이디어 & 노트", "## 아이디어", "## 회고"]:
            if possible in after:
                next_section = possible
                break

        if next_section:
            after_parts = after.split(next_section)
            if len(after_parts) == 2:
                middle = after_parts[0]
                end = after_parts[1]
                updated_content = before + marker + middle + log_entry + "\n---\n\n" + next_section + end

                # 저장
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(updated_content)

                print(f"✅ 데일리 노트 업데이트 완료: {filename}")
                print(f"   {len(activities)}개 활동 기록")
                return

    print("⚠️ 데일리 노트 업데이트 실패")

def main():
    now = datetime.datetime.now()
    hour = now.hour

    # 07:00~23:00만 실행
    if hour < 7 or hour >= 23:
        print(f"⏰ 작업 로그 시간 아님: {hour:02d}:00")
        return 0

    print(f"📝 자동 활동 로깅 시작: {now}")
    update_daily_note()

if __name__ == "__main__":
    main()
