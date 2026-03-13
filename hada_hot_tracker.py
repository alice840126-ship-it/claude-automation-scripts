#!/usr/bin/env python3
"""
해다.io 핫 토픽 트래커
추천수가 급상승하거나 특정 키워드 포함 글 감지
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import subprocess

# 저장 경로
SAVE_DIR = Path.home() / ".claude" / "hada_tracker"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

STATE_FILE = SAVE_DIR / "seen_topics.json"

# 관심 키워드
KEYWORDS = [
    'AI', '인공지능', 'Claude', 'GPT', 'ChatGPT',
    '주식', '투자', '부동산', '경제',
    'Python', '프로그래밍', '개발자',
    'MCP', '노트북', '생산성', '자동화',
    '스타트업', '비즈니스', '클라우드'
]

def load_seen_topics():
    """이미 확인한 토픽 로드"""

    if not STATE_FILE.exists():
        return set()

    try:
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return set(data.get('seen_ids', []))
    except:
        return set()

def save_seen_topics(seen_ids):
    """확인한 토픽 저장"""

    data = {
        'last_update': datetime.now().isoformat(),
        'seen_ids': list(seen_ids)
    }

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def check_hada_via_notebooklm():
    """
    NotebookLM을 통해 해다.io 확인
    (사용자가 직접 큐레이팅한 기사를 체크)
    """

    # NotebookLM 노트북 확인
    try:
        result = subprocess.run(
            ['python3', '-m', 'notebooklm', 'source', 'list', '--json'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            sources = json.loads(result.stdout)
            hada_sources = [
                s for s in sources.get('sources', [])
                if 'hada.io' in s.get('title', '').lower() or 'hada.io' in s.get('url', '')
            ]
            return hada_sources

    except Exception as e:
        print(f"⚠️ NotebookLM 확인 실패: {e}")

    return []

def format_hot_alert(hot_topics):
    """핫 토픽 알림 포맷팅"""

    if not hot_topics:
        return None

    alert = "🔥 해다.io 핫 토픽 알림\n"
    alert += "=" * 60 + "\n\n"

    for topic in hot_topics:
        alert += f"📰 {topic['title']}\n"
        alert += f"   👍 추천: {topic.get('vote', 'N/A')} | 🕒 {topic.get('time', 'N/A')}\n"
        alert += f"   🔗 {topic.get('url', '')}\n\n"

    return alert

def manual_check_prompt():
    """사용자에게 수동 확인 요청"""

    return """
💡 해다.io 확인 제안:

1. 브라우저에서 https://news.hada.io 접속
2. 추천수 높은 글(10+) 확인
3. 흥미있는 글을 NotebookLM에 추가:
   notebooklm source add "https://news.hada.io/topic?id=XXXXX"
4. "동기화"로 텔레그램 봇과 공유

또는 "해다.io 핫 토픽 요약해"라고 말씀하세요!
"""

def main():
    """메인 실행"""

    print("🔍 해다.io 핫 토픽 체크...")

    # 1. NotebookLM에서 해다.io 소스 확인
    hada_sources = check_hada_via_notebooklm()

    if hada_sources:
        print(f"✅ NotebookLM에서 {len(hada_sources)}개 해다.io 소스 발견")

        # 최근 소스가 있는지 확인 (24시간 이내)
        now = datetime.now()
        recent = []

        for source in hada_sources:
            created_str = source.get('created', '')
            if created_str:
                try:
                    created = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                    if (now - created) < timedelta(hours=24):
                        recent.append(source)
                except:
                    pass

        if recent:
            print(f"🔥 최근 24시간 내 {len(recent)}개 새 소스!")
            print("\n최근 해다.io 기사:")
            for source in recent[:5]:
                print(f"  - {source.get('title', 'N/A')}")
        else:
            print("📊 최근 24시간 내 새 소스 없음")

    else:
        print("📭 NotebookLM에 해다.io 소스 없음")

    # 2. 수동 확인 제안
    print(manual_check_prompt())

if __name__ == "__main__":
    main()
