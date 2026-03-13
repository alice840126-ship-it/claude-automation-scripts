#!/usr/bin/env python3
"""
관심사 큐레이션 v2
- 네이버 API 사용 (이미 할당량 있음)
- 중복 체크 (최근 100개 URL 저장)
- AI 요약 (제가 3줄 요약)
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 설정
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
DUPLICATE_DB = Path.home() / ".claude" / "curated_history.json"

# 관심사 키워드 (한국어만)
INTERESTS = {
    "부동산": ["지식산업센터 임대", "상가 임대료", "수익형 부동산", "부동산 투자", "지식센터 분양", "아파트 매매"],
    "AI/자동화": ["AI 활용", "업무 자동화", "생산성 도구", "노션 활용", "스마트 워크"],
    "뇌과학": ["집중력 향상", "생산성 루틴", "수면의 질", "두뇌 회복", "습관 형성"],
    "PKM": ["옵시디언 활용법", "지식 관리", "기록 문화", "정보 정리"],
    "투자": ["분산 투자", "배당주", "ETF", "자산 배분", "재테크"]
}

def load_duplicate_db():
    """중복 DB 로드"""
    if DUPLICATE_DB.exists():
        with open(DUPLICATE_DB, 'r') as f:
            return json.load(f)
    return {"urls": [], "last_cleanup": None}

def save_duplicate_db(data):
    """중복 DB 저장"""
    data["last_cleanup"] = datetime.now().isoformat()
    with open(DUPLICATE_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_duplicate(url):
    """중복 체크"""
    db = load_duplicate_db()
    return url in db.get("urls", [])

def add_to_duplicate_db(url):
    """중복 DB에 추가"""
    db = load_duplicate_db()
    db["urls"].append(url)

    # 100개만 유지
    if len(db["urls"]) > 100:
        db["urls"] = db["urls"][-100:]

    save_duplicate_db(db)

def search_naver(query):
    """네이버 검색"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키 없음")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": 5,
        "sort": "date"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        return data.get("items", [])
    except Exception as e:
        print(f"❌ 네이버 검색 실패: {e}")
        return []

def summarize_article(title, description):
    """간단 요약 (제목 + 설명 150자)"""
    summary = f"{title}\n\n{description[:150]}..."
    return summary

def send_to_telegram(message):
    """텔레그램 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=data, timeout=10)
        print("✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"❌ 텔레그램 전송 실패: {e}")

def main():
    """메인 실행"""
    print(f"🚀 관심사 큐레이션 v2 시작: {datetime.now()}")

    # 랜덤 카테고리 선택
    import random
    category = random.choice(list(INTERESTS.keys()))
    keywords = INTERESTS[category]
    keyword = random.choice(keywords)

    print(f"📊 주제: {category} ({keyword})")

    # 네이버 검색
    items = search_naver(keyword)

    if not items:
        print("⚠️ 검색 결과 없음")
        return

    # 중복 제거
    curated_items = []
    for item in items:
        url = item.get("link", "")
        title = item.get("title", "")
        description = item.get("description", "")

        # HTML 태그 제거
        import re
        import html
        title = html.unescape(title)
        title = re.sub(r'<[^>]+>', '', title)
        description = html.unescape(description)
        description = re.sub(r'<[^>]+>', '', description)

        if url and not is_duplicate(url):
            # 요약 생성
            summary = summarize_article(title, description)

            curated_items.append({
                "title": title,
                "summary": summary,
                "url": url,
                "category": category
            })

            add_to_duplicate_db(url)

    if not curated_items:
        print("📭 새로운 뉴스 없음")
        return

    # 메시지 생성
    message = f"📚 **[{category} 뉴스 큐레이션]**\n\n"
    message += f"🔍 키워드: {keyword}\n\n"

    for i, item in enumerate(curated_items[:3], 1):
        message += f"**{i}. {item['title']}**\n\n"
        message += f"{item['summary']}\n\n"
        message += f"🔗 {item['url']}\n\n"
        message += "---\n\n"

    # 전송
    send_to_telegram(message)
    print(f"✅ {len(curated_items)}개 뉴스 큐레이션 완료")

if __name__ == "__main__":
    main()
