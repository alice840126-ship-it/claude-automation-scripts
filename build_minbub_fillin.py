#!/usr/bin/env python3
"""
민법 괄호 채우기 문제 생성기
- 별 표시(★) 있는 중요 문장 추출
- 핵심 단어를 괄호로 변환
"""

import json
import re
from pathlib import Path
from datetime import datetime

def extract_star_questions_from_pdf(pdf_path: str) -> list:
    """PDF에서 별 표시(★) 있는 문제 추출"""
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 없음. 설치 필요: pip3 install PyPDF2")
        return []

    questions = []

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            # 별 표시(★)로 시작하는 문장 찾기
            lines = text.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('★'):
                    # 문장 클렌징
                    question = clean_question(line)
                    if question and len(question) > 20:  # 너무 짧은 건 제외
                        questions.append({
                            "id": f"minbub_{page_num}_{i}",
                            "page": page_num + 1,
                            "original": question,
                            "source": "민법"
                        })

    return questions

def clean_question(text: str) -> str:
    """문장 클렌징"""
    # 별 표시 제거
    text = text.replace('★', '').strip()
    # 번호 제거 (예: "5." -> "")
    text = re.sub(r'^\d+\.?\s*', '', text)
    # 불필요한 공백 제거
    text = ' '.join(text.split())
    return text

def create_fill_in_blank(question: str) -> tuple:
    """괄호 채우기 문제 생성
    예: "조세포탈목적으로 한 중간생략등기도 유효하다"
    -> "조세포탈목적으로 한 (     ) 등기도 유효하다", "중간생략"
    """
    # 핵심 법률 용어 패턴
    patterns = [
        r'(중간생략등기|등기)',  # 등기 관련
        r'(실체관계|부합하다|유효하다|무효이다)',  # 효력 관련
        r'(근저당권|저당권|지상권|지역권|전세권|유치권)',  # 물권
        r'(매매|교환|증여|임대차)',  # 계약
        r'(소유권|점유권|용익물권|담보물권)',  # 물권 종류
        r'(등기|인도|점유)',  # 권리 변동
        r'(청구권|항변권|취소권|해제권)',  # 권리
    ]

    # 문장에서 중요한 법률 용어 찾기
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            keyword = match.group(1)
            if len(keyword) >= 3:  # 3글자 이상만
                blanked = question.replace(keyword, ' (     ) ', 1)
                return blanked, keyword

    # 패턴 매칭 안 되면 문장 끝에서 4~6글자 추출
    words = question.split()
    if len(words) >= 3:
        target = words[-2] if len(words[-2]) >= 3 else words[-3]
        blanked = question.replace(target, ' (     ) ', 1)
        return blanked, target

    return None, None

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_fillin_questions.json"

    print("📚 민법 괄호 채우기 문제 생성 시작")
    print(f"📖 PDF: {pdf_path}")

    # 별 표시 문제 추출
    questions = extract_star_questions_from_pdf(pdf_path)
    print(f"✅ 별 표시 문제 {len(questions)}개 발견")

    # 괄호 채우기 변환
    fillin_questions = []

    for q in questions:
        blanked, answer = create_fill_in_blank(q['original'])

        if blanked and answer:
            # 주제 추출 (간단하게)
            topic = "민법총칙"
            if "물권" in q['original'] or "소유권" in q['original']:
                topic = "물권법"
            elif "계약" in q['original'] or "매매" in q['original']:
                topic = "채권법"
            elif "임대차" in q['original']:
                topic = "임대차법"

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
    print(f"\n📝 샘플 문제 (3개):")
    for i, q in enumerate(fillin_questions[:3], 1):
        print(f"\n[{i}] {q['topic']} (p.{q['page']})")
        print(f"Q: {q['question']}")
        print(f"A: {q['answer']}")

if __name__ == "__main__":
    main()
