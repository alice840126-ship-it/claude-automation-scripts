#!/usr/bin/env python3
"""
경자방 아침 뉴스 자동화 스크립트 (네이버 API 버전)
매일 아침 7시 실행 (Launchd)
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

# 섹션별 검색어
SECTIONS = {
    "🏘 부동산": "부동산 경매 아파트 분양",
    "🏭 산업/건설": "AI 반도체 데이터센터 건설",
    "💰 금융/기업": "금융 주식 코스피 코스닥",
    "🏡 주거/트렌드": "스마트홈 IoT 주거"
}

def fetch_news_naver(category: str, query: str) -> list[str]:
    """네이버 검색 API에서 뉴스 제목 수집"""
    try:
        # 네이버 검색 API 호출
        url = "https://openapi.naver.com/v1/search/news.json"

        headers = {
            "X-Naver-Client-Id": NAVER_CLIENT_ID,
            "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
        }

        params = {
            "query": query,
            "display": 5,  # 5개 결과
            "sort": "date"  # 최신순
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        items = data.get('items', [])

        news_items = []
        for item in items:
            title = item.get('title', '')
            # HTML 태그 제거 및 디코딩
            title = html.unescape(title)
            title = re.sub(r'<[^>]+>', '', title)
            # HTML 엔티티 정리
            title = title.replace('&quot;', '"').replace('&amp;', '&')
            # 대괄호 등 정리
            title = re.sub(r'\[.*?\]', '', title)
            title = title.strip()

            if len(title) > 10:
                news_items.append(title)

        return news_items

    except Exception as e:
        print(f"Error fetching {category}: {e}")
        return []

def create_report() -> str:
    """뉴스 리포트 생성"""
    today = datetime.date.today().strftime('%Y-%m-%d')

    report = f"⚛️ 경자방 아침 뉴스 리포트 ({today})\n\n"

    all_news_items = []  # 모든 뉴스 제목 저장

    for category, query in SECTIONS.items():
        news_items = fetch_news_naver(category, query)
        all_news_items.extend(news_items)  # 인사이트 생성용 저장

        report += f"{category}\n\n"

        if news_items:
            for i, title in enumerate(news_items, 1):
                report += f"{i}. {title}\n"
        else:
            report += "- 뉴스 수집 실패\n"

        report += "\n"

    # AI 인사이트 생성
    report += generate_insights(all_news_items)

    report += "\n오늘도 형님의 승리하는 하루를 응원합니다! ⚛️"

    return report

def generate_insights(news_items: list[str]) -> str:
    """뉴스 키워드 기반 인사이트 생성"""
    all_titles = " ".join(news_items)

    insights = []
    insight = "💡 자비스의 한 줄 통찰\n"

    # 키워드 분석
    keywords = {
        "부동산_상승": ["상승", "오름", "급등", "반등", "회복"],
        "부동산_하락": ["하락", "하락세", "조정", "하락마감"],
        "금리": ["금리", "기준금리", "채권", "연준"],
        "AI": ["AI", "인공지능", "ChatGPT", "삼성전자"],
        "수도권_물류": ["물류", "산업단지", "지식산업센터", "창고"],
        "투자": ["투자", "분양", "청약", "재테크"]
    }

    detected = []

    # 키워드 매칭
    if any(k in all_titles for k in keywords["부동산_상승"]):
        detected.append("부동산 시세 회복세")

    if any(k in all_titles for k in keywords["부동산_하락"]):
        detected.append("부동산 시세 조정")

    if any(k in all_titles for k in keywords["금리"]):
        detected.append("금리 관련 뉴스")

    if any(k in all_titles for k in keywords["AI"]):
        detected.append("AI/반도체 이슈")

    if any(k in all_titles for k in keywords["수도권_물류"]):
        detected.append("수도권 물류/산단 동향")

    if any(k in all_titles for k in keywords["투자"]):
        detected.append("투자/분양 기회")

    # 인사이트 문장 생성
    if "부동산 시세 회복세" in detected:
        insights.append("• 부동산 회복신호? 지식산업센터 매물 시장 점검 필요")

    if "부동산 시세 조정" in detected:
        insights.append("• 조정 시장일수록 좋은 매물 찾을 기회. 임대수요 확인하세요")

    if "금리 관련 뉴스" in detected:
        insights.append("• 금리 변동 폭 크면 대출 상환 계획 점검")

    if "AI/반도체 이슈" in detected:
        insights.append("• AI 이슈 뜨겁네요. 관련 기업 입주 물량 체크해보세요")

    if "수도권 물류/산단 동향" in detected:
        insights.append("• 수도권 산단 동향 변화 있네요. 덕은지역 임대수요 영향 있을지")

    if "투자/분양 기회" in detected:
        insights.append("• 분양 기업 관련해 신규 투자 기회 있는지 확인")

    if not insights:
        insights.append("• 오늘 뉴스는 평온합니다. 꾸준히 모니터링만 하세요")

    insight += "\n".join(insights) + "\n"

    return insight

def main():

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
    print(f"📰 경자방 아침 뉴스 수집 시작: {datetime.datetime.now()}")

    # API 키 확인
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("❌ 네이버 API 키가 설정되지 않았습니다.")
        print("📝 .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET를 설정해주세요.")
        return 1

    # 뉴스 리포트 생성
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
