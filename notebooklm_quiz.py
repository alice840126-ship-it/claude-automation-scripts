#!/usr/bin/env python3
"""
공인중개사 1차 문제 자동 전송 (NotebookLM 활용)
- 아침 9시 ~ 저녁 6시까지 80분 간격
- 매 회차: 민법 1문제 + 개론 1문제 (총 2문제)
- NotebookLM으로 문제 생성
"""

import subprocess
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
NOTEBOOK_ID = "6a1a4c9d"  # 공인중개사 1차 자료
LOG_FILE = Path.home() / ".claude" / "logs" / "notebooklm-quiz.log"

# 시간대별 회차 (09:00 ~ 17:00, 80분 간격)
SCHEDULE = [
    (9, 0, 1),    # 09:00 회차1
    (10, 20, 2),  # 10:20 회차2
    (11, 40, 3),  # 11:40 회차3
    (13, 0, 4),   # 13:00 회차4
    (14, 20, 5),  # 14:20 회차5
    (15, 40, 6),  # 15:40 회차6
    (17, 0, 7),   # 17:00 회차6
]

def log(message):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg.strip())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg)

def get_current_round():
    """현재 시간 기준으로 회차 반환"""
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute

    for hour, minute, round_num in SCHEDULE:
        if current_hour == hour and abs(current_minute - minute) <= 5:
            return round_num

    return None

import re

def parse_notebooklm_output(output):
    """NotebookLM 출력에서 불필요한 부분 제거"""
    if not output:
        return None

    # "Answer:" 다음부터 추출
    if "Answer:" in output:
        output = output.split("Answer:", 1)[1]

    # "Resumed conversation" 또는 "Conversation:" 이전까지 추출
    for marker in ["Resumed conversation:", "Conversation:", "Continuing conversation"]:
        if marker in output:
            output = output.split(marker)[0]

    # 불필요한 접두사 제거
    lines = output.strip().split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not line.startswith('Continuing') and not line.startswith('Answer'):
            # 줄 끝의 참고문헌 번호 제거 (예: "1", " 1", "[1]")
            line = re.sub(r'\s+\d+$', '', line)
            line = re.sub(r'\s+\[\d+\]$', '', line)
            cleaned_lines.append(line)

    return '\n'.join(cleaned_lines)

def ask_notebooklm(question):
    """NotebookLM에 질문 (현재 선택된 노트북 사용)"""
    try:
        cmd = ["python3", "-m", "notebooklm", "ask", question]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            log(f"❌ NotebookLM CLI 오류: {result.stderr}")
            return None

        return parse_notebooklm_output(result.stdout)
    except subprocess.TimeoutExpired:
        log(f"❌ NotebookLM 타임아웃 (120초 초과)")
        return None
    except Exception as e:
        log(f"❌ NotebookLM 오류: {e}")
        return None

def generate_quiz():
    """민법 1문제 + 개론 1문제 생성"""
    quizzes = {}

    # 민법 문제 - 기출문제 PDF만 참고
    log("📚 민법 문제 생성 중...")
    minbub_prompt = ("'김덕수 기출문제(민법) - 완성.ocr.pdf.pdf' 파일만 참고해서 객관식 문제 1개를 내줘. "
                     "다른 소스는 참고하지 말고 오직 이 PDF의 기출문제만 사용해줘. "
                     "난이도는 다양하게(하급, 중급, 상급 섞어서) 랜덤으로 출제해줘. "
                     "정답과 해설도 포함해줘. "
                     "형식: 문제, 보기 ①~⑤, 정답, 해설")
    quizzes['민법'] = ask_notebooklm(minbub_prompt)

    # 개론 문제 - 기출문제 PDF만 참고
    log("📚 개론 문제 생성 중...")
    gaeron_prompt = ("'김백중 기출문제(부동산학개론) - 완성.ocr.pdf.pdf' 파일만 참고해서 객관식 문제 1개를 내줘. "
                     "다른 소스는 참고하지 말고 오직 이 PDF의 기출문제만 사용해줘. "
                     "난이도는 다양하게(하급, 중급, 상급 섞어서) 랜덤으로 출제해줘. "
                     "정답과 해설도 포함해줘. "
                     "형식: 문제, 보기 ①~⑤, 정답, 해설")
    quizzes['개론'] = ask_notebooklm(gaeron_prompt)

    return quizzes

def format_message(round_num, quizzes):
    """텔레그램 메시지 포맷팅"""
    time_str = datetime.now().strftime("%H:%M")
    message = f"📚 **{time_str} 공인중개사 1차 문제 (회차 {round_num})**\n\n"

    # 민법
    message += f"## 📕 민법\n\n"
    message += quizzes.get('민법', '❌ 문제 생성 실패')
    message += "\n\n"

    # 개론
    message += f"## 📘 개론\n\n"
    message += quizzes.get('개론', '❌ 문제 생성 실패')

    return message

def send_to_telegram(message):
    """텔레그램 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=data, timeout=30)
        log("✅ 텔레그램 전송 완료")
        return True
    except Exception as e:
        log(f"❌ 전송 실패: {e}")
        return False

def init_notebook():
    """노트북 컨텍스트 초기화"""
    try:
        cmd = ["python3", "-m", "notebooklm", "use", NOTEBOOK_ID]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log(f"✅ 노트북 선택 완료: {NOTEBOOK_ID}")
            return True
        else:
            log(f"❌ 노트북 선택 실패: {result.stderr}")
            return False
    except Exception as e:
        log(f"❌ 노트북 초기화 오류: {e}")
        return False

def analyze_weak_points():
    """약점 진단 (주 1회)"""
    # 일요일 18:00에 실행
    now = datetime.now()
    if now.weekday() != 6:  # 0=월, 6=일
        return False

    if now.hour != 18 or now.minute != 0:
        return False

    log("📊 주간 약점 진단 시작...")
    prompt = ("공인중개사 1차 시험 준비 현황을 분석해서 "
              "1) 약점 과목/주제, 2) 학습 우선순위, 3) 이번 주 집중 공부 추천"
              "을 정리해줘")

    result = ask_notebooklm(prompt)
    if result:
        message = f"📊 **주간 약점 진단 ({now.strftime('%Y-%m-%d')})**\n\n{result}"
        send_to_telegram(message)
        return True

    return False

def main():
    """메인 실행"""
    log("=" * 50)
    log("🚀 NotebookLM 퀴즈 시작")

    # 노트북 초기화
    if not init_notebook():
        log("❌ 노트북 초기화 실패로 종료")
        return

    # 약점 진단 체크
    if analyze_weak_points():
        log("✅ 약점 진단 완료")
        return

    # 회차 확인
    round_num = get_current_round()
    if not round_num:
        log("⏰ 예약된 시간이 아님")
        return

    log(f"📚 회차 {round_num}: 민법 + 개론")

    # 문제 생성 (민법 1 + 개론 1)
    quizzes = generate_quiz()

    if not quizzes.get('민법') and not quizzes.get('개론'):
        log("❌ 문제 생성 실패")
        return

    # 메시지 포맷팅 & 전송
    message = format_message(round_num, quizzes)
    send_to_telegram(message)

    log("✅ 완료")

if __name__ == "__main__":
    main()
