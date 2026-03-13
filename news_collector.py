#!/usr/bin/env python3
"""
뉴스 스크랩 & 패턴 분석 시스템 (DATACRAFT Style)
- 주제 미리 정하지 X
- 매일 핫한 뉴스 쓱쓱 스크랩
- 1주일/한달 쌓이면 Claude가 패턴 발견
- "점묘화"처럼 쌓이다 보면 그림이 보임

작성일: 2026-03-06
작성자: Claude + 형님
"""

import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 설정
VAULT_PATH = "/Users/oungsooryu/Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수"
NEWS_FOLDER = "50. 투자/01. 뉴스 스크랩"
ANALYSIS_FOLDER = "50. 투자/02. 테제 분석"

def collect_hot_news():
    """오늘 핫한 뉴스 수집 (주제 X)"""
    today = datetime.now().strftime("%Y-%m-%d")

    # 경제/부동산/IT 톱 뉴스 (기존 morning_news.py 활용)
    # 형님, 여기서 웹 서치 MCP로 "오늘 경제 뉴스" 검색
    # 주제 미정! 그냥 핫한거 쓱쓱

    prompt = f"""
# 오늘 핫한 경제 뉴스 스크랩

## 기간
{today}

## 해주세요
1. 경제/부동산/IT/금융 뉴스 톱 15개 수집
2. 주제 미정! 그냥 지금 핫한거
3. 각 기사 핵심 1문장 요약

## 카테고리
- 경제 전반
- 부동산
- IT/반도체
- 금융/투자
- 지정학
- 가상자산
- 기타

## 결과 형식
옵시디언 마크다운으로 정리
"""

    return prompt

def save_daily_news_to_obsidian(news_items):
    """옵시디언에 일일 뉴스 저장"""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"{VAULT_PATH}/{NEWS_FOLDER}/{today}.md"

    Path(f"{VAULT_PATH}/{NEWS_FOLDER}").mkdir(parents=True, exist_ok=True)

    content = f"""---
type: daily-news-scrap
date: {today}
tags: [뉴스, 스크랩, DATACRAFT]
---

# {today} 뉴스 스크랩

## 수집 현황
- 총 기사: {len(news_items)}건
- 주제: 미정 (그냥 핫한거)

## 기사 목록

"""

    for i, item in enumerate(news_items, 1):
        content += f"""
### {i}. {item['title']}
- **카테고리:** {item['category']}
- **핵심:** {item['summary']}
- **URL:** {item['url']}
- **태그:** #{item['category'].replace(' ', '_')}
"""

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 옵시디언 저장 완료: {filename}")
    return filename

def discover_patterns_from_news(days=7):
    """
    일주일 뉴스에서 패턴 발견 (주제 X)
    Claude가 자동으로 테마 찾아줌
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    date_range = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    prompt = f"""
# 뉴스 패턴 분석 (점묘화 스타일)

## 기간
{date_range}

## 방법
1. 옵시디언에서 지난 {days}일간 뉴스 읽기
2. **주제 미정!** 자주 나오는 키워드 발견
3. 연관된 기사끼리 묶기
4. 테마(Thesis) 도출

## 예시 output
"지난 일주일 AI 인프라 기사가 12건, 지정학이 8건 나왔네.
이 둘을 연결하면: AI 전력 공급망이 지정학 리스크에 노출되는 구조다."

## 결과
- 테마 3~5개 도출
- 테마 × 섹터 매트릭스
- 핵심 인사이트
"""

    return prompt

def create_thesis_matrix(discovered_themes):
    """
    발견된 테마로 매트릭스 생성
    (�로그 글의 표와 유사)
    """
    # TODO: Claude가 테마 발견하면 그걸로 매트릭스 생성
    pass

if __name__ == "__main__":
    import sys

    command = sys.argv[1] if len(sys.argv) > 1 else "daily"

    if command == "daily":
        # 매일 실행: 핫한 뉴스 쓱쓱 스크랩 (주제 X)
        print("🔥 오늘 핫한 뉴스 수집 중...")
        prompt = collect_hot_news()
        print("📝 Claude에게 뉴스 수집 요청:")
        print(prompt)
        # TODO: Claude Code API 호출

    elif command == "weekly":
        # 매주 일요일: 패턴 분석
        print("🔍 지난 일주일 뉴스에서 패턴 찾는 중...")
        prompt = discover_patterns_from_news(days=7)
        print("📊 Claude에게 분석 요청:")
        print(prompt)
        # TODO: Claude Code API 호출

    elif command == "monthly":
        # 매월 1일: 월간 빅테마 분석
        print("🚀 지난 달 뉴스 빅테마 분석...")
        prompt = discover_patterns_from_news(days=30)
        print("📈 Claude에게 분석 요청:")
        print(prompt)
        # TODO: Claude Code API 호출
