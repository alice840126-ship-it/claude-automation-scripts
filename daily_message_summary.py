#!/usr/bin/env python3
"""
데일리 문자 메시지 요약 스크립트
매일 저녁 5시 실행 (Launchd)
"""

import os
import sqlite3
import datetime
import re
from pathlib import Path
from dotenv import load_dotenv

# 설정
MESSAGES_DB = os.path.expanduser("~/Library/Messages/chat.db")
BOT_TOKEN = "8526946005:AAHNkyee8mIAu_7R8tSh017mphjbX5SdRfE"
CHAT_ID = "756219914"

# Apple 날짜 포맷: 2001년 1월 1일부터의 초 (NSTimeInterval)
APPLE_EPOCH = 978307200

def apple_date_to_unix(apple_date):
    """Apple NSDate를 Unix timestamp로 변환"""
    if apple_date is None or apple_date == 0:
        return 0
    return int(apple_date + APPLE_EPOCH)

def get_today_messages():
    """오늘의 문자 메시지 조회"""
    if not os.path.exists(MESSAGES_DB):
        print("❌ Messages DB를 찾을 수 없습니다")
        return []

    try:
        # DB 잠금 해결을 위해 복사본 사용
        import shutil
        db_copy = "/tmp/chat.db.copy"
        shutil.copy2(MESSAGES_DB, db_copy)

        conn = sqlite3.connect(db_copy)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 오늘 00:00:00의 Unix timestamp
        today_start_ts = int(datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        now_ts = int(datetime.datetime.now().timestamp())

        # Unix timestamp를 Apple NSDate로 변환 (nanosecond)
        # Apple NSDate = (Unix timestamp - Apple epoch) * 10^9
        today_start_apple = (today_start_ts - APPLE_EPOCH) * 1000000000
        now_apple = (now_ts - APPLE_EPOCH) * 1000000000

        # 오늘의 메시지 조회 (시스템 메시지만 제외)
        query = """
        SELECT
            m.text,
            m.attributedBody,
            m.date,
            m.is_from_me,
            h.id as phone_number,
            c.chat_identifier,
            c.display_name
        FROM message m
        JOIN handle h ON m.handle_id = h.ROWID
        LEFT JOIN chat_message_join cmj ON m.ROWID = cmj.message_id
        LEFT JOIN chat c ON cmj.chat_id = c.ROWID
        WHERE m.date >= ? AND m.date <= ?
            AND m.is_system_message = 0
        ORDER BY m.date DESC
        """

        cursor.execute(query, (today_start_apple, now_apple))
        all_messages = cursor.fetchall()

        # attributedBody에서 한글 텍스트 추출
        decoded_messages = []
        for msg in all_messages:
            text = msg['text']
            attributed_body = msg['attributedBody']

            # text가 있으면 그대로 사용
            if text and text.strip():
                msg_dict = dict(msg)
                decoded_messages.append(msg_dict)
            # text가 없고 attributedBody가 있으면 추출 시도
            elif attributed_body:
                try:
                    # UTF-8로 디코딩해서 한글만 추출
                    decoded = attributed_body.decode('utf-8', errors='ignore')
                    # 모든 한글 부분 찾기 (1글자 이상)
                    korean_parts = re.findall(r'[가-힣]+', decoded)
                    if korean_parts:
                        # 공백으로 구분해서 띄어쓰기 추가
                        extracted_text = ' '.join(korean_parts)
                        msg_dict = dict(msg)
                        msg_dict['text'] = extracted_text

                        # 광고 필터링 (메시지 내용으로도 체크)
                        if not is_ad_message(extracted_text):
                            decoded_messages.append(msg_dict)
                except Exception as e:
                    pass  # 추출 실패하면 스킵

        all_messages = decoded_messages

        conn.close()
        os.remove(db_copy)

        # Web발신/광고 필터링
        filtered_messages = []
        for msg in all_messages:
            phone = msg['phone_number'] or msg['chat_identifier'] or ''
            if not is_spam_or_web_sender(phone):
                filtered_messages.append(msg)

        return filtered_messages

    except Exception as e:
        print(f"❌ 메시지 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return []

def is_ad_message(text):
    """광고 메시지인지 확인 (내용 기반)"""
    if not text:
        return False

    # "발신"으로 시작하는 건 광고성 안내
    if text.startswith("발신"):
        return True

    # 시스템/자동 안내 메시지
    system_keywords = [
        "휴대폰번호보호",
        "간편본인확인",
        "인증시도",
        "발생내역확인",
    ]

    # 광고 키워드
    ad_keywords = [
        "무료 수신 거부",
        "수신거부",
        "진흥협회",
        "매매를광업",
        "금선물거래",
        "국세환급금",
        "소득공제",
        "할인우대",
        "상담신청",
        "신청하세요",
        "상담전화",
        "고객센터",
        "문의 바랍니다",
        "무료이벤트",
        "할인혜택",
        "필요없는상품을권하지",
    ]

    # 시스템 메시지 체크
    for keyword in system_keywords:
        if keyword in text:
            return True

    # 광고 메시지 체크
    for keyword in ad_keywords:
        if keyword in text:
            return True

    return False

def is_spam_or_web_sender(phone):
    """Web발신 또는 광고 번호인지 확인"""
    if not phone:
        return False

    # 이메일은 제외하지 않음
    if '@' in phone:
        return False

    import re

    # 원본 전화번호 유지
    original_phone = phone

    # 국가 코드 제거
    clean_phone = re.sub(r'[^\d+]', '', phone)

    # +82 또는 82 제거 후 0 추가
    if clean_phone.startswith('+82'):
        clean_phone = '0' + clean_phone[3:]
    elif clean_phone.startswith('82') and len(clean_phone) > 10:
        clean_phone = '0' + clean_phone[2:]
    else:
        clean_phone = original_phone.replace('+', '').replace('-', '')

    # 길이에 따라 처리
    phone_len = len(clean_phone)

    # 10자리: 01X... (앞 0이 빠진 경우)
    if phone_len == 10 and clean_phone[0] != '0':
        clean_phone = '0' + clean_phone
    # 11자리: 01X... 또는 지역번호
    elif phone_len == 11:
        if clean_phone[0] != '0':
            # 지역번호일 수 있음 (예: 234899550 → 0234899550)
            clean_phone = '0' + clean_phone

    # Web발신/광고 번호 패턴
    spam_patterns = [
        r'^050',   # 050으로 시작 (Web발신)
        r'^060',   # 060으로 시작
        r'^070',   # 070으로 시작 (인터넷 전화, Web발신)
        r'^080',   # 080으로 시작 (수신자 부담, 광고)
        r'^1544',  # 1544로 시작 (대표번호, 광고)
        r'^1577',  # 1577로 시작 (대표번호, 700으로 6.5cm 광고)
        r'^1588',  # 1588로 시작 (대표번호, 700으로 6.5cm 광고)
        r'^1599',  # 1599로 시작 (대표번호, 700으로 6.5cm 광고)
        r'^1644',  # 1644로 시작 (대표번호, 광고)
        r'^1661',  # 1661로 시작 (대표번호, 광고)
        r'^1688',  # 1688로 시작 (대표번호)
        r'^1666',  # 1666로 시작
        r'^1833',  # 1833으로 시작 (모바일 광고)
        r'^1600',   # 1600으로 시작 (대표번호)
        r'^1611',   # 1611로 시작 (대표번호)
        r'^1666',   # 1666으로 시작 (대표번호)
        r'^1800',   # 1800으로 시작 (대표번호)
        r'^1822',   # 1822로 시작 (대표번호)
        r'^1577',   # 1577로 시작 (대표번호)
        r'^1899',   # 1899로 시작 (대표번호)
        r'^1644',   # 1644로 시작 (대표번호, 광고)
        r'^1650',   # 1650으로 시작 (대표번호)
        r'^1666',   # 1666으로 시작 (대표번호)
        r'^1577',   # 1577로 시작 (대표번호)
        r'^1633',   # 1633으로 시작 (대표번호)
        r'^1688',   # 1688로 시작 (대표번호)
        r'^1833',   # 1833으로 시작 (모바일 광고)
        r'^0303',   # 0303으로 시작 (자동응답 광고)
        r'^0300',   # 0300으로 시작
        r'^070',    # 070으로 시작 (인터넷 전화, Web발신)
        r'^050',    # 050으로 시작 (Web발신)
        r'^080',    # 080으로 시작 (수신자 부담, 광고)
        r'^1544',   # 1544로 시작 (대표번호, 광고)
        r'^1577',   # 1577로 시작 (대표번호, 광고)
        r'^1588',   # 1588로 시작 (대표번호, 광고)
        r'^1599',   # 1599로 시작 (대표번호, 광고)
        r'^1644',   # 1644로 시작 (대표번호, 광고)
        r'^1661',   # 1661로 시작 (대표번호, 광고)
        r'^1666',   # 1666으로 시작 (대표번호)
        r'^1688',   # 1688로 시작 (대표번호)
        r'^1833',   # 1833으로 시작 (모바일 광고)
    ]

    # 패턴 매칭
    for pattern in spam_patterns:
        if re.match(pattern, clean_phone):
            return True

    # 국제 번호 중 광고성 번호들 (+1로 시작하는 미국 번호 등)
    if original_phone.startswith('+1') and not original_phone.startswith('+82'):
        return True

    return False

def format_phone_number(phone):
    """전화번호 포맷팅 (010-xxxx-xxxx 형식)"""
    if not phone:
        return "알 수 없음"

    # 이메일인 경우 그대로 반환
    if '@' in phone:
        return phone

    # - 제거
    phone = phone.replace('-', '')

    # 국가 코드 처리 (+82 → 0)
    if phone.startswith('+82'):
        phone = '0' + phone[3:]
    elif phone.startswith('82') and len(phone) > 10:
        phone = '0' + phone[2:]

    # 010-xxxx-xxxx 형식으로 포맷
    if len(phone) == 11 and phone.startswith('010'):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    elif len(phone) == 11 and phone.startswith('0'):
        return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"{phone[:3]}-{phone[3:6]}-{phone[6:]}"

    return phone

def get_contact_name_from_phone(phone):
    """macOS AddressBook DB에서 전화번호로 이름 조회 (모든 소스 검색)"""
    if not phone or '@' in phone:
        return None

    try:
        import sqlite3
        import re
        import glob

        # 전화번호 정리 (원본 유지)
        original_phone = re.sub(r'[^\d+]', '', phone)

        # 여러 형식 생성
        phone_variants = []

        # 1. 원본 그대로
        phone_variants.append(original_phone)

        # 2. +82 제거 후 0 추가
        if original_phone.startswith('+82'):
            phone_no_code = '0' + original_phone[3:]
            phone_variants.append(phone_no_code)
        elif original_phone.startswith('82') and len(original_phone) > 10:
            phone_no_code = '0' + original_phone[2:]
            phone_variants.append(phone_no_code)

        # 3. Messages DB에서 앞의 0이 빠진 경우 처리 (1051059055 → 01051059055)
        if original_phone.startswith('1') and len(original_phone) == 10:
            phone_with_zero = '0' + original_phone
            phone_variants.append(phone_with_zero)

        # 4. 각 변형에 대해 하이픈 있는 버전도 추가
        with_dash_variants = []
        for p in phone_variants:
            if len(p) == 11 and p.startswith('010'):
                with_dash_variants.append(f"{p[:3]}-{p[3:7]}-{p[7:]}")
            elif len(p) == 10:
                with_dash_variants.append(f"{p[:3]}-{p[3:6]}-{p[6:]}")

        phone_variants.extend(with_dash_variants)

        # 중복 제거
        phone_variants = list(set(phone_variants))

        # 모든 AddressBook 소스 경로
        sources_base = os.path.expanduser("~/Library/Application Support/AddressBook/Sources")
        db_paths = glob.glob(os.path.join(sources_base, "*/AddressBook-v22.abcddb"))

        # 메인 DB도 추가
        main_db = os.path.expanduser("~/Library/Application Support/AddressBook/AddressBook-v22.abcddb")
        if os.path.exists(main_db):
            db_paths.append(main_db)

        # 각 DB에서 검색
        for db_path in db_paths:
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                for phone_variant in phone_variants:
                    query = """
                    SELECT ZFIRSTNAME, ZLASTNAME, ZNAME
                    FROM ZABCDRECORD
                    WHERE Z_PK IN (
                        SELECT ZOWNER FROM ZABCDPHONENUMBER
                        WHERE ZFULLNUMBER = ?
                    )
                    LIMIT 1
                    """

                    cursor.execute(query, (phone_variant,))
                    result = cursor.fetchone()

                    if result:
                        conn.close()

                        # 이름 조합
                        first_name = result['ZFIRSTNAME'] or ''
                        last_name = result['ZLASTNAME'] or ''
                        full_name = result['ZNAME'] or ''

                        if first_name or last_name:
                            return f"{last_name}{first_name}".strip()
                        elif full_name:
                            return full_name

                conn.close()

            except Exception as e:
                continue  # 다음 DB로 시도

    except Exception as e:
        print(f"연락처 조회 실패: {e}")

    return None

def extract_name_from_messages(messages):
    """메시지 내용에서 이름 추출"""
    import re
    name_count = {}

    for msg in messages:
        text = msg.get('text')
        if not text or text == '[사진 또는 첨부파일]':
            continue

        # "입니다" 패턴 (예: "김철수입니다", "홍길동입니다~")
        matches = re.findall(r'([가-힣]{2,4})입니다', text)
        for name in matches:
            # 성+이름으로 된 2~4글자 한글 이름
            if name not in ['안녕', '감사', '죄송', '수고', '행복', '좋은', '올해']:
                name_count[name] = name_count.get(name, 0) + 1

        # "입니다~" 패턴
        matches = re.findall(r'([가-힣]{2,4})입니다~', text)
        for name in matches:
            if name not in ['안녕', '감사', '죄송', '수고', '행복', '좋은', '올해']:
                name_count[name] = name_count.get(name, 0) + 1

    # 가장 자주 나온 이름 반환
    if name_count:
        return max(name_count.items(), key=lambda x: x[1])[0]

    return None

def create_summary(messages):
    """메시지 요약 생성"""
    if not messages:
        return "📱 오늘 주고받은 문자가 없습니다."

    # 사람별로 시간 순서대로 그룹화
    by_person = {}
    for msg in messages:
        # text 처리: None이면 '[메시지]', 빈 문자열이면 제외
        if msg['text'] is None:
            text = '[메시지]'
        elif not msg['text'].strip():
            continue
        else:
            text = msg['text']

        is_from_me = msg['is_from_me']
        date_val = msg['date']

        # 연락처 식별 (원본 전화번호 보관)
        raw_phone = msg['phone_number'] or msg['chat_identifier'] or ''
        if not raw_phone:
            continue

        if raw_phone not in by_person:
            by_person[raw_phone] = []

        # 시간 변환 (Apple NSDate → Unix timestamp)
        unix_ts = date_val / 1000000000 + APPLE_EPOCH
        msg_time = datetime.datetime.fromtimestamp(unix_ts)

        by_person[raw_phone].append({
            'time': msg_time,
            'text': text,
            'is_from_me': is_from_me
        })

    # 시간 순서대로 정렬 (오래된 순)
    for person in by_person:
        by_person[person].sort(key=lambda x: x['time'])

    # 요약 생성
    today = datetime.date.today().strftime('%Y-%m-%d')
    summary = f"📱 [{today}] 문자 메시지 요약\n\n"

    total_count = len(messages)
    total_people = len(by_person)
    summary += f"총 {total_count}개의 메시지, {total_people}명과 대화\n\n"
    summary += "=" * 50 + "\n\n"

    # 사람별 대화 표시
    for raw_phone, convos in sorted(by_person.items()):
        # 전화번호 포맷팅
        formatted_phone = format_phone_number(raw_phone)

        # 연락처에서 이름 조회 (1순위)
        name = get_contact_name_from_phone(raw_phone)

        # 연락처에 없으면 문자 내용에서 추출 (2순위)
        if not name:
            name = extract_name_from_messages(convos)

        # 이름 표시
        if name:
            display_name = f"{name} ({formatted_phone})"
        else:
            display_name = formatted_phone

        msg_count = len(convos)
        summary += f"👤 {display_name}\n"

        # 대화를 시간 순서대로 표시
        for msg in convos:
            time_str = msg['time'].strftime('%H:%M')
            if msg['is_from_me']:
                # 내가 보낸 메시지 (볼드체)
                prefix = "▶ **보냄**"
            else:
                # 받은 메시지 (일반 텍스트)
                prefix = "▷ 받음"

            text = msg['text'].replace('\n', ' ')  # 줄바꿈 처리

            summary += f"\n[{time_str}] {prefix}\n{text}\n"

        summary += "\n" + "-" * 50 + "\n\n"

    return summary

def send_telegram(message):
    """Telegram으로 메시지 전송 (긴 메시지는 분할 전송)"""
    try:
        import requests

        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        max_length = 4000  # 안전하게 4000자로 제한

        # 메시지가 길면 분할
        if len(message) <= max_length:
            # 한 번에 전송
            data = {
                "chat_id": CHAT_ID,
                "text": message
            }
            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()
        else:
            # 여러 부분으로 나눠서 전송
            messages = []
            current_message = ""
            lines = message.split('\n')

            for line in lines:
                # 현재 메시지에 이 줄을 추가했을 때 길이 체크
                test_message = current_message + "\n" + line if current_message else line

                if len(test_message) > max_length:
                    # 현재 메시지 전송하고 새로 시작
                    if current_message:
                        messages.append(current_message)
                    current_message = line
                else:
                    current_message = test_message

            # 마지막 메시지 추가
            if current_message:
                messages.append(current_message)

            # 순차적으로 전송
            for i, msg in enumerate(messages, 1):
                print(f"📤 전송 중... ({i}/{len(messages)})")
                data = {
                    "chat_id": CHAT_ID,
                    "text": msg
                }
                response = requests.post(url, data=data, timeout=10)
                response.raise_for_status()

        return True
    except Exception as e:
        print(f"❌ Telegram 전송 실패: {e}")
        return False

def main():
    """메인 함수"""
    print(f"📱 문자 요약 생성 시작: {datetime.datetime.now()}")

    # 오늘 메시지 조회
    messages = get_today_messages()

    # 요약 생성
    summary = create_summary(messages)

    # 출력
    print(summary)

    # Telegram 전송
    print("📤 Telegram 전송 중...")
    if send_telegram(summary):
        print("✅ 전송 완료")
        return 0
    else:
        print("❌ 전송 실패")
        return 1

if __name__ == "__main__":
    exit(main())
