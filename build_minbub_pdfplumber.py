#!/usr/bin/env python3
"""
민법 5지선다 객관식 문제 추출기 v4
- pdfplumber 사용 (정확한 텍스트 추출)
- 번호 문제 + OX 정답 추출
"""

import json
import re
from pathlib import Path
try:
    import pdfplumber
except ImportError:
    print("❌ pdfplumber 설치 필요: pip3 install pdfplumber")
    exit(1)

def extract_questions_from_pdf(pdf_path: str) -> list:
    """PDF에서 객관식 문제 추출"""
    questions = []
    current_q = None

    with pdfplumber.open(pdf_path) as pdf:
        print(f"📖 총 {len(pdf.pages)}페이지 처리 중...")

        for page_num, page in enumerate(pdf.pages):
            if page_num < 200:  # 앞부분은 건너뜀 (문제는 뒤에 있음)
                continue

            text = page.extract_text()
            if not text:
                continue

            lines = text.split('\n')

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # 문제 번호 패턴: "숫자. 문장" (최소 20글자)
                q_match = re.match(r'^(\d+)\.\s*([가-힣a-zA-Z.\s]{20,})', line)
                if q_match:
                    # 이전 문제 저장
                    if current_q and current_q.get('text') and len(current_q.get('options', [])) >= 3:
                        questions.append(current_q)

                    # 새 문제 시작
                    q_num = q_match.group(1)
                    q_text = q_match.group(2).strip()
                    current_q = {
                        "id": f"minbub_p{page_num+1}_q{q_num}",
                        "page": page_num + 1,
                        "number": int(q_num),
                        "text": q_text,
                        "options": [],
                        "answer": None
                    }

                # 보기 패턴: ①, ②, ③, ④, ⑤
                elif current_q and re.match(r'^[①②③④⑤]\s*', line):
                    option_text = re.sub(r'^[①②③④⑤]\s*', '', line).strip()
                    current_q["options"].append(option_text)

                # OX 정답 패턴
                elif current_q and re.search(r'\([OX○×]\)', line):
                    for opt_char, opt_num in [('①', 1), ('②', 2), ('③', 3), ('④', 4), ('⑤', 5)]:
                        if opt_char in line and ('(O)' in line or '(○)' in line):
                            current_q["answer"] = opt_num
                            break

            # 진행상황
            if (page_num + 1) % 50 == 0:
                print(f"  처리 중... {page_num + 1}/{len(pdf.pages)}페이지, 문제 {len(questions)}개 발견")

        # 마지막 문제 저장
        if current_q and current_q.get('text') and len(current_q.get('options', [])) >= 3:
            questions.append(current_q)

    return questions

def clean_questions(questions: list) -> list:
    """문제 정리 및 필터링"""
    valid_questions = []

    for q in questions:
        # 텍스트 정리
        q['text'] = re.sub(r'\s+', ' ', q['text']).strip()
        q['options'] = [re.sub(r'\s+', ' ', opt).strip() for opt in q['options']]

        # 최소 조건: 문제 20글자 이상 + 보기 3개 이상
        if len(q['text']) >= 20 and len(q['options']) >= 3:
            # 주제 분류
            topic = classify_topic(q['text'])

            valid_questions.append({
                "id": q['id'],
                "topic": topic,
                "question": q['text'],
                "options": q['options'][:5],
                "answer": q['answer'],
                "page": q['page']
            })

    return valid_questions

def classify_topic(text: str) -> str:
    """주제 분류"""
    if any(k in text for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권', '유치권', '질권', '등기', '점유']):
        return "물권법"
    elif any(k in text for k in ['계약', '매매', '임대차', '증여', '교환', '이행', '채무', '채권', '해제', '취소', '손해배상']):
        return "계약법/채권법"
    elif any(k in text for k in ['혼인', '상속', '친족', '부부', '부양', '이혼']):
        return "가족법"
    elif any(k in text for k in ['의사표시', '대리', '무효', '취소', '법률행위', '조건', '기한']):
        return "민법총칙"
    else:
        return "민법"

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_multiple_choice.json"

    print("📚 민법 5지선다 객관식 문제 추출 v4 (pdfplumber)")
    print(f"📖 PDF: {pdf_path}\n")

    # 문제 추출
    raw_questions = extract_questions_from_pdf(pdf_path)
    print(f"\n✅ 원본 문제 {len(raw_questions)}개 발견")

    # 정리 및 필터링
    valid_questions = clean_questions(raw_questions)
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
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
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
