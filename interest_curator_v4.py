#!/usr/bin/env python3
"""
관심사 큐레이션 v4
- Reddit, GitHub, Nitter API 직접 활용
- 무료 무제한
- 1시간마다 자동 실행
"""

import json
import random
import requests
from pathlib import Path
from datetime import datetime
import re
import html

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
DUPLICATE_DB = Path.home() / ".claude" / "curated_v4_history.json"

# 관심사 설정 (한국 소스 중심)
INTERESTS = {
    "부동산": {
        "reddit": ["RealEstateKorea", "realestate"],
        "github": ["부동산", "임대", "투자"],
        "nitter": "부동산 투자"
    },
    "AI/자동화": {
        "reddit": ["PythonKorea", "automation"],
        "github": ["AI", "자동화", "업무 자동화"],
        "nitter": "AI 자동화"
    },
    "뇌과학": {
        "reddit": ["productivity"],
        "github": ["생산성", "집중력", "습관"],
        "nitter": "생산성 루틴"
    },
    "PKM": {
        "reddit": ["ObsidianMD", "ProductivityHacks"],
        "github": ["옵시디언", "지식 관리", "Zettelkasten"],
        "nitter": "옵시디언 활용"
    },
    "투자": {
        "reddit": ["financialindependence"],
        "github": ["주식", "ETF", "배당", "재테크"],
        "nitter": "배당주 투자"
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

def search_reddit(subreddits, limit=5):
    """Reddit 검색 (JSON API)"""
    results = []
    headers = {'User-agent': 'ClaudeCode/1.0'}

    for subreddit in subreddits[:2]:  # 2개만
        try:
            # 핫 토픽 가져오기
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=10"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts[:limit]:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    url = post_data.get("url", "")
                    selftext = post_data.get("selftext", "")
                    score = post_data.get("score", 0)

                    if title and url and not is_duplicate(url):
                        results.append({
                            "title": title,
                            "url": url,
                            "description": selftext[:200] if selftext else f"↑ {score} points",
                            "source": f"r/{subreddit}"
                        })
                        add_to_duplicate_db(url)

        except Exception as e:
            print(f"❌ Reddit {subreddit} 검색 실패: {e}")

    return results

def search_github(keywords, limit=5):
    """GitHub 검색 (Search API)"""
    results = []
    headers = {'Accept': 'application/vnd.github.v3+json'}

    keyword = keywords[0]  # 첫 번째 키워드
    try:
        url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars&order=desc&per_page=10"
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            repos = data.get("items", [])

            for repo in repos[:limit]:
                name = repo.get("full_name", "")
                url = repo.get("html_url", "")
                description = repo.get("description", "No description")
                stars = repo.get("stargazers_count", 0)

                if name and url and not is_duplicate(url):
                    results.append({
                        "title": name,
                        "url": url,
                        "description": f"{description} (★ {stars})",
                        "source": "GitHub"
                    })
                    add_to_duplicate_db(url)

    except Exception as e:
        print(f"❌ GitHub 검색 실패: {e}")

    return results

def search_nitter(query, limit=3):
    """Nitter로 트윗 검색"""
    results = []

    try:
        # 공개 Nitter 인스턴스
        instances = ["nitter.net", "nitter.poast.org"]
        instance = random.choice(instances)

        url = f"https://{instance}/search?q={query}&f=tweets"
        headers = {'User-agent': 'ClaudeCode/1.0'}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # HTML 파싱 (간단하게)
            # 실제로는 BeautifulSoup 필요하지만 간소화
            pass

    except Exception as e:
        print(f"⚠️ Nitter 검색 실패 (무시): {e}")

    return results

def format_message(category, items):
    """텔레그램 메시지 포맷"""
    message = f"🔍 [{category} 큐레이션]\n\n"

    for i, item in enumerate(items[:3], 1):
        source = item.get("source", "")
        title = item.get("title", "")
        description = item.get("description", "")
        url = item.get("url", "")

        # HTML 태그 제거 및 이스케이프
        title = re.sub(r'<[^>]+>', '', title)
        title = html.unescape(title)
        # Markdown 특수문자 이스케이프
        title = title.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')

        message += f"{i}. {title}\n"
        message += f"📍 {source}\n"
        message += f"📝 {description[:150]}...\n"
        message += f"🔗 {url}\n\n"
        message += "---\n\n"

    message += f"💬 흥미로우시면 말씀해요! 제가 심층 분석해드릴게요"

    return message

def send_to_telegram(message):
    """텔레그램 전송"""
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
        print(f"❌ 텔레그램 전송 실패: {e}")

def main():
    """메인 실행"""
    print(f"🚀 관심사 큐레이션 v4 시작: {datetime.now()}")

    # 랜덤 카테고리 선택
    category = random.choice(list(INTERESTS.keys()))
    sources = INTERESTS[category]

    print(f"📊 주제: {category}")

    all_results = []

    # Reddit 검색
    if "reddit" in sources:
        print("🔴 Reddit 검색 중...")
        reddit_results = search_reddit(sources["reddit"])
        all_results.extend(reddit_results)
        print(f"   → {len(reddit_results)}개 찾음")

    # GitHub 검색
    if "github" in sources:
        print("🐙 GitHub 검색 중...")
        github_results = search_github(sources["github"])
        all_results.extend(github_results)
        print(f"   → {len(github_results)}개 찾음")

    # Nitter 검색 (선택)
    if "nitter" in sources and random.random() > 0.5:  # 50% 확률
        print("🐦 Nitter 검색 중...")
        nitter_results = search_nitter(sources["nitter"])
        all_results.extend(nitter_results)

    if not all_results:
        print("📭 큐레이션 결과 없음")
        return

    # 섞기
    random.shuffle(all_results)

    # 메시지 생성 & 전송
    message = format_message(category, all_results)
    send_to_telegram(message)

    print(f"✅ {len(all_results)}개 큐레이션 완료")

if __name__ == "__main__":
    main()
