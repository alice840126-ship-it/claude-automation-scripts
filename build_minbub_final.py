#!/usr/bin/env python3
"""
민법 OX 문제 추출 최종판
- 여러 줄에 걸친 문장 완벽 처리
"""

import json
import re
from pathlib import Path


def extract_minbub_ox_final(md_file: Path) -> list:
    """민법 OX 문제 추출 최종판"""
    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    questions = []
    i = 0
    q_counter = 1  # 번호 추적기

    while i < len(lines):
        line = lines[i].strip()

        # (O) 또는 (X)로 끝나는지 확인 (대소문자 무시)
        if re.search(r'[（\(]?[OX][）\)]?\s*$', line, re.IGNORECASE):
            # 정답 추출
            if '(O)' in line or '（O）' in line:
                answer = 'O'
            elif '(X)' in line or '（X）' in line:
                answer = 'X'
            elif '(o)' in line:
                answer = 'O'
            elif '(x)' in line:
                answer = 'X'
            else:
                i += 1
                continue

            # 현재 라인에서 정답 제거
            current_text = re.sub(r'[（\(]?[OXox][）\)]?\s*$', '', line).strip()

            # 위로 올라가며 문장 완성
            full_question = current_text
            j = i - 1
            q_num = str(q_counter)  # 기본값

            while j >= 0:
                prev_line = lines[j].strip()

                # 빈 줄이거나 주제 섹션(02, 03 등)이면 중단
                if not prev_line or re.match(r'^0[234]\s', prev_line):
                    break

                # 번호로 시작하면 문제 시작점 발견
                num_match = re.match(r'^(\d+)\.\s*(.+)', prev_line)
                if num_match:
                    q_num = num_match.group(1)
                    q_counter = int(q_num) + 1  # 카운터 업데이트
                    rest = num_match.group(2).strip()

                    # 문장 합치기
                    full_question = rest + ' ' + full_question
                    break

                # 일반 텍스트 라인이면 앞에 추가
                full_question = prev_line + ' ' + full_question
                j -= 1

            # 클린업
            full_question = re.sub(r'\s+', ' ', full_question).strip()
            full_question = re.sub(r'^\d+\.\s*', '', full_question).strip()

            # 너무 짧거나 이미 같은 번호가 있으면 스킵
            if len(full_question) < 10:
                i += 1
                continue

            q_id = f'minbub-ox-{q_num}'
            if any(q['id'] == q_id for q in questions):
                i += 1
                continue

            # 주제 추출 (더 위쪽에서)
            topic = "민법 기출"
            if j > 0:
                for k in range(max(0, j-10), j):
                    topic_line = lines[k].strip()
                    if '02 ' in topic_line or '03 ' in topic_line or '04 ' in topic_line:
                        topic = topic_line
                        break
                    if any(x in topic_line for x in ['민법총칙', '물권법', '계약법', '점유권', '소유권', '저당권', '임대차']):
                        topic = topic_line[:60]
                        break

            questions.append({
                'id': q_id,
                'round': '기출',
                'topic': topic,
                'question': full_question,
                'options': ['O', 'X'],
                'answer': answer,
                'explanation': ''
            })

        i += 1

    print(f"✅ 민법 OX 문제 {len(questions)}개 추출")
    return questions


if __name__ == '__main__':
    md_file = Path.home() / 'Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'

    questions = extract_minbub_ox_final(md_file)

    # 기존 DB 로드
    db_path = Path.home() / '.claude' / 'exam_questions_database.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # 민법만 교체
    db['민법'] = questions

    # 저장
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"📁 DB 업데이트: {db_path}")
    print(f"   개론: {len(db['개론'])}개, 민법: {len(db['민법'])}개")

    # 샘플 출력
    print("\n=== 샘플 ===")
    for q in questions[:3]:
        print(f"\n{q['id']}: {q['question'][:80]}...")
        print(f"정답: {q['answer']}")
