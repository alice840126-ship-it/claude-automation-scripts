#!/usr/bin/env python3
"""
민법 괄호 채우기 문제 생성기 v3
- 별 표시(★) 있는 모든 문제 추출
- 핵심 법률 용어를 괄호로 변환
"""

import json
import re
from pathlib import Path

def extract_all_star_questions(pdf_path: str) -> list:
    """PDF에서 별 표시(★) 있는 모든 문제 추출"""
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 없음")
        return []

    questions = []
    seen_texts = set()  # 중복 방지

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # 별 표시가 있는 줄 찾기 (1개 또는 2개)
                if '★' in line:
                    # 별 표시 제거
                    clean_line = line.replace('★', '').replace('◆', '').strip()

                    # 다음 줄들도 합치기 (문장 완성을 위해)
                    full_text = clean_line
                    j = i + 1
                    while j < len(lines) and j < i + 5:  # 최대 5줄까지
                        next_line = lines[j].strip()
                        # 빈 줄이거나 별 표시 있으면 중단
                        if not next_line or '★' in next_line:
                            break
                        # 숫자로 시작하면 다음 문제일 가능성
                        if re.match(r'^\d+\.', next_line):
                            break
                        # 문장이 계속되면 합치기
                        if len(next_line) > 3:
                            full_text += ' ' + next_line
                        j += 1

                    # 클렌징
                    cleaned = clean_sentence(full_text)

                    # 중복 확인 & 길이 확인
                    if cleaned and len(cleaned) >= 20 and cleaned not in seen_texts:
                        seen_texts.add(cleaned)
                        questions.append({
                            "id": f"minbub_p{page_num+1}_{len(questions)}",
                            "page": page_num + 1,
                            "original": cleaned,
                            "source": "민법"
                        })

                i += 1

    return questions

def clean_sentence(text: str) -> str:
    """문장 클렌징"""
    # 특수문자 제거
    text = re.sub(r'[！◆■□▶●○◎▣▤]', '', text)
    # 불필요한 공백 제거
    text = ' '.join(text.split())
    return text.strip()

def create_fill_in_blank(question: str) -> tuple:
    """괄호 채우기 문제 생성"""
    # 중요한 법률 용어 패턴 (긴 것부터)
    legal_terms = [
        # 5글자 이상
        '중간생략등기', '근저당권설정', '선이행의무자', '강제집행면할',
        '소유권이전등기', '가등기담보등', '부동산실권리',
        # 4글자
        '근저당권', '지상권설정', '전세권설정', '유치권행사',
        '매매계약', '임대차계약', '증여계약', '교환계약',
        '소유권', '점유권', '용익물권', '담보물권', '질권설정',
        # 3글자
        '저당권', '지상권', '지역권', '전세권', '유치권',
        '등기명의', '등기절차', '등기신청', '등기완료',
        '계약금', '중도금', '잔금지급', '이행지체',
        '무효이다', '유효하다', '취소권', '해제권',
        '시효완성', '소멸시효', '취득시효', '제척기간',
        # 2글자 (필수적인 것만)
        '등기', '매매', '임대', '임차', '증여', '교환',
        '청구', '항변', '취소', '해제', '추인',
        '무효', '유효', '시효',
    ]

    # 긴 용어부터 매칭
    for term in legal_terms:
        if term in question:
            blanked = question.replace(term, ' (           ) ', 1)
            return blanked, term

    # 패턴 매칭 안 되면 문장 끝에서 핵심 단어 추출
    # 예: "~한다", "~이다" 앞의 2-4글자 단어
    words = question.split()
    for word in reversed(words):
        word = word.strip('.,;!?')
        if 2 <= len(word) <= 4 and word not in ['이다', '한다', '없다', '있다', '위해', '경우', '때문', '수있다']:
            blanked = question.replace(word, ' (           ) ', 1)
            return blanked, word

    return None, None

def classify_topic(text: str) -> str:
    """주제 분류"""
    if any(k in text for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권', '유치권', '질권']):
        return "물권법"
    elif any(k in text for k in ['계약', '매매', '임대차', '증여', '교환', '이행', '채무', '채권']):
        return "계약법/채권법"
    elif any(k in text for k in ['혼인', '상속', '친족', '부부', '부양']):
        return "가족법"
    else:
        return "민법총칙"

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_fillin_questions.json"

    print("📚 민법 괄호 채우기 문제 생성 시작")
    print(f"📖 PDF: {pdf_path}")

    # 별 표시 문제 추출
    questions = extract_all_star_questions(pdf_path)
    print(f"✅ 별 표시(★) 문제 {len(questions)}개 발견")

    if not questions:
        print("❌ 문제 추출 실패")
        return

    # 괄호 채우기 변환
    fillin_questions = []

    for q in questions:
        blanked, answer = create_fill_in_blank(q['original'])

        if blanked and answer and len(answer) >= 2:
            topic = classify_topic(q['original'])

            fillin_questions.append({
                "id": q['id'],
                "topic": topic,
                "question": blanked,
                "answer": answer,
                "original": q['original'],
                "page": q['page']
            })

    print(f"✅ 괄호 채우기 문제 {len(fillin_questions)}개 생성")

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fillin_questions, f, ensure_ascii=False, indent=2)

    print(f"💾 저장 완료: {output_file}")

    # 주제별 통계
    topic_counts = {}
    for q in fillin_questions:
        topic_counts[q['topic']] = topic_counts.get(q['topic'], 0) + 1

    print(f"\n📊 주제별 분포:")
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic}: {count}개")

    # 샘플 출력
    print(f"\n📝 샘플 문제 (5개):")
    for i, q in enumerate(fillin_questions[:5], 1):
        print(f"\n[{i}] {q['topic']} (p.{q['page']})")
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}")

if __name__ == "__main__":
    main()
