#!/usr/bin/env python3
"""
민법 5지선다 객관식 문제 추출기 v3
- PDF 모든 페이지 스캔
- 번호 문제 + 보기 추출
- 정답 OX 패턴 파악
"""

import json
import re
from pathlib import Path

def extract_all_minbub_questions(pdf_path: str) -> list:
    """PDF에서 모든 객관식 문제 추출"""
    try:
        import PyPDF2
    except ImportError:
        print("❌ PyPDF2 없음")
        return []

    questions = []
    current_q = None

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text()

            # 줄 단위로 처리
            lines = text.split('\n')

            for i, line in enumerate(lines):
                line = line.strip()

                # 빈 줄 스킵
                if not line:
                    continue

                # 문제 번호 패턴: "숫자. 문장" (최소 15글자)
                # 예: "1. 당사자 쌍방이 각각 별개의 약정으로"
                question_match = re.match(r'^(\d+)\.\s*([가-힣a-zA-Z]{15,})', line)
                if question_match:
                    # 이전 문제 저장
                    if current_q and current_q.get('text'):
                        questions.append(current_q)

                    # 새 문제 시작
                    q_num = question_match.group(1)
                    q_text = question_match.group(2)
                    current_q = {
                        "id": f"minbub_p{page_num+1}_q{q_num}",
                        "page": page_num + 1,
                        "number": int(q_num),
                        "text": q_text,
                        "options": [],
                        "answer": None
                    }

                # 보기 패턴: ①, ②, ③, ④, ⑤
                elif current_q and re.match(r'^[①②③④⑤]', line):
                    option_text = line[1:].strip()  # ① 제거
                    current_q["options"].append(option_text)

                # 정답 패턴: (O), (X), (○), (×)
                elif current_q and re.search(r'\([O○X×]\)', line):
                    # 어느 보기에 O 표시가 있는지 찾기
                    for opt_char, opt_num in [('①', 1), ('②', 2), ('③', 3), ('④', 4), ('⑤', 5)]:
                        if opt_char in line and ('(O)' in line or '(○)' in line):
                            current_q["answer"] = opt_num
                            break

                # 문제가 너무 길면 다음 줄도 추가
                elif current_q and len(current_q["text"]) < 100:
                    # 숫자나 특수문자로 시작하지 않으면 연속된 문장
                    if not re.match(r'^[\d①②③④⑤★◆■]', line):
                        current_q["text"] += " " + line

        # 마지막 문제 저장
        if current_q and current_q.get('text'):
            questions.append(current_q)

    return questions

def clean_question_text(q: dict) -> dict:
    """문제 텍스트 정리"""
    # 문장 정리
    q['text'] = re.sub(r'\s+', ' ', q['text']).strip()
    # 보기 정리
    q['options'] = [re.sub(r'\s+', ' ', opt).strip() for opt in q['options'] if opt.strip()]
    return q

def classify_topic(text: str) -> str:
    """주제 분류"""
    keywords = {
        "물권법": ['물권', '소유권', '점유권', '지상권', '지역권', '전세권', '유치권', '저당권', '질권', '등기', '점유'],
        "계약법/채권법": ['계약', '매매', '임대차', '증여', '교환', '이행', '채무', '채권', '해제', '취소', '손해배상'],
        "가족법": ['혼인', '상속', '친족', '부부', '부양', '이혼'],
        "민법총칙": ['의사표시', '대리', '무효', '취소', '법률행위', '조건', '기한']
    }

    for topic, kws in keywords.items():
        if any(kw in text for kw in kws):
            return topic

    return "민법"

def main():
    pdf_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
    output_file = Path.home() / ".claude" / "minbub_multiple_choice.json"

    print("📚 민법 5지선다 객관식 문제 추출 v3")
    print(f"📖 PDF: {pdf_path}")

    # 문제 추출
    raw_questions = extract_all_minbub_questions(pdf_path)
    print(f"✅ 원본 문제 {len(raw_questions)}개 발견")

    # 정리 및 필터링
    valid_questions = []
    for q in raw_questions:
        q = clean_question_text(q)

        # 최소 조건: 문제 텍스트 + 보기 3개 이상
        if len(q['text']) >= 20 and len(q['options']) >= 3:
            topic = classify_topic(q['text'])

            valid_questions.append({
                "id": q['id'],
                "topic": topic,
                "question": q['text'],
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
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count}개")

    # 샘플 출력
    print(f"\n📝 샘플 문제 (5개):")
    for i, q in enumerate(valid_questions[:5], 1):
        print(f"\n[{i}] {q['topic']} (p.{q['page']})")
        print(f"Q: {q['question'][:100]}...")
        for j, opt in enumerate(q['options'][:5], 1):
            print(f"  {j}. {opt[:60]}...")
        if q['answer']:
            print(f"정답: {q['answer']}번")

if __name__ == "__main__":
    main()
