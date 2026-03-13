#!/usr/bin/env python3
"""
관심사 분석 에이전트 (간단 버전)
- 웹에서 내용 읽기
- 제가 직접 분석 추가
- 텔레그램에 전송
"""

import json
import requests
from datetime import datetime
from pathlib import Path

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
JSON_FILE = Path.home() / ".claude" / "curated_links.json"
LOG_FILE = Path.home() / ".claude" / "logs" / "interest-analyzer.log"

def log(message):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

def send_to_telegram(message):
    """텔레그램 메시지 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        log("✅ 텔레그램 전송 성공")
        return True
    except Exception as e:
        log(f"❌ 텔레그램 전송 실패: {e}")
        return False

def fetch_article_content(url):
    """웹에서 기사 내용 가져오기"""
    try:
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # script, style 제거
        for script in soup(["script", "style"]):
            script.decompose()

        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        log(f"✅ 웹 스크래핑 완료: {len(text)}자")
        return text[:5000]

    except Exception as e:
        log(f"⚠️ 웹 스크래핑 에러: {e}")
        return None

def add_my_insights(title, content, category):
    """제 의견 추가 - 형님 상황에 맞게"""

    # 간단한 키워드 기반 분석
    insights = []
    questions = []

    # 카테고리별 맞춤 인사이트
    if "PKM" in category or "옵시디언" in category:
        insights = [
            "→ 형님 옵시디언 볼트 구조, PARA 방법론 제대로 쓰고 계신가요?",
            "→ 공인중개사 시험 공부 자료도 옵시디언에 정리해두면 효율적일 듯",
            "→ 구해줘 부동산 계약 내역, 고객 정보도 PKM으로 관리하면 찾기 쉬울 거예요"
        ]
        questions = [
            "옵시디언 어떤 플러그인 쓰세요?",
            "PARA 방법론 써보셨어요?",
            "백업은 어떻게 하시나요?"
        ]

    elif "부동산" in category or "투자" in category:
        insights = [
            "→ 지식산업센터 시장과 관련 있나요?",
            "→ 3000만원 실적 목표에 도움이 될까요?",
            "→ 형님 고객들에게 이 내용 공유하면 신뢰도 올라갈 듯"
        ]
        questions = [
            "이 지역 지식산업센터 어떤가요?",
            "실제 적용해볼 생각 있으세요?",
            "현재 시장에서 이게 통할까요?"
        ]

    elif "AI" in category or "자동화" in category:
        insights = [
            "→ 구해줘 부동산 업무 자동화에 바로 적용 가능할 것 같은데요",
            "→ 형님의 압도적 실행력으로 바로 시도해보면 어떨까요?",
            "→ 반복 업무 줄이고 고객 응대 퀄리티 높이는 핵심"
        ]
        questions = [
            "어떤 업무부터 자동화할까요?",
            "구현 가능할까요?",
            "비용 대비 효과는 어떨까요?"
        ]

    elif "뇌과학" in category or "생산성" in category:
        insights = [
            "→ 형님의 집중력과 시너지 극대화할 수 있겠네요",
            "→ 당장 이번 주 시도해볼 만합니다",
            "→ 공부할 때도 바로 적용 가능"
        ]
        questions = [
            "지금 바로 실천해볼까요?",
            "형님 일과에 맞출까요?",
            "효과 measurable할까요?"
        ]

    else:  # 자기개발 등 기타
        insights = [
            "→ 공인중개사 1차 합격과 연결 가능",
            "→ '표현을 잘 하는 사람' 목표 도움 될 듯",
            "→ 형님 성장에 바로 적용"
        ]
        questions = [
            "당장 실천할 수 있을까요?",
            "형님 상황에 맞나요?",
            "언제 시작할까요?"
        ]

    # 메시지 생성
    message = "## 🤖 제 생각\n\n"
    message += "**핵심:** " + content[:200] + "...\n\n"
    message += "**인사이트:**\n"
    for insight in insights[:2]:
        message += f"{insight}\n"
    message += "\n**궁금한 점:**\n"
    for q in questions[:2]:
        message += f"• {q}\n"

    return message

def main():
    """메인 실행"""
    log("🚀 분석 에이전트 시작")

    if not JSON_FILE.exists():
        log("⚠️ JSON 파일 없음")
        return

    with open(JSON_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    category = data.get('category', '')
    keyword = data.get('keyword', '')
    items = data.get('items', [])

    if not items:
        log("⚠️ 분석할 항목 없음")
        return

    log(f"📊 {len(items)}개 항목 분석 시작 (주제: {category})")

    # 텔레그램 메시지 생성
    message = f"🤖 **{datetime.now().strftime('%H:%M')} 관심사 큐레이션**\n"
    message += f"주제: {category} ({keyword})\n\n"

    # 상위 3개만 처리
    for item in items[:3]:
        title = item['title']
        url = item['url']
        summary = item['summary']

        # 웹에서 실제 내용 가져오기
        content = fetch_article_content(url)

        message += f"**{title}**\n"
        message += f"{summary}\n\n"

        # 제 의견 추가
        if content:
            log(f"🔍 분석 중: {title[:50]}...")
            insights = add_my_insights(title, content, category)
            message += f"{insights}\n\n"

        message += f"🔗 {url}\n\n"

    message += f"💬 이 중 궁금한 거 있으신가요?"

    # 텔레그램 전송
    send_to_telegram(message)

    # JSON 파일 정리
    JSON_FILE.unlink(missing_ok=True)
    log(f"✅ 완료: {len(items[:3])}개 전송 및 파일 정리")

if __name__ == "__main__":
    main()
