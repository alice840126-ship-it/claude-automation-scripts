#!/usr/bin/env python3
"""
민법 객관식 문제 추출기 v7
- Markdown에서 모든 문제 추출
- 번호 + 문장 + 보기(①②③) + OX 정답
"""

import json
import re
from pathlib import Path

def extract_all_questions(md_path: str) -> list:
    """Markdown에서 모든 객관식 문제 추출"""
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions = []
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # 문제 번호 패턴
        q_match = re.match(r'^(\d+)\.\s*(.+)', line)
        if q_match and len(q_match.group(2)) > 15:
            q_num = q_match.group(1)
            q_text = q_match.group(2).strip()

            # OX 표시 확인 (정답 여부)
            has_answer = '(O)' in q_text or '(○)' in q_text or '(X)' in q_text or '(×)' in q_text

            # 다음 줄도 확인
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()

                # 빈 줄
                if not next_line:
                    j += 1
                    continue

                # 새 문제 시작
                if re.match(r'^\d+\.', next_line):
                    break

                # 보기 시작
                if re.match(r'^[①②③④⑤]', next_line):
                    break

                # 문장 이어붙이기
                q_text += " " + next_line
                has_answer = has_answer or '(O)' in next_line or '(○)' in next_line
                j += 1

            # 보기 수집
            options = []
            answer = None
            k = j

            while k < len(lines):
                opt_line = lines[k].strip()

                # 보기 패턴
                opt_match = re.match(r'^([①②③④⑤])\s*(.+)', opt_line)
                if opt_match:
                    opt_char = opt_match.group(1)
                    opt_text = opt_match.group(2).strip()
                    options.append(opt_text)

                    # 정답 체크
                    if '(O)' in opt_line or '(○)' in opt_line:
                        answer_map = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
                        answer = answer_map.get(opt_char)
                elif not opt_line:
                    break
                elif re.match(r'^\d+\.', opt_line):
                    break
                else:
                    # 보기가 아니면 끝
                    break

                k += 1

            # 문제 저장 (문제 + OX 표시)
            if len(q_text) >= 15:
                questions.append({
                    "id": f"minbub_q{q_num}",
                    "number": int(q_num),
                    "text": q_text,
                    "options": options,
                    "answer": answer,
                    "has_ox": has_answer
                })

            i = k
        else:
            i += 1

    return questions

def clean_questions(questions: list) -> list:
    """문제 정리"""
    valid_questions = []

    for q in questions:
        # 텍스트 정리
        q['text'] = re.sub(r'\s+', ' ', q['text']).strip()
        q['options'] = [re.sub(r'\s+', ' ', opt).strip() for opt in q['options']]

        # 주제 분류
        topic = classify_topic(q['text'])

        valid_questions.append({
            "id": q['id'],
            "topic": topic,
            "question": q['text'],
            "options": q['options'],
            "answer": q['answer']
        })

    return valid_questions

def classify_topic(text: str) -> str:
    """주제 분류"""
    if any(k in text for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권', '유치권', '질권', '등기', '점유', '공유', '부합', '혼동']):
        return "물권법"
    elif any(k in text for k in ['계약', '매매', '임대차', '증여', '교환', '이행', '채무', '채권', '해제', '취소', '손해배상', '계약금']):
        return "계약법/채권법"
    elif any(k in text for k in ['혼인', '상속', '친족', '부부', '부양', '이혼']):
        return "가족법"
    elif any(k in text for k in ['의사표시', '대리', '무효', '취소', '법률행위', '조건', '기한', '추인']):
        return "민법총칙"
    else:
        return "민법"

def main():
    md_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md"
    output_file = Path.home() / ".claude" / "minbub_from_md.json"

    print("📚 Markdown에서 민법 문제 추출 v7")
    print(f"📖 파일: {md_path}\n")

    # 문제 추출
    raw_questions = extract_all_questions(md_path)
    print(f"✅ 원본 문제 {len(raw_questions)}개 발견")

    # 정리
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

    # 보기 개수별 통계
    opt_counts = {}
    for q in valid_questions:
        opt_num = len(q['options'])
        opt_counts[opt_num] = opt_counts.get(opt_num, 0) + 1

    print(f"\n📊 보기 개수별 분포:")
    for opt_num, count in sorted(opt_counts.items()):
        print(f"  보기 {opt_num}개: {count}개")

    # 샘플 출력
    print(f"\n📝 샘플 문제 (3개):")
    for i, q in enumerate(valid_questions[:3], 1):
        print(f"\n[{i}] {q['topic']} ({len(q['options'])}개 보기)")
        print(f"Q: {q['question'][:150]}...")
        if q['options']:
            for j, opt in enumerate(q['options'][:3], 1):
                print(f"  {j}. {opt}")
        if q['answer']:
            print(f"정답: {q['answer']}번")

if __name__ == "__main__":
    main()
