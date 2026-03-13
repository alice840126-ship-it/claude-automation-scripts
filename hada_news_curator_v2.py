#!/usr/bin/env python3
"""
해다.io 뉴스 큐레이션 시스템 (RSS 버전)
RSS 피드를 통해 기술/비즈니스 트렌드 수집
"""

import feedparser
from datetime import datetime
import json
from pathlib import Path

# 저장 경로
SAVE_DIR = Path.home() / ".claude" / "hada_news"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_hada_rss():
    """해다.io RSS 피드 가져오기"""

    # RSS URL (여러 시도)
    rss_urls = [
        "https://news.hada.io/rss",
        "https://hada.io/rss",
        "https://news.hada.io/rss.xml",
    ]

    for rss_url in rss_urls:
        try:
            print(f"📡 시도: {rss_url}")
            feed = feedparser.parse(rss_url)

            if feed.entries:
                print(f"✅ 성공: {len(feed.entries)}개 항목")
                return feed

        except Exception as e:
            print(f"⚠️ 실패: {e}")
            continue

    return None

def filter_tech_topics(feed, keywords=None):
    """기술/비즈니스 관련 토픽 필터링"""

    if keywords is None:
        keywords = [
            'AI', '인공지능', 'Claude', 'GPT', 'ChatGPT',
            '주식', '투자', '부동산', '경제',
            'Python', '프로그래밍', '개발자',
            'MCP', '노트북', 'Notebook',
            '생산성', '자동화', '시스템',
            '스타트업', '비즈니스',
            '웹', '앱', '서비스',
            '클라우드', 'AWS', 'Azure',
            '데이터', '분석', '모델'
        ]

    filtered = []

    for entry in feed.entries:
        # 제목에 키워드 포함 여부 확인
        title = entry.get('title', '')
        title_lower = title.lower()

        # 키워드 포함 확인
        if any(keyword.lower() in title_lower for keyword in keywords):
            filtered.append({
                'title': title,
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', '')[:200]
            })

    return filtered

def save_topics(topics):
    """토픽 저장"""

    today = datetime.now().strftime("%Y-%m-%d")
    save_path = SAVE_DIR / f"{today}.json"

    data = {
        'date': today,
        'count': len(topics),
        'topics': topics
    }

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return save_path

def format_summary(topics):
    """요약 포맷팅"""

    if not topics:
        return "📰 해다.io 신규 토픽 없음"

    summary = "📰 해다.io 기술/비즈니스 토픽\n"
    summary += "=" * 60 + "\n\n"

    for i, topic in enumerate(topics, 1):
        summary += f"{i}. {topic['title']}\n"
        summary += f"   🕒 {topic['published']}\n"
        summary += f"   🔗 {topic['link']}\n\n"

    return summary

def main():
    """메인 실행"""

    print("📡 해다.io RSS 수집 중...")

    # 1. RSS 피드 가져오기
    feed = fetch_hada_rss()

    if not feed or not feed.entries:
        print("❌ RSS 피드를 가져오지 못했습니다.")
        print("💡 해다.io는 RSS 접근을 제한할 수 있습니다.")
        print("💡 대안: 브라우저 자동화(Playwright) 또는 수동 큐레이션")
        return

    print(f"✅ {len(feed.entries)}개 항목 수집 완료")

    # 2. 필터링
    filtered = filter_tech_topics(feed)
    print(f"🎯 필터링: {len(filtered)}개 (기술/비즈니스)")

    # 3. 저장
    save_path = save_topics(filtered)
    print(f"💾 저장 완료: {save_path}")

    # 4. 요약 출력
    print("\n" + format_summary(filtered))

if __name__ == "__main__":
    main()
