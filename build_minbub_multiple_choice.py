#!/usr/bin/env python3
"""
민법 5지선다 객관식 문제 추출기
- PDF에서 번호 문제와 보기 추출
- O/X 표시로 정답 판별
"""

import json
import re
from pathlib import Path
from typing import Optional

def extract_multiple_choice_questions(pdf_path: str) -> list:
    """PDF에서 5지선다 객관식 문제 추출"""
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 없음")
        return []

    questions = []
    current_question = None

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)

        # 뒤쪽 페이지에서 기출문제 찾기
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            lines = text.split('\n')

            for line in lines:
                line = line.strip()

                # 문제 번호 패턴 (1. 2. 3. 등)
                if re.match(r'^\d+\.', line) and len(line) > 20:
                    # 이전 문제 저장
                    if current_question and current_question.get('question'):
                        questions.append(current_question)

                    # 새 문제 시작
                    current_question = {
                        "id": f"minbub_{page_num+1}_{len(questions)}",
                        "page": page_num + 1,
                        "question": clean_text(line),
                        "options": [],
                        "answer": None,
                        "source": "민법"
                    }

                # 보기 패턴 (①, ②, ③, ④, ⑤)
                elif current_question and re.match(r'^[①②③④⑤]', line):
                    option_text = clean_text(line)
                    current_question["options"].append(option_text)

                # OX 패턴 (정답 표시)
                elif current_question and ('(O)' in line or '(X)' in line or '(○)' in line or '(×)' in line):
                    # 보기 중 어디에 O 표시가 있는지 찾기
                    ox_match = re.search(r'[①②③④⑤]\s*\((O|○|X|×)\)', line)
                    if ox_match:
                        option_char = ox_match.group(0)[0]  # ①, ② 등
                        answer_map = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
                        current_question["answer"] = answer_map.get(option_char)

                # 페이지 넘어가면 문제 저장
                elif current_question and len(current_question["options"]) >= 4:
                    questions.append(current_question)
                    current_question = None

        # 마지막 문제 저장
        if current_question and current_question.get('question'):
            questions.append(current_question)

    return questions

def clean_text(text: str) -> str:
    """텍스트 클렌징"""
    # 특수문자 정리
    text = text.replace('（', '(').replace('）', ')')
    text = text.replace('○', 'O').replace('×', 'X')
    # 불필요한 공백 제거
    text = ' '.join(text.split())
    return text.strip()

def classify_topic(question: str) -> str:
    """주제 분류"""
    if any(k in question for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권', '유치권', '질권', '등기']):
        return "물권법"
    elif any(k in question for k in ['계약', '매매', '임대차', '증여', '교환', '이행', '채무', '채권', '해제', '취소']):
        return "계약법/채권법"
    elif any(k in question for k in ['혼인', '상속', '친족', '부부', '부양']):
        return "가족법"
    elif any(k in question for k in ['민법총칙', '의사표시', '대리', '무효', '취소']):
        return "민법총칙"
    else:
        return "민법"

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_multiple_choice.json"

    print("📚 민법 5지선다 객관식 문제 추출 시작")
    print(f"📖 PDF: {pdf_path}")

    # 문제 추출
    questions = extract_multiple_choice_questions(pdf_path)
    print(f"✅ 문제 {len(questions)}개 발견")

    # 유효한 문제만 필터링 (문제 + 보기 4개 이상)
    valid_questions = []
    for q in questions:
        if q['question'] and len(q['options']) >= 4:
            topic = classify_topic(q['question'])

            valid_questions.append({
                "id": q['id'],
                "topic": topic,
                "question": q['question'],
                "options": q['options'][:5],  # 최대 5개
                "answer": q['answer'],
                "page": q['page']
            })

    print(f"✅ 유효한 문제 {len(valid_questions)}개 생성")

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(valid_questions, f, ensure_ascii=False, indent=2)

    print(f"💾 저장 완료: {output_file}")

    # 주제별 통계
    topic_counts = {}
    for q in valid_questions:
        topic_counts[q['topic']] = topic_counts.get(q['topic'], 0) + 1

    print(f"\n📊 주제별 분포:")
    for topic, count in sorted(topic_counts.items()):
        print(f"  {topic}: {count}개")

    # 샘플 출력
    print(f"\n📝 샘플 문제 (3개):")
    for i, q in enumerate(valid_questions[:3], 1):
        print(f"\n[{i}] {q['topic']} (p.{q['page']})")
        print(f"Q: {q['question']}")
        for j, opt in enumerate(q['options'], 1):
            print(f"  {j}. {opt}")
        if q['answer']:
            print(f"정답: {q['answer']}번")

if __name__ == "__main__":
    main()
