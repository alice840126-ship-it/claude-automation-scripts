#!/usr/bin/env python3
"""
매일 저녁 11시 자동 작업 요약 시스템
1. work_log.json 읽기
2. 오늘 날짜 작업 필터링
3. 중복 제거 후 요약 생성
4. 4곳에 자동 기록
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 경로 설정
WORK_LOG = Path.home() / ".claude" / "work_log.json"
SESSION_LOG = Path.home() / ".claude" / "session_log.md"
SHARED_CONTEXT = Path.home() / ".claude-unified" / "shared_context.md"
DAILY_NOTE_DIR = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수/30. 자원 상자/01. 데일리 노트"

def read_work_log():
    """work_log.json 읽기"""
    if not WORK_LOG.exists():
        return {"current_session": []}

    with open(WORK_LOG, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_today_work(work_data, today_str):
    """오늘 날짜 작업 필터링"""
    # current_session에서 오늘 날짜 작업 필터링
    all_work = work_data.get('current_session', [])

    today_work = []
    for item in all_work:
        time_str = item.get('time', '')  # "HH:MM" 형식
        # 시간에서 ":" 제거해서 날짜와 비교
        if time_str and ':' in time_str:
            hour = int(time_str.split(':')[0])
            # 아침 6시 이후 작업만 포함 (새베 Dawn 이후)
            if hour >= 6:
                today_work.append(item)

    return today_work

def remove_duplicates(work_items):
    """중복 제거"""
    seen = set()
    unique_items = []

    for item in work_items:
        # description 기준 중복 체크
        desc = item.get('description', '')
        if desc and desc not in seen:
            seen.add(desc)
            unique_items.append(item)

    return unique_items

def generate_summary(work_items):
    """요약 생성"""
    if not work_items:
        return "오늘 작업 내역 없음"

    # 시간순 정렬
    sorted_items = sorted(work_items, key=lambda x: x.get('time', ''))

    # 카테고리별 그룹핑
    categories = {}
    for item in sorted_items:
        desc = item.get('description', '')

        # 간단한 카테고리 분류
        category = "기타"
        if "뉴스" in desc or "스크래핑" in desc:
            category = "뉴스 시스템"
        elif "CLAUDE" in desc or "수정" in desc:
            category = "시스템 정리"
        elif "분석" in desc:
            category = "분석"
        elif "테스트" in desc:
            category = "테스트"

        if category not in categories:
            categories[category] = []
        categories[category].append(desc)

    # 요약 생성
    summary_lines = [f"## 오늘 작업 요약 ({len(sorted_items)}건)\n"]

    for category, items in categories.items():
        summary_lines.append(f"\n### {category} ({len(items)}건)")
        for i, item in enumerate(items, 1):
            summary_lines.append(f"{i}. {item}")

    return '\n'.join(summary_lines)

def save_to_4_locations(summary_text, today_str):
    """4곳에 자동 기록"""

    # 1. session_log.md
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n## [{timestamp}] 매일 저녁 11시 작업 요약\n\n{summary_text}\n\n---\n"

    if SESSION_LOG.exists():
        with open(SESSION_LOG, 'a', encoding='utf-8') as f:
            f.write(entry)

    # 2. shared_context.md
    shared_entry = f"\n## {today_str} 23:00\n{summary_text}\n"

    if SHARED_CONTEXT.exists():
        with open(SHARED_CONTEXT, 'a', encoding='utf-8') as f:
            f.write(shared_entry)

    # 3. 옵시디언 데일리 노트
    daily_note_path = DAILY_NOTE_DIR / f"{today_str}.md"

    if daily_note_path.exists():
        with open(daily_note_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 작업 로그 섹션 찾기
        if "## 작업 로그" in content:
            # 작업 로그 섹션의 끝을 찾아서 추가
            # 마지막 시간대 섹션 뒤에 추가

            # 23:00 섹션이 이미 있는지 확인
            if "### 🌙 저녁 23:00 자동 요약" in content:
                return  # 이미 있으면 종료

            # 작업 로그 섹션의 마지막 부분 찾기
            lines = content.split('\n')
            insert_idx = -1

            for i in range(len(lines) - 1, -1, -1):
                # "---" 또는 파일 끝을 찾으면
                if lines[i].strip() == "---" or i == len(lines) - 1:
                    insert_idx = i
                    break

            if insert_idx > 0:
                # 요약 추가
                evening_entry = f"\n\n### 🌙 저녁 23:00 자동 요약\n{summary_text}\n"
                lines.insert(insert_idx, evening_entry)

                # 다시 합치기
                content = '\n'.join(lines)

                with open(daily_note_path, 'w', encoding='utf-8') as f:
                    f.write(content)

def main():
    """메인 함수"""
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")

    print(f"🌙 매일 저녁 11시 작업 요약 시작... ({today_str})")

    # 1. work_log.json 읽기
    work_data = read_work_log()
    print(f"  📋 work_log.json 읽기 완료")

    # 2. 오늘 날짜 작업 필터링
    today_work = filter_today_work(work_data, today_str)
    print(f"  🔍 오늘 작업 필터링: {len(today_work)}건")

    if not today_work:
        print("  ⚠️ 오늘 작업 없음, 종료")
        return

    # 3. 중복 제거
    unique_work = remove_duplicates(today_work)
    print(f"  🔄 중복 제거: {len(unique_work)}건")

    # 4. 요약 생성
    summary = generate_summary(unique_work)
    print(f"  📝 요약 생성 완료")

    # 5. 4곳에 자동 기록
    save_to_4_locations(summary, today_str)
    print(f"  ✅ 4곳 기록 완료")

    print(f"\n🎉 매일 저녁 11시 작업 요약 완료!")

if __name__ == "__main__":
    main()
