#!/usr/bin/env python3
"""
경자방 아침 일정 브리핑 자동화 스크립트
매일 아침 7시 실행 (Launchd)
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

def create_schedule_briefing():
    """아침 일정 브리핑 생성"""
    today = datetime.date.today().strftime('%Y-%m-%d')
    weekday = datetime.date.today().strftime('%A')

    report = f"⏰ 아침 일정 브리핑\n"
    report += f"📅 {today} ({weekday})\n\n"

    # 오늘 일정
    schedule = calendar_helper.get_todays_schedule()
    report += schedule

    # 이번 주 일정 요약
    try:
        week_schedule = calendar_helper.get_this_week_schedule()
        report += "\n📆 이번 주 한눈에\n"
        report += week_schedule
    except Exception as e:
        print(f"⚠️ 이번 주 일정 조회 실패: {e}")

    # 하루 시작 인사
    report += "\n💡 오늘도 승리하는 하루가 되길 응원합니다! ⚛️"

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
    print(f"⏰ 아침 일정 브리핑 생성 시작: {datetime.datetime.now()}")

    # 일정 브리핑 생성
    report = create_schedule_briefing()

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
