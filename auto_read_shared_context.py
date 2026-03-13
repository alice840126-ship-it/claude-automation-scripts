#!/usr/bin/env python3
"""
Shared Context 자동 읽기 스크립트
아침 7시부터 저녁 9시까지 1시간에 한 번씩 실행
Claude Code가 텔레그램 봇의 작업 내역을 확인
"""

import sys
from pathlib import Path
from datetime import datetime

SHARED_CONTEXT = Path.home() / ".claude-unified" / "shared_context.md"

def read_shared_context():
    """Shared Context 읽기"""

    if not SHARED_CONTEXT.exists():
        return "❌ Shared Context 파일이 없습니다."

    with open(SHARED_CONTEXT, 'r', encoding='utf-8') as f:
        content = f.read()

    return content

def get_recent_entries(num_entries=10):
    """최근 작업 내역 추출"""

    content = read_shared_context()

    if isinstance(content, str) and content.startswith("❌"):
        return content

    lines = content.split('\n')
    recent_entries = []

    # ## YYYY-MM-DD HH:MM 형식의 타임스탬프 찾기
    for i, line in enumerate(lines):
        if line.startswith('## 2026-'):
            timestamp = line.replace('## ', '').strip()

            # 다음 줄이 내용
            if i + 1 < len(lines):
                description = lines[i + 1].strip()

                if description and not description.startswith('##'):
                    recent_entries.append({
                        'timestamp': timestamp,
                        'description': description
                    })

    # 최근 N개만 반환
    return recent_entries[-num_entries:]

def main():
    """메인 실행 함수"""

    # 현재 시간 확인 (07:00 ~ 21:00만 실행)
    now = datetime.now()
    hour = now.hour

    if hour < 7 or hour >= 21:
        # 근무 시간 외에는 조용히 종료
        sys.exit(0)

    # 최근 작업 내역 가져오기
    entries = get_recent_entries(num_entries=5)

    if not entries:
        print("📋 Shared Context에 새 작업 내역 없음")
        sys.exit(0)

    # 출력 (Claude가 볼 수 있도록)
    print("=" * 70)
    print(f"📋 Shared Context 확인 ({now.strftime('%Y-%m-%d %H:%M')})")
    print("=" * 70)
    print()

    for entry in entries:
        print(f"🕐 {entry['timestamp']}")
        print(f"   {entry['description'][:100]}")
        print()

    print("=" * 70)
    print("✅ 텔레그램 봇 작업 내역 확인 완료")
    print()

if __name__ == "__main__":
    main()
