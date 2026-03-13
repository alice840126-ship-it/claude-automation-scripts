#!/usr/bin/env python3
"""
공인중개사 1차 퀴즈 전송 (1시간마다)
- 아침 9시부터 저녁 9시까지
- 개론 1문제 + 민법 1문제
"""

import json
import random
import requests
from datetime import datetime
from pathlib import Path

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"

QUESTION_DB = Path.home() / '.claude' / 'exam_questions_database.json'
LOG_FILE = Path.home() / '.claude' / 'logs' / 'quiz-hourly.log'
SENT_LOG = Path.home() / '.claude' / 'sent_questions.jsonl'


def log(message: str):
    """로그 기록"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


def send_telegram(message: str) -> bool:
    """텔레그램 전송"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        log(f"❌ 전송 실패: {e}")
        return False


def load_sent_ids():
    """이미 전송한 문제 ID 로드"""
    sent_ids = set()
    if SENT_LOG.exists():
        with open(SENT_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    sent_ids.add(data['id'])
                except:
                    pass
    return sent_ids


def save_sent_id(q_id: str):
    """전송한 문제 ID 저장"""
    with open(SENT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'id': q_id, 'time': datetime.now().isoformat()}) + '\n')


def load_questions():
    """문제 로드"""
    try:
        with open(QUESTION_DB, 'r', encoding='utf-8') as f:
            db = json.load(f)

        gaeron = db.get('개론', [])
        minbub = db.get('민법', [])

        log(f"📚 개론: {len(gaeron)}개, 민법: {len(minbub)}개")
        return gaeron, minbub

    except Exception as e:
        log(f"❌ 파일 로드 실패: {e}")
        return [], []


def select_random_question(questions: list, sent_ids: set) -> dict:
    """안 전송한 문제 중 랜덤 선택"""
    # 안 전송한 문제 필터링
    available = [q for q in questions if q['id'] not in sent_ids]

    if not available:
        # 모두 전송했으면 전체에서 선택
        available = questions

    return random.choice(available)


def format_quiz(gaeron_q: dict, minbub_q: dict) -> str:
    """퀴즈 포맷팅"""
    now = datetime.now().strftime("%H:%M")
    message = f"📚 [{now}] 공인중개사 1차 퀴즈\n\n"

    # 개론
    message += f"📘 개론\n"
    message += f"📌 {gaeron_q.get('topic', '')} | {gaeron_q.get('round', '')}\n\n"
    message += f"Q. {gaeron_q['question']}\n\n"
    for opt in gaeron_q['options']:
        message += f"{opt}\n"
    message += f"\n💡 정답: {gaeron_q.get('answer', '?')}번"
    if gaeron_q.get('explanation'):
        message += f"\n📝 {gaeron_q['explanation']}"

    message += "\n\n" + "─" * 30 + "\n\n"

    # 민법
    message += f"📕 민법\n"
    message += f"📌 {minbub_q.get('topic', '')} | {minbub_q.get('round', '')}\n\n"
    message += f"Q. {minbub_q['question']}\n\n"
    for opt in minbub_q['options']:
        message += f"{opt}\n"
    message += f"\n💡 정답: {minbub_q.get('answer', '?')}번"
    if minbub_q.get('explanation'):
        message += f"\n📝 {minbub_q['explanation']}"

    return message


def main():
    """메인 실행"""
    log("🚀 퀴즈 전송 시작")

    # 문제 로드
    gaeron, minbub = load_questions()

    if not gaeron or not minbub:
        log("❌ 문제 없음")
        return

    # 전송 기록 로드
    sent_ids = load_sent_ids()

    # 문제 선택
    gaeron_q = select_random_question(gaeron, sent_ids)
    minbub_q = select_random_question(minbub, sent_ids)

    log(f"📘 개론: {gaeron_q['id']} - {gaeron_q['topic']}")
    log(f"📕 민법: {minbub_q['id']} - {minbub_q['topic']}")

    # 포맷팅
    message = format_quiz(gaeron_q, minbub_q)

    # 전송
    if send_telegram(message):
        log("✅ 전송 완료")
        # 전송 기록 저장
        save_sent_id(gaeron_q['id'])
        save_sent_id(minbub_q['id'])
    else:
        log("❌ 전송 실패")


if __name__ == "__main__":
    main()
