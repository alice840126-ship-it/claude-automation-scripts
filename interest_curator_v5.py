#!/usr/bin/env python3
"""
관심사 큐레이션 v5
- 네이버 뉴스 API (한글 100%)
- GitHub 한국 저장소
- 한글만!
"""

import os
import json
import random
import requests
from pathlib import Path
from datetime import datetime
import re
import html
from dotenv import load_dotenv

load_dotenv(Path.home() / ".claude/scripts/.env")

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
DUPLICATE_DB = Path.home() / ".claude" / "curated_v5_history.json"

# 관심사 키워드 (한국어)
INTERESTS = {
    "부동산": ["지식산업센터 투자", "상가 임대료", "수익형 부동산", "부동산 분석", "임대 사업"],
    "AI/자동화": ["AI 에이전트", "업무 자동화", "생산성 도구", "노션 활용", "LLM 활용"],
    "뇌과학": ["집중력 향상", "생산성 루틴", "뇌과학 생산성", "수면의 질", "습관 형성"],
    "PKM": ["옵시디언 활용", "지식 관리", "제텔카스텐", "기록 방법", "세컨드 브레인"],
    "투자": ["배당주 투자", "ETF 분산", "자산 배분", "주식 분석", "재테크 전략"]
}

def load_duplicate_db():
    if DUPLICATE_DB.exists():
        with open(DUPLICATE_DB, 'r') as f:
            return json.load(f)
    return {"urls": []}

def save_duplicate_db(data):
    with open(DUPLICATE_DB, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_duplicate(url):
    return url in load_duplicate_db().get("urls", [])

def add_to_duplicate_db(url):
    db = load_duplicate_db()
    db["urls"].append(url)
    if len(db["urls"]) > 100:
        db["urls"] = db["urls"][-100:]
    save_duplicate_db(db)

def search_naver_news(keyword):
    """네이버 뉴스 검색 (한글 100%)"""
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키 없음")
        return []

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": keyword,
        "display": 10,
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

def search_github_korean(keyword):
    """GitHub 한국 저장소 검색"""
    results = []
    headers = {'Accept': 'application/vnd.github.v3+json'}

    try:
        url = f"https://api.github.com/search/repositories?q={keyword}+language:python&sort=stars&per_page=10"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            repos = data.get("items", [])

            for repo in repos[:5]:
                name = repo.get("full_name", "")
                url = repo.get("html_url", "")
                description = repo.get("description", "")

                # 한글 설명만 필터링
                if description and any('\u3131' <= c <= '\u3163' or '\uac00' <= c <= '\ud7a3' for c in description):
                    if not is_duplicate(url):
                        results.append({
                            "title": name,
                            "url": url,
                            "description": description,
                            "source": "GitHub"
                        })
                        add_to_duplicate_db(url)

    except Exception as e:
        print(f"⚠️ GitHub 검색 실패: {e}")

    return results

def format_message(category, items):
    message = f"🔍 [{category} 큐레이션]\n\n"

    for i, item in enumerate(items[:5], 1):
        title = item.get("title", "")
        description = item.get("description", "")
        url = item.get("url", "")
        source = item.get("source", "뉴스")

        # HTML 태그 제거
        title = re.sub(r'<[^>]+>', '', title)
        title = html.unescape(title)
        description = re.sub(r'<[^>]+>', '', description)
        description = html.unescape(description)

        message += f"{i}. {title}\n"
        message += f"📍 {source}\n"
        message += f"📝 {description[:120]}...\n"
        message += f"🔗 {url}\n\n"
        message += "---\n\n"

    message += f"💬 더 알고 싶은 거 있으세요?"

    return message

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        print("✅ 텔레그램 전송 완료")
    except Exception as e:
        print(f"❌ 전송 실패: {e}")

def main():
    print(f"🚀 관심사 큐레이션 v5 시작: {datetime.now()}")

    category = random.choice(list(INTERESTS.keys()))
    keyword = random.choice(INTERESTS[category])

    print(f"📊 주제: {category} ({keyword})")

    all_results = []

    # 네이버 뉴스
    print("📰 네이버 뉴스 검색 중...")
    news_items = search_naver_news(keyword)
    for item in news_items:
        url = item.get("link", "")
        if url and not is_duplicate(url):
            all_results.append({
                "title": item.get("title", ""),
                "url": url,
                "description": item.get("description", ""),
                "source": "뉴스"
            })
            add_to_duplicate_db(url)
    print(f"   → {len(news_items)}개 찾음")

    # GitHub 한국 저장소
    print("🐙 GitHub 한국 저장소 검색 중...")
    github_results = search_github_korean(keyword)
    all_results.extend(github_results)
    print(f"   → {len(github_results)}개 찾음")

    if not all_results:
        print("📭 결과 없음")
        return

    # 섞기
    random.shuffle(all_results)

    message = format_message(category, all_results)
    send_to_telegram(message)

    print(f"✅ {len(all_results)}개 큐레이션 완료")

if __name__ == "__main__":
    main()
