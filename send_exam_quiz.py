#!/usr/bin/env python3
"""
공인중개사 시험 문제 전송
- 개론 1문제, 민법 3문제
- 마크다운 파일에서 직접 추출
"""

import re
import random
import requests
from pathlib import Path
from datetime import datetime

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
GAERON_FILE = Path.home() / ".claude" / "data" / "exam" / "26년 개론 마크다운.md"
MINBUB_FILE = Path.home() / ".claude" / "data" / "exam" / "26 민법 마크다운.md"
LOG_FILE = Path.home() / ".claude" / "logs" / "exam-quiz.log"

def log(message):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}\n"
    print(log_msg.strip())
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg)

def load_gaeron_questions():
    """개론 문제 추출"""
    with open(GAERON_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    # **[회차] 로 시작하는 블록 찾기
    blocks = content.split('**[')[1:]  # 첫 번째는 비어있음

    questions = []
    for block in blocks:
        # 정답 라인 찾기
        if '* **정답:' in block:
            # 정답 라인까지 자르기
            parts = block.split('* **정답:')
            if len(parts) >= 2:
                question = '**[' + parts[0] + '* **정답:' + parts[1].split('\n')[0]
                questions.append(question)

    return questions

def load_minbub_questions():
    """민법 O/X 문제 추출"""
    with open(MINBUB_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions = []
    for line in lines:
        line = line.strip()
        # * **★★ 번호.** 로 시작하고 (O) 또는 (X)로 끝나는 라인
        if line.startswith('* **★★') and (line.endswith('(O)') or line.endswith('(X)')):
            questions.append(line)

    return questions

def format_quiz(gaeron_q, minbub_qs):
    """퀴즈 포맷팅"""
    message = f"📚 **{datetime.now().strftime('%H:%M')} 공인중개사 1차 문제**\n\n"

    # 개론 문제
    message += f"## 📘 개론 (1문제)\n\n"
    message += f"{gaeron_q}\n\n"

    # 민법 문제
    message += f"## 📕 민법 (3문제)\n\n"
    for i, q in enumerate(minbub_qs, 1):
        message += f"{i}. {q}\n"

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
    except Exception as e:
        log(f"❌ 전송 실패: {e}")

def main():
    """메인 실행"""
    log("🚀 공인중개사 문제 전송 시작")

    # 문제 로드
    gaeron_questions = load_gaeron_questions()
    minbub_questions = load_minbub_questions()

    log(f"📚 개론: {len(gaeron_questions)}개")
    log(f"📕 민법: {len(minbub_questions)}개")

    # 랜덤 선택
    gaeron_q = random.choice(gaeron_questions)
    minbub_qs = random.sample(minbub_questions, 3)

    # 주제 추출 (간단하게)
    gaeron_topic = "부동산학"
    if "감정" in gaeron_q:
        gaeron_topic = "감정평가론"
    elif "경제" in gaeron_q:
        gaeron_topic = "부동산경제론"

    minbub_topic = "민법총칙"
    if minbub_qs:
        if "물권" in minbub_qs[0]:
            minbub_topic = "물권법"
        elif "계약" in minbub_qs[0]:
            minbub_topic = "계약법"

    log(f"📘 개론: {gaeron_topic}")
    log(f"📕 민법: {minbub_topic}")

    # 포맷팅 & 전송
    message = format_quiz(gaeron_q, minbub_qs)
    send_to_telegram(message)

    log("✅ 완료")

if __name__ == "__main__":
    main()
