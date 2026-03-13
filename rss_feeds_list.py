#!/usr/bin/env python3
"""
한국 주요 뉴스 사이트 RSS 피드 리스트
- 부동산, 경제, IT, 뇌과학, PKM 분야
"""

RSS_FEEDS = {
    "부동산": [
        # 매일경제
        "https://www.mk.co.kr/news/rss/rss.xml",
        # 머니투데이
        "https://news.mt.co.kr/news/rss/rss.xml",
        # 한국경제신문
        "https://www.hankyung.com/rss/section.xml"  # 부동산 섹션
        # 헤럴드경제
        "https://www.heraldcorp.com/",
    ],

    "AI/IT": [
        # ITWorld
        "https://www.itworld.co.kr/rss/A.xml",
        # ZDNet Korea
        "https://www.zdnet.co.kr/news/news/rss.xml",
        # 기타
        "https://news.naver.com/rss/IT.xml",
    ],

    "뇌과학/생산성": [
        # 브런치 한국어 (없을 수도 있음)
        # 해외 사이트
        "https://news.google.com/rss/search?q=%EB%87%8C%EA%B3%BC%ED%95%99&hl=ko&gl=KR&ceid=KR:ko",
    ],

    "PKM/생산성": [
        # Notion 블로그
        "https://www.notion.so/rss.xml",  # 공식 RSS 없을 수 있음
        # Slab 블로그
        "https://news.naver.com/rss/search?q=%EC%98%B5%EC%8B%9C%EB%94%94%EC%95%88&hl=ko&gl=KR&ceid=KR:ko",
    ],

    "투자": [
        # 한국투자증권협회
        "https://www.ksd.co.kr/rss/news.xml",  # 없을 수 있음
        # 머니투데이 투자
        "https://news.mt.co.kr/news/invest/rss.xml",
    ]
}

# 네이버 뉴스 RSS (카테고리별)
NAVER_NEWS_RSS = {
    "부동산": "https://news.naver.com/rss/section_list.xml?cid=267",  # 부동산 일반
    "경제": "https://news.naver.com/rss/section_list.xml?cid=101",  # 경제 일반
    "IT/과학": "https://news.naver.com/rss/section_list.xml?cid=105",  # IT/과학
    "생활/문화": "https://news.naver.com/rss/section_list.xml?cid=103",  # 생활/문화
}

# 해외 주요 RSS (영어)
FOREIGN_RSS = {
    "AI/ML": [
        "https://www.artificialintelligence-news.com/feed",
        "https://openai.com/rss/blog/",
    ],
    "Productivity": [
        "https://news.google.com/rss/search?q=productivity+hacks&hl=en",
    ],
}
