#!/usr/bin/env python3
"""
해다.io 뉴스 큐레이션 시스템
기술/비즈니스 트렌드를 자동으로 수집하고 요약
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from pathlib import Path

# 저장 경로
SAVE_DIR = Path.home() / ".claude" / "hada_news"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def fetch_hada_topics(limit=20):
    """해다.io 최신 토픽 가져오기"""

    url = "https://news.hada.io/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 토픽 추출
        topics = []
        topic_rows = soup.find_all('tr', class_='topic')

        for row in topic_rows[:limit]:
            try:
                # 링크와 제목
                link_tag = row.find('a', class_='topic_link')
                if not link_tag:
                    continue

                title = link_tag.get_text(strip=True)
                topic_url = f"https://news.hada.io/{link_tag['href']}"

                # ID 추출
                topic_id = link_tag['href'].split('id=')[1].split('&')[0] if 'id=' in link_tag['href'] else ''

                # 카테고리
                info_div = row.find('div', class_='info')
                category = info_div.find_all('a')[0].get_text(strip=True) if info_div else ''

                # 작성시간
                time_tag = info_div.find('span', class_='time') if info_div else None
                time_str = time_tag.get_text(strip=True) if time_tag else ''

                # 추천수
                vote_tag = row.find('td', class_='vote')
                vote = vote_tag.get_text(strip=True) if vote_tag else '0'

                topics.append({
                    'id': topic_id,
                    'title': title,
                    'url': topic_url,
                    'category': category,
                    'time': time_str,
                    'vote': vote
                })

            except Exception as e:
                print(f"⚠️ 토픽 파싱 에러: {e}")
                continue

        return topics

    except Exception as e:
        print(f"❌ 해다.io fetch 에러: {e}")
        return []

def filter_tech_topics(topics, keywords=None):
    """기술/비즈니스 관련 토픽 필터링"""

    if keywords is None:
        keywords = [
            'AI', '인공지능', 'Claude', 'GPT', 'ChatGPT',
            '주식', '투자', '부동산', '경제',
            'Python', '프로그래밍', '개발자',
            'MCP', '노트북', 'Notebook',
            '생산성', '자동화', '시스템',
            '스타트업', '비즈니스',
            '웹', '앱', '서비스'
        ]

    filtered = []
    for topic in topics:
        # 제목에 키워드 포함 여부 확인
        title_lower = topic['title'].lower()

        # 카테고리가 GN⁺(프리미엄)이거나 키워드 포함
        if (topic['category'] == 'GN⁺' or
            any(keyword.lower() in title_lower for keyword in keywords)):

            # 추천수 5개 이상 필터
            try:
                vote = int(topic['vote'])
                if vote >= 5:
                    filtered.append(topic)
            except:
                filtered.append(topic)

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
        summary += f"{i}. [{topic['category']}] {topic['title']}\n"
        summary += f"   👍 {topic['vote']} | 🕒 {topic['time']}\n"
        summary += f"   🔗 {topic['url']}\n\n"

    return summary

def main():
    """메인 실행"""

    print("📡 해다.io 토픽 수집 중...")

    # 1. 최신 토픽 가져오기
    all_topics = fetch_hada_topics(limit=30)

    if not all_topics:
        print("❌ 토픽을 가져오지 못했습니다.")
        return

    print(f"✅ {len(all_topics)}개 토픽 수집 완료")

    # 2. 필터링
    filtered = filter_tech_topics(all_topics)
    print(f"🎯 필터링: {len(filtered)}개 (기술/비즈니스, 추천 5+)")

    # 3. 저장
    save_path = save_topics(filtered)
    print(f"💾 저장 완료: {save_path}")

    # 4. 요약 출력
    print("\n" + format_summary(filtered))

if __name__ == "__main__":
    main()
