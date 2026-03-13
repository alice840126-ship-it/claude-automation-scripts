#!/usr/bin/env python3
"""
민법 객관식 문제 추출기 v6
- Markdown 파일에서 문제 추출
- 번호 문제 + 보기 + OX 정답
"""

import json
import re
from pathlib import Path

def extract_questions_from_md(md_path: str) -> list:
    """Markdown 파일에서 객관식 문제 추출"""
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # 문제 번호 패턴: "숫자. 문장"
        q_match = re.match(r'^(\d+)\.\s*(.+)', line)
        if q_match and len(q_match.group(2)) > 15:
            q_num = q_match.group(1)
            q_text = q_match.group(2).strip()

            # 이어지는 문장 합치기
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                # 빈 줄이거나 새 문제 시작하면 중단
                if not next_line or re.match(r'^\d+\.', next_line):
                    break
                # ①, ②, ③ 등 보기 시작하면 중단
                if re.match(r'^[①②③④⑤]', next_line):
                    break
                # 문장 이어붙이기
                q_text += " " + next_line
                j += 1

            # 보기 수집
            options = []
            answer = None

            k = j
            while k < len(lines):
                opt_line = lines[k].strip()

                # 보기 패턴: ①, ②, ③, ④, ⑤
                opt_match = re.match(r'^([①②③④⑤])\s*(.+)', opt_line)
                if opt_match:
                    opt_text = opt_match.group(2).strip()
                    options.append(opt_text)

                    # OX 정답 체크
                    if '(O)' in opt_line or '(○)' in opt_line:
                        answer_map = {'①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5}
                        answer = answer_map.get(opt_match.group(1))
                elif not opt_line:
                    # 빈 줄은 보기 끝
                    break
                elif re.match(r'^\d+\.', opt_line):
                    # 새 문제 시작
                    break
                elif len(options) > 0 and '(' in opt_line and ')' in opt_line:
                    # 보기 뒤에 있는 정답 표시
                    for opt_char, opt_num in [('①', 1), ('②', 2), ('③', 3), ('④', 4), ('⑤', 5)]:
                        if opt_char in opt_line and ('(O)' in opt_line or '(○)' in opt_line):
                            answer = opt_num
                            break

                k += 1

            # 문제 저장 (최소 2개 보기)
            if len(q_text) >= 20 and len(options) >= 2:
                # 페이지 번호 추출 (근사치)
                page_match = re.search(r'제\s*\d+\s*편|(\d+)\s*민법', content[:content.find(q_text)])
                page_num = int(page_match.group(1)) if page_match else 1

                questions.append({
                    "id": f"minbub_q{q_num}",
                    "number": int(q_num),
                    "text": q_text,
                    "options": options,
                    "answer": answer
                })

            i = k
        else:
            i += 1

    return questions

def classify_topic(text: str) -> str:
    """주제 분류"""
    if any(k in text for k in ['물권', '소유권', '점유권', '지상권', '저당권', '전세권', '유치권', '질권', '등기', '점유', '공유']):
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
    md_path = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md"
    output_file = Path.home() / ".claude" / "minbub_from_md.json"

    print("📚 Markdown에서 민법 문제 추출")
    print(f"📖 파일: {md_path}\n")

    # 문제 추출
    questions = extract_questions_from_md(md_path)
    print(f"✅ 문제 {len(questions)}개 발견")

    # 주제 분류
    for q in questions:
        q['topic'] = classify_topic(q['text'])

    # 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f"💾 저장 완료: {output_file}")

    # 주제별 통계
    topic_counts = {}
    for q in questions:
        topic_counts[q['topic']] = topic_counts.get(q['topic'], 0) + 1

    print(f"\n📊 주제별 분포:")
    for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {topic}: {count}개")

    # 샘플 출력
    print(f"\n📝 샘플 문제 (5개):")
    for i, q in enumerate(questions[:5], 1):
        print(f"\n[{i}] {q['topic']} {len(q['options'])}지선다")
        print(f"Q: {q['text']}")
        for j, opt in enumerate(q['options'], 1):
            print(f"  {j}. {opt}")
        if q['answer']:
            print(f"정답: {q['answer']}번")

if __name__ == "__main__":
    main()
