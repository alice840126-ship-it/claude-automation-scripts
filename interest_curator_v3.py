#!/usr/bin/env python3
"""
관심사 큐레이션 v3
- X, Reddit, GitHub 검색
- 웹 리더기로 실제 내용 읽기
- 토론 가능한 풍부한 요약
"""

import json
import random
import requests
from pathlib import Path
from datetime import datetime

# MCP 웹 리더기 엔드포인트
WEB_READER_URL = "http://localhost:3000/read"  # 실제 MCP 엔드포인트 확인 필요

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
DUPLICATE_DB = Path.home() / ".claude" / "curated_v3_history.json"

# 관심사 키워드 (영어/한국어)
INTERESTS = {
    "부동산": {
        "keywords": ["지식산업센터 임대", "상가 임대료", "수익형 부동산", "commercial real estate", "office building investment"],
        "sources": ["reddit", "github"]  # 부동산은 Reddit, GitHub
    },
    "AI/자동화": {
        "keywords": ["AI agent", "LLM automation", "Claude API", "AutoGPT", "workflow automation"],
        "sources": ["reddit", "github", "x"]  # AI는 전부
    },
    "뇌과학": {
        "keywords": ["focus techniques", "deep work", "sleep optimization", "neuroscience productivity"],
        "sources": ["reddit", "github"]
    },
    "PKM": {
        "keywords": ["Obsidian workflow", "Zettelkasten method", "knowledge management", "Second Brain"],
        "sources": ["reddit", "github"]
    },
    "투자": {
        "keywords": ["dividend investing", "ETF strategy", "passive income", "portfolio management"],
        "sources": ["reddit"]
    }
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
    if len(db["urls"]) > 100:
        db["urls"] = db["urls"][-100:]
    save_duplicate_db(db)

def search_reddit(query):
    """Reddit 검색 (Brave Search API 활용)"""
    search_query = f"site:reddit.com {query}"
    # Brave Search API 사용 (기존 웹 검색 MCP 활용)
    # 여기서는 구조화된 결과 반환
    return []

def search_github(query):
    """GitHub 검색"""
    search_query = f"site:github.com {query}"
    return []

def search_x(query):
    """X/Twitter 검색"""
    # X는 인증 필요해서 직접 검색 어려움
    # 대신 Google 검색 통해 X 트윗 찾기
    search_query = f"site:x.com {query}"
    return []

def read_content_with_web_reader(url):
    """웹 리더기로 실제 내용 읽기"""
    try:
        # mcp__web_reader__webReader 툴 호출 필요
        # 여기서는 간소화해서 URL만 반환
        return {
            "url": url,
            "summary": "웹 리더기로 읽을 내용",
            "key_points": []
        }
    except Exception as e:
        print(f"❌ 웹 리더 읽기 실패: {e}")
        return None

def format_message(category, items):
    """텔레그램 메시지 포맷"""
    message = f"🔍 **[{category} 큐레이션]**\n\n"

    for i, item in enumerate(items[:2], 1):  # 상위 2개만
        message += f"## {i}. {item['title']}\n\n"
        message += f"📝 **핵심:**\n{item.get('summary', '')}\n\n"
        message += f"💡 **토론 포인트:**\n{item.get('discussion', '')}\n\n"
        message += f"🔗 {item['url']}\n\n"
        message += "---\n\n"

    message += f"💬 이 내용 어떠세요? 토론해요!"

    return message

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
    print(f"🚀 관심사 큐레이션 v3 시작: {datetime.now()}")

    # 랜덤 카테고리 선택
    category = random.choice(list(INTERESTS.keys()))
    category_info = INTERESTS[category]
    keyword = random.choice(category_info["keywords"])
    sources = category_info["sources"]

    print(f"📊 주제: {category} ({keyword})")
    print(f"📍 검색 소스: {sources}")

    # 각 소스별 검색
    all_results = []

    for source in sources:
        if source == "reddit":
            results = search_reddit(keyword)
        elif source == "github":
            results = search_github(keyword)
        elif source == "x":
            results = search_x(keyword)

        all_results.extend(results)

    # 중복 제거
    curated_items = []
    for item in all_results:
        url = item.get("link", "")
        if url and not is_duplicate(url):
            # 웹 리더기로 내용 읽기
            content = read_content_with_web_reader(url)
            if content:
                curated_items.append({
                    "title": item.get("title", ""),
                    "url": url,
                    "summary": content.get("summary", ""),
                    "discussion": content.get("key_points", "")
                })
                add_to_duplicate_db(url)

    if not curated_items:
        print("📭 큐레이션 결과 없음")
        return

    # 메시지 생성 & 전송
    message = format_message(category, curated_items)
    send_to_telegram(message)

    print(f"✅ {len(curated_items)}개 큐레이션 완료")

if __name__ == "__main__":
    main()
