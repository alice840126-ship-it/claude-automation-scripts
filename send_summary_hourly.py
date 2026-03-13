#!/usr/bin/env python3
"""
공인중개사 1차 상세 학습 내용 전송
- 에이전트가 추출한 상세 내용 기반
- 한 번에 개론 + 민법 둘 다 전송
- 40분마다 실행
"""

import json
import requests
from datetime import datetime
from pathlib import Path

TELEGRAM_BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
TELEGRAM_CHAT_ID = "756219914"
LOG_FILE = Path.home() / '.claude' / 'logs' / 'summary-hourly.log'
SENT_LOG = Path.home() / '.claude' / 'sent_summaries.jsonl'

# 에이전트가 추출한 상세 학습 자료
DATA_FILE = Path.home() / 'Desktop/0. 자비스/공인중개사/학습자료_완성.json'


def load_contents():
    """상세 학습 자료 로드"""
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 파일 로드 실패: {e}")
        return None


def log(msg: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {msg}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


def send_telegram(message: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        log(f"❌ 전송 실패: {e}")
        return False


def load_sent():
    sent = set()
    if SENT_LOG.exists():
        with open(SENT_LOG, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    sent.add(data['topic'])
                except:
                    pass
    return sent


def save_sent(topic: str):
    with open(SENT_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'topic': topic, 'time': datetime.now().isoformat()}) + '\n')


def select_contents(contents: dict, sent_topics: set):
    """개론, 민법 각각 선택"""
    # 개론
    gaeron_available = []
    for chapter, items in contents['개론'].items():
        key = f"개론 - {chapter[:30]}"
        if key not in sent_topics:
            gaeron_available.append((key, '개론', chapter, items))

    # 민법
    minbub_available = []
    for chapter, items in contents['민법'].items():
        key = f"민법 - {chapter[:30]}"
        if key not in sent_topics:
            minbub_available.append((key, '민법', chapter, items))

    # 모두 전송했으면 초기화
    if not gaeron_available:
        gaeron_available = [(f"개론 - {list(contents['개론'].keys())[0][:30]}",
                               '개론', list(contents['개론'].keys())[0],
                               contents['개론'][list(contents['개론'].keys())[0]])]
    if not minbub_available:
        minbub_available = [(f"민법 - {list(contents['민법'].keys())[0][:30]}",
                                '민법', list(contents['민법'].keys())[0],
                                contents['민법'][list(contents['민법'].keys())[0]])]

    # 순차적 선택
    import time
    idx_g = int(time.time() * 1000) % len(gaeron_available)
    idx_m = int(time.time() * 1000) % len(minbub_available)

    return gaeron_available[idx_g], minbub_available[idx_m]


def format_message(gaeron_data: tuple, minbub_data: tuple) -> str:
    now = datetime.now().strftime("%H:%M")
    message = f"📚 [{now}] 공인중개사 1차 상세 내용\n\n"

    # 개론
    message += f"## 📘 개론\n"
    message += f"### {gaeron_data[2][:80]}\n\n"

    # 상위 5개만 (메시지 길이 제한)
    for i, item in enumerate(gaeron_data[3][:5], 1):
        message += f"{i}. {item}\n"

    remaining = len(gaeron_data[3]) - 5
    if remaining > 0:
        message += f"\n(외 {remaining}개 더 있음)\n"

    message += "\n" + "─" * 30 + "\n\n"

    # 민법
    message += f"## 📕 민법\n"
    message += f"### {minbub_data[2][:80]}\n\n"

    for i, item in enumerate(minbub_data[3][:5], 1):
        message += f"{i}. {item}\n"

    remaining = len(minbub_data[3]) - 5
    if remaining > 0:
        message += f"\n(외 {remaining}개 더 있음)\n"

    message += f"\n💬 40분 뒤에 다음 주제!"

    return message


def main():
    log("🚀 상세 내용 전송 시작")

    contents = load_contents()
    if not contents:
        log("❌ 내용 로드 실패")
        return

    sent_topics = load_sent()
    gaeron_data, minbub_data = select_contents(contents, sent_topics)

    log(f"📘 개론: {gaeron_data[2][:50]}")
    log(f"📕 민법: {minbub_data[2][:50]}")

    message = format_message(gaeron_data, minbub_data)

    if send_telegram(message):
        log("✅ 전송 완료")
        save_sent(gaeron_data[0])
        save_sent(minbub_data[0])
    else:
        log("❌ 전송 실패")


if __name__ == "__main__":
    main()
