#!/usr/bin/env python3
"""
민법 괄호 채우기 문제 생성기 v2
- 별 2개(★★) 있는 중요 문장만 추출
- 핵심 법률 용어를 괄호로 변환
"""

import json
import re
from pathlib import Path
from datetime import datetime

def extract_double_star_questions(pdf_path: str) -> list:
    """PDF에서 별 2개(★★) 있는 문제 추출"""
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 없음")
        return []

    questions = []

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            lines = text.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()

                # 별 2개 패턴: ★★ 또는 ★ ★
                if '★★' in line or ('★' in line and line.count('★') >= 2):
                    # 다음 줄도 합치기 (문장이 길 수 있음)
                    full_sentence = line.replace('★★', '').replace('★', '').strip()

                    # 다음 2-3줄도 확인해서 합치기
                    j = i + 1
                    while j < len(lines) and j < i + 3:
                        next_line = lines[j].strip()
                        # 숫자나 글자로 시작하면 계속 합치기
                        if next_line and not next_line.startswith('★') and len(next_line) > 5:
                            full_sentence += ' ' + next_line
                            j += 1
                        else:
                            break

                    # 클렌징
                    cleaned = clean_sentence(full_sentence)

                    if cleaned and len(cleaned) >= 30:  # 최소 30글자
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
    text = re.sub(r'[！◆■□▶●○◎]', '', text)
    # 번호 제거 (예: "6 ! " -> "")
    text = re.sub(r'^\d+\s*[!！]?\s*', '', text)
    # 불필요한 공백 제거
    text = ' '.join(text.split())
    return text.strip()

def create_fill_in_blank(question: str) -> tuple:
    """괄호 채우기 문제 생성
    핵심 법률 용어를 괄호로 변환
    """
    # 중요한 법률 용어 패턴 (긴 것부터 매칭)
    legal_terms = [
        # 물권 관련
        '근저당권설정등기', '근저당권', '저당권', '지상권', '지역권',
        '전세권', '유치권', '질권', '소유권', '점유권', '용익물권', '담보물권',
        # 등기 관련
        '중간생략등기', '등기', '가등기', '보존등기', '이전등기',
        # 계약 관련
        '이행의무자', '선이행의무자', '계약금', '중도금', '잔금',
        '쌍무계약', '편무계약', '담보계약', '임대차계약',
        # 효력 관련
        '무효이다', '유효하다', '취소할수있다', '해제할수있다',
        '추인', '시효', '제척기간', '소멸시효', '취득시효',
        # 기타
        '실체관계', '부합하면', '강제집행', '부동산',
        '매매', '교환', '증여', '임대차',
        '청구권', '항변권', '취소권', '해제권', '회복권',
    ]

    # 긴 용어부터 매칭
    for term in legal_terms:
        if term in question:
            blanked = question.replace(term, ' (           ) ', 1)
            return blanked, term

    # 패턴 매칭 안 되면 문장에서 중요한 2음절 이상 단어 찾기
    words = question.split()
    for word in reversed(words):  # 뒤에서부터
        if len(word) >= 2 and word not in ['이다', '한다', '없다', '있다', '위해']:
            blanked = question.replace(word, ' (           ) ', 1)
            return blanked, word

    return None, None

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_fillin_questions.json"

    print("📚 민법 괄호 채우기 문제 생성 시작")
    print(f"📖 PDF: {pdf_path}")

    # 별 2개 문제 추출
    questions = extract_double_star_questions(pdf_path)
    print(f"✅ 별 2개(★★) 문제 {len(questions)}개 발견")

    if not questions:
        print("❌ 문제 추출 실패")
        return

    # 괄호 채우기 변환
    fillin_questions = []

    for q in questions:
        blanked, answer = create_fill_in_blank(q['original'])

        if blanked and answer and len(answer) >= 2:
            # 주제 분류
            topic = "민법총칙"
            if any(k in q['original'] for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권']):
                topic = "물권법"
            elif any(k in q['original'] for k in ['계약', '매매', '임대차', '증여']):
                topic = "계약법/채권법"
            elif any(k in q['original'] for k in ['혼인', '상속', '친족']):
                topic = "가족법"

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

    # 샘플 출력
    print(f"\n📝 샘플 문제 (5개):")
    for i, q in enumerate(fillin_questions[:5], 1):
        print(f"\n[{i}] {q['topic']} (p.{q['page']})")
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}")

if __name__ == "__main__":
    main()
