#!/usr/bin/env python3
"""
관심사 심층 분석 v8
- 네이버 웹문서 검색 (webkr)
- 상위 5개 본문 깊게 읽기 (trafilatura)
- 종합 인사이트 리포트 텔레그램 전송
- 2시간마다 실행
"""

import json
import random
import requests
from pathlib import Path
from datetime import datetime
import re
import html
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
DUPLICATE_DB = Path.home() / ".claude" / "curated_v6_history.json"
LOG_FILE = Path.home() / ".claude" / "logs" / "interest-curation.log"

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

# Web Reader (trafilatura로 본문 추출)
def read_web_content(url, timeout=15):
    """웹페이지 본문 읽기 (trafilatura 사용)"""
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)

        if downloaded:
            content = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if content:
                return content[:2000]  # 최대 2000자

    except Exception as e:
        log(f"⚠️ 웹페이지 읽기 실패: {e}")

    return None

def log(message):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg.strip())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg)

# 관심사 설정 (영역 확장)
INTERESTS = {
    "부동산": {
        "webkr": ["부동산 투자", "지식산업센터 임대", "상가 임대", "부동산 수익형", "부동산 투자 방법"],
        "reddit": ["RealEstateKorea", "realestate", "landlord", "RealEstate", "commercialrealestate"],
        "github": ["부동산", "임대", "투자", "real estate", "investment", "property"],
        "x": "부동산 투자"
    },
    "AI/자동화": {
        "webkr": ["AI 자동화", "업무 자동화 도구", "LLM 활용", "AI 에이전트", "생산성 AI"],
        "reddit": ["PythonKorea", "Python", "automation", "ArtificialIntelligence", "OpenAI", "ChatGPT"],
        "github": ["AI", "자동화", "업무 자동화", "LLM", "automation", "agent", "workflow"],
        "x": "AI 자동화"
    },
    "뇌과학": {
        "webkr": ["생산성 향상", "집중력 높이는 법", "두뇌 과학", "수면과 효율", "인지 능력"],
        "reddit": ["productivity", "getdisciplined", "Habits", "selfimprovement", "DecidingToBeBetter"],
        "github": ["생산성", "집중력", "productivity", "focus", "habits", "routine"],
        "x": "생산성 루틴"
    },
    "PKM": {
        "webkr": ["옵시디언 활용", "지식 관리 시스템", "제텔카스텐", "메모 앱", "옵시디언 플러그인"],
        "reddit": ["ObsidianMD", "ProductivityHacks", "Anki", "Notion", "note-taking"],
        "github": ["옵시디언", "지식 관리", "Obsidian", "knowledge", "note", "PKM"],
        "x": "옵시디언 활용"
    },
    "투자": {
        "webkr": ["배당주 투자", "ETF 종류", "주식 초보", "재테크 방법", "패시브 인컴"],
        "reddit": ["financialindependence", "investing", "stocks", "personalfinance", "valueinvesting"],
        "github": ["주식", "ETF", "배당", "trading", "finance", "investment", "portfolio"],
        "x": "배당주 투자"
    },
    "창업/비즈니스": {
        "webkr": ["창업 아이템", "사업 아이디어", "소호 사업", "부업 아이디어", "온라인 비즈니스"],
        "reddit": ["Entrepreneur", "SideProject", "startup", "smallbusiness", "korea"],
        "github": ["startup", "business", "SaaS", "indie hacker"],
        "x": "창업 팁"
    }
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

def is_korean(text):
    """한글 포함 여부 확인"""
    return bool(re.search(r'[가-힣]', text))

def search_naver_webkr(keywords, limit=5):
    """네이버 웹문서 검색 + 본문 깊게 읽기"""
    results = []

    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        log("⚠️ 네이버 API 키 없음")
        return results

    for keyword in keywords[:2]:  # 2개 키워드
        try:
            url = "https://openapi.naver.com/v1/search/webkr.json"
            headers = {
                "X-Naver-Client-Id": NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
            }
            params = {
                "query": keyword,
                "display": 10,
                "sort": "sim"
            }

            response = requests.get(url, headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                items = data.get("items", [])

                for item in items:
                    title = item.get("title", "")
                    title = title.replace("<b>", "").replace("</b>", "")
                    title = title.replace("&quot;", '"').replace("&amp;", "&")  # HTML 엔티티 디코딩

                    link = item.get("link", "")

                    if title and link and link.startswith('http') and not is_duplicate(link):
                        # 모든 항목 본문 읽기
                        log(f"   → 읽는 중: {title[:40]}...")
                        full_content = read_web_content(link)

                        if full_content:
                            results.append({
                                "title": title,
                                "url": link,
                                "content": full_content,
                                "source": "네이버"
                            })
                            add_to_duplicate_db(link)

                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break

        except Exception as e:
            log(f"⚠️ 네이버 검색 실패: {e}")

    return results

def search_reddit_korean(subreddits, limit=5):
    """Reddit 한글만 필터링 (링크만)"""
    results = []
    headers = {'User-agent': 'ClaudeCode/1.0'}

    for subreddit in subreddits[:3]:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=25"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                posts = data.get("data", {}).get("children", [])

                for post in posts:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "")
                    url = post_data.get("url", "")
                    selftext = post_data.get("selftext", "")
                    score = post_data.get("score", 0)

                    # 한글 제목만 필터링
                    if title and url and is_korean(title) and not is_duplicate(url):
                        results.append({
                            "title": title,
                            "url": url,
                            "description": selftext[:150] if selftext else f"↑ {score} points",
                            "source": f"r/{subreddit}"
                        })
                        add_to_duplicate_db(url)

                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break

        except Exception as e:
            print(f"⚠️ Reddit {subreddit} 실패: {e}")

    return results

def search_github_korean(keywords, limit=5):
    """GitHub 한글 저장소 (링크만)"""
    results = []
    headers = {'Accept': 'application/vnd.github.v3+json'}

    for keyword in keywords[:3]:
        try:
            url = f"https://api.github.com/search/repositories?q={keyword}&sort=stars&per_page=20"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                repos = data.get("items", [])

                for repo in repos:
                    name = repo.get("full_name", "")
                    url = repo.get("html_url", "")
                    description = repo.get("description", "")

                    # 한글 설명만
                    if description and is_korean(description) and not is_duplicate(url):
                        results.append({
                            "title": name,
                            "url": url,
                            "description": description,
                            "source": "GitHub"
                        })
                        add_to_duplicate_db(url)

                    if len(results) >= limit:
                        break

                if len(results) >= limit:
                    break

        except Exception as e:
            print(f"⚠️ GitHub 검색 실패: {e}")

    return results

def search_x_korean(query, limit=3):
    """Nitter로 한글 트윗 검색"""
    results = []

    try:
        # 공개 Nitter 인스턴스
        instances = ["nitter.net", "nitter.poast.org", "nitter.privacydev.net"]
        instance = random.choice(instances)

        url = f"https://{instance}/search?q={query}&f=tweets"
        headers = {'User-agent': 'ClaudeCode/1.0'}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            # 간단한 HTML 파싱 (한글 트윗 찾기)
            content = response.text

            # 한글 패턴 찾기 (간소화)
            korean_pattern = r'([가-힣]+.{1,100}[가-힣]+)'
            matches = re.findall(korean_pattern, content)

            if matches and len(matches) >= limit:
                # URL 추출 (간소화)
                urls = re.findall(r'href="/([^/]+)/status/\d+', content)

                for i, text in enumerate(matches[:limit]):
                    if i < len(urls):
                        tweet_url = f"https://x.com/{urls[i]}"
                        if not is_duplicate(tweet_url):
                            results.append({
                                "title": text[:100] + "...",
                                "url": tweet_url,
                                "description": "트윗",
                                "source": "X"
                            })
                            add_to_duplicate_db(tweet_url)

    except Exception as e:
        print(f"⚠️ Nitter 검색 실패 (무시): {e}")

    return results

def format_message(category, webkr_articles, reddit_links, github_links):
    """심층 분석 리포트 포맷팅 (네이버만 본문, 나머지 링크)"""
    report = f"📊 **{category} 심층 분석**\n\n"
    report += f"📅 {datetime.now().strftime('%Y년 %m월 %d일')}\n"
    report += f"🎯 주제: {category}\n\n"
    report += "=" * 50 + "\n\n"

    # 1. 네이버 본문 분석 (메인)
    if webkr_articles:
        report += "## 🔥 네이버 본문 분석\n\n"

        for i, article in enumerate(webkr_articles[:5], 1):
            title = article.get("title", "")
            content = article.get("content", "")
            url = article.get("url", "")

            report += f"**{i}. {title}**\n\n"

            if content:
                summary = content[:600] + "..." if len(content) > 600 else content
                report += f"{summary}\n\n"

            report += f"🔗 [원문 보기]({url})\n\n"
            report += "---\n\n"

    # 2. Reddit 큐레이션 (링크만)
    if reddit_links:
        report += "## 🔴 Reddit 한글\n\n"

        for i, item in enumerate(reddit_links[:5], 1):
            title = item.get("title", "")
            url = item.get("url", "")
            source = item.get("source", "")
            description = item.get("description", "")

            report += f"**{i}. {title}**\n"
            report += f"📍 {source}\n"
            if description:
                report += f"📝 {description[:120]}...\n"
            report += f"🔗 {url}\n\n"

    # 3. GitHub 큐레이션 (링크만)
    if github_links:
        report += "## 🐙 GitHub 한글\n\n"

        for i, item in enumerate(github_links[:5], 1):
            title = item.get("title", "")
            url = item.get("url", "")
            description = item.get("description", "")

            report += f"**{i}. {title}**\n"
            if description:
                report += f"📝 {description[:120]}...\n"
            report += f"🔗 {url}\n\n"

    report += f"💬 더 깊은 분석이 필요하시면 말씀해주세요!"

    return report

def send_to_telegram(message):
    """텔레그램 전송 (긴 메시지 분할)"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    # Telegram 제한: 4096자
    MAX_LENGTH = 4000

    if len(message) <= MAX_LENGTH:
        # 한 번에 전송
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            log("✅ 텔레그램 전송 완료")
        except Exception as e:
            log(f"❌ 전송 실패: {e}")
    else:
        # 메시지 분할 전송
        parts = []
        current_part = ""

        for line in message.split('\n'):
            if len(current_part) + len(line) + 1 > MAX_LENGTH:
                parts.append(current_part)
                current_part = line
            else:
                current_part += '\n' + line if current_part else line

        if current_part:
            parts.append(current_part)

        # 각 부분 전송
        for i, part in enumerate(parts, 1):
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": f"{part}\n\n({i}/{len(parts)})"}
            try:
                response = requests.post(url, json=data, timeout=10)
                response.raise_for_status()
                log(f"✅ 텔레그램 전송 완료 ({i}/{len(parts)})")
            except Exception as e:
                log(f"❌ 전송 실패 ({i}/{len(parts)}): {e}")

def main():
    log(f"🚀 관심사 심층 분석 시작: {datetime.now()}")

    category = random.choice(list(INTERESTS.keys()))
    sources = INTERESTS[category]

    log(f"📊 주제: {category}")

    # 1. 네이버 웹문서 본문 깊게 읽기
    webkr_articles = []
    if "webkr" in sources:
        log("🔍 네이버 웹문서 검색 + 본문 분석 중...")
        webkr_articles = search_naver_webkr(sources["webkr"], limit=5)
        log(f"   → {len(webkr_articles)}개")

    # 2. Reddit 한글
    reddit_links = []
    if "reddit" in sources:
        log("🔴 Reddit 한글 검색 중...")
        reddit_links = search_reddit_korean(sources["reddit"], limit=5)
        log(f"   → {len(reddit_links)}개")

    # 3. GitHub 한글
    github_links = []
    if "github" in sources:
        log("🐙 GitHub 한글 검색 중...")
        github_links = search_github_korean(sources["github"], limit=5)
        log(f"   → {len(github_links)}개")

    if not webkr_articles and not reddit_links and not github_links:
        log("📭 결과 없음")
        return

    log(f"✅ 총 {len(webkr_articles) + len(reddit_links) + len(github_links)}개 수집 완료")

    # 리포트 생성
    report = format_message(category, webkr_articles, reddit_links, github_links)

    # 텔레그램 전송
    send_to_telegram(report)

    log(f"✅ 심층 분석 완료")

if __name__ == "__main__":
    main()
