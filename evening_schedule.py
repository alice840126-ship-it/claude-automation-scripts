#!/usr/bin/env python3
"""
경자방 저녁 내일 일정 브리핑 자동화 스크립트
매일 저녁 6시 실행 (Launchd)
"""

import os
import sys
import requests
import datetime
from dotenv import load_dotenv

# calendar_helper 모듈 추가
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
import calendar_helper

# 환경 변수 로드
load_dotenv(os.path.join(SCRIPT_DIR, '.env'))

# 설정
BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
CHAT_ID = "756219914"

def create_tomorrow_briefing():
    """내일 일정 브리핑 생성"""
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    weekday = (datetime.date.today() + datetime.timedelta(days=1)).strftime('%A')

    report = f"🌙 내일 일정 미리보기\n"
    report += f"📅 {tomorrow} ({weekday})\n\n"

    # 내일 일정
    schedule = calendar_helper.get_tomorrows_schedule()
    report += schedule

    # 퇴근 인사
    report += "\n💡 오늘 하루도 고생 많으셨습니다! 내일도 화이팅! ⚛️"

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
    print(f"🌙 내일 일정 브리핑 생성 시작: {datetime.datetime.now()}")

    # 내일 일정 브리핑 생성
    report = create_tomorrow_briefing()

    # 출력
    print(report)

    # Telegram 전송
    print("📤 Telegram 전송 중...")
    if send_telegram(report):
        print("✅ 전송 완료")
        return 0
    else:
        print("❌ 전송 실패")
        return 1

if __name__ == "__main__":
    exit(main())
