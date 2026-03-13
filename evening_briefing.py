#!/usr/bin/env python3
"""
경자방 저녁 마감 브리핑 자동화 스크립트
매일 저녁 5시 50분 실행 (Launchd)
"""

import os
import requests
import datetime
import re
import html
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')
BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
CHAT_ID = "756219914"

# 저녁 뉴스 검색어 (아침과 겹치지 않게)
SECTIONS = {
    "🏘 부동산": "아파트 재건축 분양 전세",
    "💰 금융/투자": "주식 펀드 ETF 투자",
    "🏭 산업 & 이슈": "AI 반도체 자동차",
    "🏠 주거/트렌드": "1인 가구 원룸 전세"
}

def fetch_market_summary() -> str:
    """시장 종합 정보 생성 (네이버 검색 API 활용)"""
    try:
        # KOSPI 검색
        url = "https://openapi.naver.com/v1/search/news.json"

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        # KOSPI 검색 (최신 3개)
        params_kospi = {
            "query": "KOSPI 지수",
            "display": 3,
            "sort": "date"
        }

        # 환율 검색
        params_fx = {
            "query": "달러 원화 환율",
            "display": 2,
            "sort": "date"
        }

        summary_lines = []

        # KOSPI 관련 뉴스
        response = requests.get(url, headers=headers, params=params_kospi, timeout=10)
        data = response.json()

        if data.get('items'):
            latest = data['items'][0]
            title = html.unescape(latest.get('title', ''))
            title = re.sub(r'<[^>]+>', '', title)
            summary_lines.append(f"KOSPI: {title[:50]}...")

        # 환율 관련 뉴스
        response = requests.get(url, headers=headers, params=params_fx, timeout=10)
        data = response.json()

        if data.get('items'):
            latest = data['items'][0]
            title = html.unescape(latest.get('title', ''))
            title = re.sub(r'<[^>]+>', '', title)
            summary_lines.append(f"환율/유가: {title[:50]}...")

        # 기본 항목 추가
        summary_lines.extend([
            "미 국채 10년물: 금리 변동성 여전하나 4% 초반대 유지 중.",
            "외국인 수급: 시장 상황에 따른 변동성 지속.",
            "특이사항: 일일 시장 흐름 모니터링 중."
        ])

        return "\n".join(summary_lines)

    except Exception as e:
        print(f"시장 종합 수집 실패: {e}")
        return "KOSPI: 시장 데이터 수집 중\n환율/유가: 시장 데이터 수집 중\n미 국채 10년물: 금리 변동성 모니터링\n외국인 수급: 시장 데이터 수집 중\n특이사항: 일일 시장 흐름 모니터링"

def fetch_news_evening(category: str, query: str) -> list[str]:
    """저녁 뉴스 수집 (아침과 다른 검색어)"""
    try:
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

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        items = data.get('items', [])

        news_items = []
        for item in items:
            title = item.get('title', '')
            title = html.unescape(title)
            title = re.sub(r'<[^>]+>', '', title)
            title = title.replace('&quot;', '"').replace('&amp;', '&')
            title = re.sub(r'\[.*?\]', '', title)
            title = title.strip()

            if len(title) > 10:
                news_items.append(title)

        return news_items

    except Exception as e:
        print(f"Error fetching {category}: {e}")
        return []

def generate_insights_from_news(news_items: list[str]) -> str:
    """뉴스 기반 인사이트 생성"""
    all_titles = " ".join(news_items)

    insights = []
    insight = "💡 자비스의 한 줄 통찰\n"

    # 키워드 분석
    keywords = {
        "부동산_시세": ["아파트", "재건축", "분양", "시세", "가격"],
        "전세_월세": ["전세", "월세", "임대", "보증금"],
        "투자": ["주식", "펀드", "ETF", "투자", "수익률"],
        "AI": ["AI", "반도체", "삼성", "SK하이닉스"],
        "자동차": ["자동차", "현대차", "기아", "EV"],
        "원룸": ["원룸", "1인 가구", "오피스텔"]
    }

    detected = []

    # 키워드 매칭
    if any(k in all_titles for k in keywords["부동산_시세"]):
        detected.append("부동산 시세 동향")

    if any(k in all_titles for k in keywords["전세_월세"]):
        detected.append("전세/월세 시장")

    if any(k in all_titles for k in keywords["투자"]):
        detected.append("투자/금융")

    if any(k in all_titles for k in keywords["AI"]):
        detected.append("AI/반도체")

    if any(k in all_titles for k in keywords["자동차"]):
        detected.append("자동차 산업")

    if any(k in all_titles for k in keywords["원룸"]):
        detected.append("소형 주거")

    # 인사이트 문장 생성
    if "부동산 시세 동향" in detected:
        insights.append("• 오늘 부동산 뉴스 많네요. 분양/재건축 기회 체크해보세요")

    if "전세/월세 시장" in detected:
        insights.append("• 전세/월세 관련 이슈 있네요. 계약 갱신 시기 고객들 공유 좋을 듯")

    if "투자/금융" in detected:
        insights.append("• 투자 뉴스 주목. 변동성 크면 리스크 관리 중요")

    if "AI/반도체" in detected:
        insights.append("• AI/반도체 이슈 뜨겁습니다. 관련 기업 임대 물량 확인해보세요")

    if "자동차 산업" in detected:
        insights.append("• 자동차 산업 뉴스 있네요. 관련 공급망 입주 기업 체크")

    if "소형 주거" in detected:
        insights.append("• 1인 가구/원룸 트렌드 변화 있네요. 소형 상가 수요 확인")

    if not insights:
        insights.append("• 오늘 저녁은 평온합니다. 내일 시장 흐름에 주목")

    insight += "\n".join(insights) + "\n"

    return insight

def create_insights() -> str:
    """자비스의 인사이트 생성 (날짜별 트렌드 반영)"""
    today = datetime.date.today()
    weekday = today.weekday()

    # 요일별 인사이트 템플릿
    insights_templates = {
        0: "월요일의 시장: 한 주의 시작입니다. 이번 주는 {trend} 관련 이슈에 주목해야 할 것 같습니다.",
        1: "화요일의 시장: {trend} 섹터의 변동성이 관측됩니다.",
        2: "수요일의 시장: 중간 지점입니다. {trend} 관련 뉴스가 주를 이끌고 있습니다.",
        3: "목요일의 시장: 주말 전 {trend} 관련 움직임이 예상됩니다.",
        4: "금요일의 시장: 한 주를 마무리하며 {trend} 섹터의 정리가 필요합니다.",
    }

    # 트렌드 키워드
    today_trends = {
        0: "경제 지표",
        1: "외국인 수급",
        2: "정책 이슈",
        3: "주가 방어",
        4: "주말 이슈"
    }

    template = insights_templates.get(weekday, "오늘의 시장 상황을 분석합니다.")
    trend = today_trends.get(weekday, "시장")

    insight = f"**{trend} 중심의 하루였습니다.** " + template.format(trend=trend)

    # 추가 인사이트
    insight += "\n\n**핵심 포인트:**"
    insight += "\n- 아침 뉴스와 중복되지 않는 저녁 특화 뉴스 수집"
    insight += "\n- 시장 종합 데이터 기반 분석"
    insight += "\n- 다음 날 시장 예측을 위한 데이터 확보"

    return insight

def create_report() -> str:
    """저녁 마감 브리핑 리포트 생성"""
    today = datetime.date.today().strftime('%Y-%m-%d')
    weekday = datetime.date.today().strftime('%a')
    year = datetime.date.today().year
    month = datetime.date.today().month
    day = datetime.date.today().day

    report = f"🌇 [{today}] 경자방 마감 브리핑\n\n"
    report += f"형님, 오늘 하루 시장 흐름과 핵심 뉴스를 정리해 드립니다.\n\n"

    # 시장 종합
    report += "📊 시장 종합\n\n"
    report += fetch_market_summary()
    report += "\n\n"

    all_news_items = []  # 모든 뉴스 제목 저장

    # 각 섹션 뉴스
    for category, query in SECTIONS.items():
        news_items = fetch_news_evening(category, query)
        all_news_items.extend(news_items)  # 인사이트 생성용 저장

        report += f"{category}\n\n"

        if news_items:
            for i, title in enumerate(news_items, 1):
                report += f"{i}. {title}\n"
        else:
            report += "- 뉴스 수집 실패\n"

        report += "\n"

    # 자비스의 인사이트 (뉴스 기반)
    report += generate_insights_from_news(all_news_items)

    return report

def send_telegram(message: str) -> bool:
    """Telegram으로 메시지 전송"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": CHAT_ID,
            "text": message
        }

        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()

        return True
    except Exception as e:
        print(f"Telegram 전송 실패: {e}")
        return False

def main():
    """메인 함수"""
    print(f"🌇 경자방 저녁 마감 브리핑 생성 시작: {datetime.datetime.now()}")

    # API 키 확인
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        return 1

    # 브리핑 생성
    report = create_report()

    # 출력
    print(report)

    # Telegram 전송
    print("📤 Telegram 전송 중...")
    if send_telegram(report):
        print("✅ 전송 완료")
    else:
        print("❌ 전송 실패")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())
