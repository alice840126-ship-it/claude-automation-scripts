#!/usr/bin/env python3
"""
민법 OX 문제 추출 개선판
- 여러 줄에 걸친 문장 처리
"""

import json
import re
from pathlib import Path


def extract_minbub_ox_v2(md_file: Path) -> list:
    """민법 OX 문제 추출 개선판"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = []

    # 정규식: 번호로 시작하고 (O) 또는 (X)로 끝나는 패턴
    # 여러 줄을 고려해서 전체 텍스트에서 검색
    pattern = re.compile(r'(\d+)\.\s*([^（\n]+?[（\(]?[OX][）\)])', re.MULTILINE)

    for match in pattern.finditer(content):
        q_num = match.group(1)
        full_text = match.group(2).strip()

        # 정답 추출
        if '(O)' in full_text or '（O）' in full_text:
            answer = 'O'
            # 정답 표시 제거
            question_text = re.sub(r'[（\(]?O[）\)]', '', full_text).strip()
        elif '(X)' in full_text or '（X）' in full_text:
            answer = 'X'
            question_text = re.sub(r'[（\(]?X[）\)]', '', full_text).strip()
        else:
            continue

        # 클린업
        question_text = re.sub(r'\s+', ' ', question_text).strip()
        question_text = re.sub(r'^\d+\.\s*', '', question_text).strip()

        # 너무 짧으면 스킵
        if len(question_text) < 10:
            continue

        # 주제 추출
        pos_before = match.start()
        lines_before = content[:pos_before].split('\n')
        topic = "민법 기출"

        for line in reversed(lines_before[-15:]):
            line = line.strip()
            if '02 ' in line or '03 ' in line or '04 ' in line:
                topic = line
                break
            if any(x in line for x in ['민법총칙', '물권법', '계약법', '점유권', '소유권', '저당권', '임대차', '유치권']):
                topic = line[:60]
                break

        questions.append({
            'id': f'minbub-ox-{q_num}',
            'round': '기출',
            'topic': topic,
            'question': question_text,
            'options': ['O', 'X'],
            'answer': answer,
            'explanation': ''
        })

    # 중복 제거 (ID 기준)
    seen = set()
    unique_questions = []
    for q in questions:
        if q['id'] not in seen:
            seen.add(q['id'])
            unique_questions.append(q)

    print(f"✅ 민법 OX 문제 {len(unique_questions)}개 추출")
    return unique_questions


if __name__ == '__main__':
    md_file = Path.home() / 'Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'

    questions = extract_minbub_ox_v2(md_file)

    # 기존 DB 로드
    db_path = Path.home() / '.claude' / 'exam_questions_database.json'
    with open(db_path, 'r', encoding='utf-8') as f:
        db = json.load(f)

    # 개론은 유지, 민법만 교체
    db['민법'] = questions

    # 저장
    with open(db_path, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"📁 DB 업데이트: {db_path}")
    print(f"   개론: {len(db['개론'])}개, 민법: {len(db['민법'])}개")
