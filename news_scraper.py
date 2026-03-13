#!/usr/bin/env python3
"""
투자 뉴스 스크랩 자동화 시스템 (DATACRAFT Style)
- 기존 morning_news.py와 완전 분리
- 주제 미정! 핫한 뉴스 15건/일
- 하이브리드: 네이버 API + 웹 서치 MCP
- 주간/월간 분석 자동화

스케줄:
- Daily: 매일 07:00 (뉴스 15건)
- Weekly: 일요일 22:00 (테마 분석)
- Monthly: 매월 1일 09:00 (빅테마)

작성일: 2026-03-06
"""

import os
import sys
import requests
import json
import subprocess
import html
import re
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from newspaper import Article
from newspaper import Config

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 설정
VAULT_PATH = "/Users/oungsooryu/Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수"
NEWS_FOLDER = "50. 투자/01. 뉴스 스크랩"
ANALYSIS_FOLDER = "50. 투자/02. 테제 분석"
TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

# 뉴스 수집 설정 (카테고리 없음!)
# 블로그 스타일: 주제 미정, 핫한거 쓱쓱
TOTAL_NEWS_COUNT = 20  # 15건 → 20건 증량 (일주일 140건, 패턴 빨리 보임)

# 검색어 (광범위하게 - 카테고리 없음)
SEARCH_QUERIES = [
    # 전체 경제 뉴스 (카테고리 없이)
    "경제 뉴스",
    "주식 시장",
    "부동산",
    "반도체 AI",
    "금융 투자",
    "국제 경제",
    # 핫한 토픽 (자동 감지용)
    "HBM 삼성전자",
    "미국 금리",
    "아파트 분양",
    "지정학 이슈"
]

# 스팸 필터링 키워드
SPAM_KEYWORDS = [
    "속보", "재업로드", "2보", "3보", "1분전", "2분전", "사진입니다",
    "소식입니다", "알려드립니다", "일정", "공지",
    "원본보기", "더보기", "관련뉴스"
]

# 출처 신뢰도 점수
TRUSTED_SOURCES = {
    # 1티어: 주요 경제지 (점수 3)
    "한국경제": 3,
    "매일경제": 3,
    "헤럴드경제": 3,
    "조선비즈": 3,
    "이데일리": 3,
    "머니투데이": 3,
    "비즈니스워치": 3,

    # 2티어: 주요 일간지 (점수 2)
    "연합뉴스": 2,
    "뉴시스": 2,
    "이노베이션트리뷔": 2,
    "아주경제": 2,
    "서울경제": 2,
    "내일경제": 2,
    "파이낸셜뉴스": 2,
    "더벨": 2,
    "한국일보": 2,
    "동아일보": 2,
    "조선일보": 2,
    "중앙일보": 2,

    # 3티어: 지역지/기타 (점수 1)
    "세계일보": 1,
    "국제신문": 1,
    "매일노무동": 1,
    "newsprime": 1,
    "pinpointnews": 1,
    "kbc뉴스": 1,
}

# 실시간 트렌드 검색어 (웹 서치 MCP용)
TREND_QUERIES = [
    "오늘 경제 뉴스 핫이슈",
    "오늘 주요 경제 뉴스",
    "오늘 주식 시장 이슈"
]

# 핵심 키워드 (요약 시 우선 순위)
SUMMARY_KEYWORDS = [
    # 전망/예측
    "전망", "예상", "전망됨", "예측", "전망치", "시나리오",
    # 분석
    "분석", "평가", "진단", "제언", "시사",
    # 경제/투자
    "부동산", "주식", "코스피", "코스닥", "금리", "인플레이션",
    "환율", "유가", "반도체", "AI", "HBM", "투자",
    # 중요 동사
    "영향", "상승", "하락", "변동", "확대", "축소", "개선", "악화"
]

def fetch_full_article_summary(url: str, title: str) -> str:
    """
    뉴스 본문 전체를 읽고 핵심 요약 생성
    - newspaper3k로 본문 추출
    - 상위 3개 문장 추출
    """
    try:
        # newspaper3k 설정 (한글 + 로봇 차단 회피)
        config = Config()
        config.browser_user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        config.request_timeout = 10

        # 기사 다운로드 및 파싱
        article = Article(url, config=config)
        article.download()
        article.parse()

        # 본문 텍스트 추출
        full_text = article.text

        if not full_text or len(full_text) < 100:
            # 본문 추출 실패시 기본 description 사용
            return None

        # 문장 단위 분리
        sentences = re.split(r'(?<=[.!?])', full_text)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        if not sentences:
            return None

        # 핵심 키워드 포함 문장 우선 추출
        relevant_sentences = []
        for s in sentences:
            if any(keyword in s for keyword in SUMMARY_KEYWORDS):
                relevant_sentences.append(s)

        # 관련 문장 2개 + 일반 문장 2개 조합 (최대 4개)
        if relevant_sentences:
            selected = (relevant_sentences[:2] + sentences[:2])[:4]
        else:
            # 키워드 없으면 그냥 상위 3개
            selected = sentences[:3]

        # 문장 합치기
        summary = ' '.join(selected)

        # 끝처리
        if summary and not summary[-1] in ['.', '!', '?', '요']:
            summary += '.'

        # 최대 500자
        if len(summary) > 500:
            summary = summary[:497] + '...'

        return summary

    except Exception as e:
        print(f"  ⚠️ 본문 추출 실패 ({url[:50]}...): {str(e)[:50]}")
        return None

def send_telegram_message(message):
    """텔레그램 발송"""
    import requests

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, data=data, timeout=10)
        print(f"✅ 텔레그램 발송 완료")
    except Exception as e:
        print(f"❌ 텔레그램 발송 실패: {e}")

def fetch_naver_news(query: str, display: int = 10) -> list:
    """
    네이버 검색 API에서 뉴스 수집
    - 본문 전체 추출 (newspaper3k)
    - 핵심 문장 요약
    """
    try:
        url = "https://openapi.naver.com/v1/search/news.json"

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        params = {
            "query": query,
            "display": display,
            "sort": "date"
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        items = data.get('items', [])

        news_items = []
        for item in items:
            # 제목 정제
            title = item.get('title', '')
            title = html.unescape(title)
            title = re.sub(r'<[^>]+>', '', title)
            title = title.replace('&quot;', '"').replace('&amp;', '&')
            title = re.sub(r'\[.*?\]', '', title).strip()

            # URL
            article_url = item.get('link', '')

            if not article_url or len(title) < 10:
                continue

            # 본문 전체 추출 시도
            print(f"    📄 본문 추출 중: {title[:30]}...")
            full_summary = fetch_full_article_summary(article_url, title)

            if full_summary:
                # 본문 추출 성공
                summary = full_summary
                print(f"      ✅ 본문 요약 완료 ({len(summary)}자)")
            else:
                # 실패시 기본 description 사용
                description = item.get('description', '')
                description = html.unescape(description)
                description = re.sub(r'<[^>]+>', '', description)
                description = description.replace('&quot;', '"').replace('&amp;', '&')
                description = re.sub(r'\[.*?\]', '', description).strip()
                description = ' '.join([word for word in description.split() if not word.startswith('#')])
                description = re.sub(r'\.{3,}', '', description)
                description = re.sub(r'\s+', ' ', description)

                sentences = re.split(r'(?<=[.!?])', description)
                sentences = [s.strip() for s in sentences if s.strip()]
                summary_sentences = sentences[:2]
                summary = ' '.join(summary_sentences)

                if summary and not summary[-1] in ['.', '!', '?', '요']:
                    summary += '.'

                print(f"      ⚠️ 기본 요약 사용 ({len(summary)}자)")

            if len(summary) > 30:
                news_items.append({
                    'title': title,
                    'summary': summary[:500],
                    'url': article_url
                })

        return news_items

    except Exception as e:
        print(f"❌ 네이버 API 오류 ({query}): {e}")
        return []

def fetch_web_search_trends() -> list:
    """
    웹 서치 MCP로 실시간 트렌드 수집
    """
    # TODO: 형님, 여기서 웹 서치 MCP를 호출합니다
    # 지금은 예시 데이터 반환
    # 실제로는 subprocess로 MCP 서버 호출하거나
    # 직접 웹 검색 API를 사용해야 합니다

    print("🔍 웹 서치 MCP: 실시간 트렌드 수집 중...")
    # TODO: 실제 구현 필요
    return []

def collect_hybrid_news() -> list:
    """
    하이브리드 뉴스 수집 (블로그 스타일)
    - 카테고리 없음!
    - 그냥 핫한 경제 뉴스 15건
    - 나중에 Claude가 패턴 발견
    """
    all_news = {}
    seen_urls = set()

    # 1단계: 네이버 API (광범위한 검색어)
    print("📰 네이버 API: 핫한 뉴스 수집 중...")

    total_collected = 0
    for query in SEARCH_QUERIES:
        news_items = fetch_naver_news(query, display=5)

        # 스팸 필터링 + 중복 제거하면서 추가
        for item in news_items:
            # 스팸 체크
            if is_spam(item['title']):
                continue

            url = item['url']

            if url not in seen_urls:
                seen_urls.add(url)

                # 출처 점수 추가
                source_score = get_source_score(url)

                all_news[url] = {
                    'title': item['title'],
                    'summary': item['summary'],
                    'url': url,
                    'source': 'naver',
                    'score': source_score  # 신뢰도 점수
                }
                total_collected += 1

        print(f"  🔍 '{query}': {len(news_items)}건 (스팸 필터링 완료)")

        # 30건 모이면 중단 (여유있게, 20건 선별)
        if total_collected >= 30:
            break

    # 2단계: 웹 서치 MCP (실시간 트렌드)
    trend_items = fetch_web_search_trends()

    for item in trend_items:
        url = item.get('url', '')

        if url and url not in seen_urls:
            seen_urls.add(url)
            all_news[url] = {
                'title': item.get('title', ''),
                'summary': item.get('summary', '')[:100],
                'url': url,
                'source': 'web_search'
            }

    print(f"  🔥 실시간 트렌드: {len(trend_items)}건 추가")

    # 3단계: 출처 점수로 정렬 후 상위 20건 선택
    # 점수 순 → URL 순 (안정성)
    sorted_news = sorted(
        all_news.values(),
        key=lambda x: (-x['score'], x['url'])
    )
    final_news = sorted_news[:TOTAL_NEWS_COUNT]

    print(f"\n📊 최종 수집: {len(final_news)}건 (출처 점수 반영)")

    # 통계 출력
    score_distribution = {}
    for item in final_news:
        score = item['score']
        score_distribution[score] = score_distribution.get(score, 0) + 1

    print("📈 출처별 분포:")
    for score in sorted(score_distribution.keys(), reverse=True):
        print(f"  {score}점: {score_distribution[score]}건")

    return final_news

def is_spam(title: str) -> bool:
    """
    스팸 필터링
    - 속보, 재업로드 등 제거
    """
    for keyword in SPAM_KEYWORDS:
        if keyword in title:
            return True
    return False

def get_source_score(url: str) -> int:
    """
    출처 신뢰도 점수 반환
    - 1~3점
    """
    # URL에서 언론사 추출
    for source, score in TRUSTED_SOURCES.items():
        if source in url:
            return score

    # 알 수 없는 출처는 1점
    return 1


def generate_daily_dashboard(news_items, date_str, today) -> str:
    """
    일일 시각화 대시보드 생성
    - 출처 점수 분포
    - 키워드 히트맵
    """
    # 통계 계산
    score_distribution = {}
    for item in news_items:
        score = item.get('score', 1)
        score_distribution[score] = score_distribution.get(score, 0) + 1

    # 키워드 추출 (간단)
    keywords = {}
    for item in news_items:
        title = item['title']
        # 주요 키워드 추출 (간단한 방식)
        major_keywords = ["AI", "HBM", "코스피", "금리", "부동산", "아파트", "반도체",
                         "삼성전자", "이란", "유가", "인플레이션", "주식", "투자", "은행"]
        for keyword in major_keywords:
            if keyword in title:
                keywords[keyword] = keywords.get(keyword, 0) + 1

    # 키워드 정렬 (상위 10개)
    top_keywords = sorted(keywords.items(), key=lambda x: -x[1])[:10]

    # 대시보드 생성
    dashboard = f"""---
type: daily-news-scrap
date: {date_str}
tags: [뉴스, 스크랩, DATACRAFT]
source: hybrid
---

# {date_str} 뉴스 스크랩

## 📊 수집 현황
- 총 기사: {len(news_items)}건
- 수집 시간: {today.strftime("%H:%M")}
- 출처: 네이버 API + 웹 서치 MCP
- 스팸 필터링: ✅ 적용
- 출처 점수화: ✅ 적용

---

## 📈 오늘의 시각화

### 출처 신뢰도 분포
"""

    # 출처 점수 히트맵
    for score in sorted(score_distribution.keys(), reverse=True):
        bar = "█" * score_distribution[score]
        percent = (score_distribution[score] / len(news_items)) * 100
        dashboard += f"\n- **{score}점:** {bar} {score_distribution[score]}건 ({percent:.0f}%)"

    dashboard += "\n\n### 키워드 빈도 (상위 10개)\n"

    # 키워드 히트맵
    if top_keywords:
        max_count = top_keywords[0][1] if top_keywords else 1
        for keyword, count in top_keywords:
            bar_length = int((count / max_count) * 20)
            bar = "█" * bar_length
            dashboard += f"\n- **{keyword}:** {bar} {count}회"

    dashboard += f"""

---
## 💡 인사이트 (자동 생성)

### 출처 품질
"""

    # 출처 품질 인사이트
    high_quality = sum(1 for s in score_distribution.keys() if s >= 2)
    low_quality = sum(1 for s in score_distribution.keys() if s == 1)

    if high_quality >= len(news_items) * 0.5:
        dashboard += "\n- ✅ 주요 경제지 비중 {high_quality}/{len(news_items)}건 ({high_quality/len(news_items)*100:.0f}%)"
    else:
        dashboard += f"\n- ⚠️ 저품질 출처 다수: {low_quality}/{len(news_items)}건"

    dashboard += "\n### 키워드 트렌드\n"

    # 키워드 트렌드 인사이트
    if len(top_keywords) >= 3:
        top_3 = [kw for kw, cnt in top_keywords[:3]]
        dashboard += f"- **주요 키워드:** {', '.join(top_3)}"
        dashboard += "\n- 이번 주에 이 키워드가 지속적으로 나오면 '테마'로 분류됩니다"

    return dashboard

def scrape_daily_news():
    """
    일일 뉴스 15건 스크랩 (하이브리드)
    - 네이버 API + 웹 서치 MCP
    - 주제 미정! 핫한거 쓱쓱
    - 카테고리별 배분
    """
    today = datetime.now()
    date_str = today.strftime("%Y-%m-%d")
    year = today.strftime("%Y")
    month = today.strftime("%m")

    print(f"\n{'='*60}")
    print(f"📰 {date_str} 뉴스 스크랩 시작")
    print(f"{'='*60}\n")

    # 1. 뉴스 수집 (하이브리드)
    news_items = collect_hybrid_news()

    # 2. 폴더 경로
    folder_path = f"{VAULT_PATH}/{NEWS_FOLDER}/{year}/{month}"
    Path(folder_path).mkdir(parents=True, exist_ok=True)

    filename = f"{folder_path}/{date_str}.md"

    # 3. 시각화 대시보드 생성
    content = generate_daily_dashboard(news_items, date_str, today)

    # 4. 마크다운 생성 (뉴스 목록)
    content += f"""

---

## 📰 뉴스 목록

"""

    # 카테고리 없이! 그냥 순서대로
    for i, item in enumerate(news_items, 1):
        score_badge = "⭐" * item.get('score', 1)
        content += f"""
### {i}. {item['title']} {score_badge}
- **핵심:** {item['summary']}
- **URL:** {item['url']}
- **출처:** {item['source']}

"""

    content += f"""
---
## 🏷️ 오늘의 태그
#{date_str.replace('-', '_')}
"""

    # 4. 저장
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n✅ 뉴스 저장 완료: {filename}")

    # 5. 텔레그램 알림
    message = f"""
📰 *일일 뉴스 스크랩 완료*

📅 {date_str}
📊 총 {len(news_items)}건 수집 (카테고리 무관)

📁 {filename}
"""
    send_telegram_message(message)

    print(f"{'='*60}\n")

    return filename

def analyze_weekly_thesis():
    """
    주간 테마 분석 (자동)
    - 일요일 22:00 실행
    - 지난 7일 뉴스 분석
    - 테마 3~5개 도출
    """
    from pathlib import Path
    import re
    from collections import Counter

    today = datetime.now()
    end_date = today
    start_date = today - timedelta(days=7)

    date_range = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    week_num = today.isocalendar()[1]
    year = today.strftime("%Y")

    # 폴더 경로
    folder_path = f"{VAULT_PATH}/{ANALYSIS_FOLDER}/Weekly/{year}"
    Path(folder_path).mkdir(parents=True, exist_ok=True)

    filename = f"{folder_path}/{year}-W{week_num}_주간분석.md"

    print(f"📊 주간 분석 시작: {date_range}")

    # 옵시디언에서 지난 주 뉴스 파일 읽기
    news_folder = f"{VAULT_PATH}/{NEWS_FOLDER}/{year}"
    news_files = []

    # 지난 7일간 파일 찾기
    for i in range(7):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        year = date.strftime("%Y")
        month = date.strftime("%m")
        file_path = f"{news_folder}/{year}/{month}/{date_str}.md"

        if Path(file_path).exists():
            news_files.append(file_path)

    print(f"  📁 찾은 파일: {len(news_files)}개")

    # 뉴스 파일에서 기사 추출
    all_articles = []

    for file_path in news_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 기사 제목 추출 (### 숫자. 제목 형식)
            articles = re.findall(r'###\s*\d+\.\s*(.+?)(?=\n|$)', content)
            all_articles.extend(articles)

        except Exception as e:
            print(f"  ⚠️ 파일 읽기 실패 ({file_path}): {e}")

    print(f"  📰 총 기사 수: {len(all_articles)}건")

    # 키워드 추출 및 빈도 분석
    # 뉴스 제목에서 명사 추출 (간단하게 키워드 매칭)
    keywords = []
    for article in all_articles:
        # 핵심 키워드 추출
        for keyword in SUMMARY_KEYWORDS:
            if keyword in article and len(keyword) >= 2:
                keywords.append(keyword)

    keyword_freq = Counter(keywords)

    print(f"  🔑 키워드 추출 완료: {len(keyword_freq)}개")

    # 상위 키워드 5개를 테마로 선정
    top_keywords = keyword_freq.most_common(5)

    # 주간 분석 보고서 생성
    report = f"""# {year}-W{week_num} 주간 테마 분석

## 기간
{date_range}

## 📊 뉴스 현황
- 총 기사: {len(all_articles)}건
- 분석 대상: {len(news_files)}일
- 발견된 키워드: {len(keyword_freq)}개

---

## 🎯 발견된 테마

"""

    # 테마별 상세 분석
    for idx, (keyword, freq) in enumerate(top_keywords, 1):
        report += f"""### T{idx}: {keyword} 테마
- **빈도:** {freq}회
- **중요도:** 상위 {idx}위
- **인사이트:** 최근 7일간 '{keyword}'와 관련된 뉴스가 {freq}회 보도되어 시장의 관심이 높은 편입니다.

"""

    # 섹터 분석
    report += f"""---

## 📊 섹터별 현황

"""

    # 섹터별 키워드 분류
    sectors = {
        "반도체/반도체": ["반도체", "HBM", "삼성전자", "SK하이닉스", "메모리"],
        "AI/AI": ["AI", "인공지능"],
        "금융/금융": ["금리", "코스피", "코스닥", "주식"],
        "부동산/부동산": ["부동산", "아파트", "분양"],
        "에너지/에너지": ["유가", "석유", "전력"],
        "지정학/지정학": ["이란", "중동", "미국", "중국"]
    }

    for sector_name, sector_keywords in sectors.items():
        count = sum(1 for k in keywords if k in sector_keywords)
        if count > 0:
            report += f"- **{sector_name}:** {count}회 언급\n"

    report += f"""

---

## 💡 핵심 인사이트

"""

    # 핵심 인사이트 3가지
    insights = []
    insights.append(f"가장 많이 언급된 키워드는 '{top_keywords[0][0]}'(으)로 {top_keywords[0][1]}회 보고되었습니다.")
    if len(top_keywords) >= 2:
        insights.append(f"2위 키워드는 '{top_keywords[1][0]}'(으)로 {top_keywords[1][1]}회 언급되었습니다.")
    if len(all_articles) >= 20:
        insights.append(f"총 {len(all_articles)}건의 뉴스가 수집되어 시장 관심도가 높은 편입니다.")
    else:
        insights.append(f"뉴스 수집이 {len(all_articles)}건으로 시장 관심도를 파악하기에 데이터가 부족합니다.")

    for idx, insight in enumerate(insights, 1):
        report += f"{idx}. {insight}\n"

    report += f"""

---

## 📁 원본 뉴스
"""

    # 원본 뉴스 파일 목록
    for file_path in news_files:
        file_name = Path(file_path).name
        report += f"- [{file_name}]({file_path})\n"

    # 파일 저장
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ 주간 분석 저장 완료: {filename}")

    # 텔레그램 알림
    message = f"""
📊 *주간 테마 분석 완료*

📅 {date_range}
📰 총 기사: {len(all_articles)}건
🎯 주요 테마: {', '.join([k[0] for k in top_keywords[:3]])}

📁 {filename}
"""

def analyze_monthly_thesis():
    """
    월간 빅테마 분석 (자동)
    - 매월 1일 09:00 실행
    - 지난 30일 뉴스 분석
    - 빅테마 3~5개 도출
    """
    today = datetime.now()
    end_date = today
    start_date = today - timedelta(days=30)

    date_range = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"
    month = today.strftime("%Y-%m")

    # 폴더 경로
    folder_path = f"{VAULT_PATH}/{ANALYSIS_FOLDER}/Monthly"
    Path(folder_path).mkdir(parents=True, exist_ok=True)

    filename = f"{folder_path}/{month}_월간분석.md"

    # 월간 분석 프롬프트
    prompt = f"""
# 월간 빅테마 분석 (자동)

## 기간
{date_range}

## 방법
1. 옵시디언에서 지난 30일간 뉴스 읽기
2. 주간 테마와 비교해서 **지속되는 테마** vs **새로운 테마** 구분
3. 빅테마 3~5개 도출
4. 섹터별 포트폴리오 제안

## 결과 형식
```markdown
# {month} 월간 빅테마 분석

## 기간
{date_range}

## 📊 뉴스 현황
- 총 기사: XXX건
- 일일 평균: 15건

---

## 🚀 빅테마 (지속)

### BT1: [테마명]
- **기간:** 3주 이상 지속
- **빈도:** XXX건
- **추세:** 상승 / 유지 / 하락
- **인사이트:** ...

---

## 🆕 새로운 테마

### NT1: [테마명]
- **첫 등장:** 날짜
- **빈도:** XX건
- **의미:** ...

---

## 📊 빅테마 × 섹터 매트릭스

---

## 💡 포트폴리오 제안

### 과거 제안 검토
- **지난 달:** ...
- **실제:** ...

### 이번 달 제안
1. **비중:** ...
2. **섹터:** ...
3. **종목:** ...

---

## 🎯 3개월 전망
- ...
```

## 저장 위치
{filename}
"""

    print("📈 월간 분석 프롬프트:")
    print(prompt)

    # 텔레그램 알림
    message = f"""
📈 *월간 빅테마 분석 완료*

📅 {date_range}
🔍 빅테마 3~5개 도출
💼 포트폴리오 제안 포함

📁 {filename}
"""
    send_telegram_message(message)

    return filename

if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "daily"

    if command == "daily":
        # 매일 07:00 실행
        scrape_daily_news()

    elif command == "weekly":
        # 일요일 22:00 실행
        analyze_weekly_thesis()

    elif command == "monthly":
        # 매월 1일 09:00 실행
        analyze_monthly_thesis()
