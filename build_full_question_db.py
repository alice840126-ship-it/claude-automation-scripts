#!/usr/bin/env python3
"""
MD 파일에서 모든 기출문제 추출하여 완전한 DB 구축
"""

import json
import re
from pathlib import Path
from typing import List, Dict


def extract_gaeron_questions(md_file: Path) -> List[Dict]:
    """개론 모든 문제 추출"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = []
    lines = content.split('\n')

    # 정답 위치들 찾기
    answer_pattern = re.compile(r'[/\'*\.]?\s*정답\s*([①②③④⑤]|\d+|©|○|●)')

    # 각 문제 블록 추출
    for i, line in enumerate(lines):
        if answer_pattern.search(line):
            # 정답 추출
            ans_match = answer_pattern.search(line)
            ans = ans_match.group(1)
            answer_map = {'①': '1', '②': '2', '③': '3', '④': '4', '⑤': '5',
                          '©': '3', '○': '1', '●': '1'}
            answer = answer_map.get(ans, ans)

            # 위로 50라인 탐색하여 문제 블록 찾기
            block_start = max(0, i - 50)
            block_lines = lines[block_start:i]

            # 문제 회차 및 내용 찾기
            round_num = "기출"
            question_text = ""
            options = []
            topic = "기출문제"

            for j, blk_line in enumerate(reversed(block_lines)):
                blk_line = blk_line.strip()

                # 회차 패턴
                round_match = re.search(r'(\d+)\s*회', blk_line)
                if round_match and not round_num:
                    round_num = round_match.group(1) + "회"

                # ①②③④⑤로 시작하면 객관식 보기
                if blk_line.startswith(('①', '②', '③', '④', '⑤')):
                    options.insert(0, blk_line)
                elif re.match(r'^[①②③④⑤]', blk_line):
                    options.insert(0, blk_line)

            # 문제 텍스트 추출 (보기 앞부분)
            full_text = ' '.join(block_lines)
            for opt_marker in ['①', '②', '③', '④', '⑤']:
                if opt_marker in full_text:
                    parts = full_text.split(opt_marker, 1)
                    full_text = parts[0]
                    break

            # 회차 패턴 제거하고 문제만 추출
            question_text = re.sub(r'.*?\d+\s*회\s*[:：]\s*', '', full_text).strip()
            question_text = re.sub(r'^\s*[-/|•]+\s*', '', question_text).strip()

            # 주제 추출 (예상문제, 기출 등)
            for blk in block_lines[-20:]:
                if '예상문제' in blk:
                    topic = "예상문제"
                    break
                if '계산문제' in blk:
                    topic = "계산문제"
                    break

            if question_text and len(question_text) > 10:
                q_id = f"gaeron-{len(questions)+1:03d}"
                questions.append({
                    'id': q_id,
                    'round': round_num,
                    'topic': topic,
                    'question': question_text,
                    'options': options if options else ['①', '②', '③', '④', '⑤'],
                    'answer': answer,
                    'explanation': ''
                })

    print(f"✅ 개론 문제 {len(questions)}개 추출")
    return questions


def extract_minbub_ox_questions(md_file: Path) -> List[Dict]:
    """민법 OX 문제 추출"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    questions = []

    # 줄 단위로 처리
    lines = content.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()

        # "(O)" 또는 "(X)" 포함된 라인 찾기
        if '(O)' in line or '(X)' in line or '（O）' in line or '（X）' in line:
            # 번호 추출
            num_match = re.match(r'^(\d+)\.', line)
            if not num_match:
                continue

            q_num = num_match.group(1)

            # 정답 추출
            if '(O)' in line or '（O）' in line:
                answer = 'O'
                # (O) 제거하고 문장만 추출
                question_text = re.sub(r'[（\(]?O[）\)]', '', line).strip()
            else:
                answer = 'X'
                question_text = re.sub(r'[（\(]?X[）\)]', '', line).strip()

            # 번호 제거
            question_text = re.sub(r'^\d+\.\s*', '', question_text).strip()

            # 문장이 너무 짧으면 스킵
            if len(question_text) < 15:
                continue

            # 주제 추출 (직전 20라인에서 섹션 제목 찾기)
            topic = "민법 기출"
            for j in range(max(0, i-20), i):
                prev_line = lines[j].strip()
                if '02 ' in prev_line or '03 ' in prev_line or '04 ' in prev_line:
                    topic = prev_line
                    break
                if any(x in prev_line for x in ['민법총칙', '물권법', '계약법', '점유권', '소유권', '저당권', '임대차']):
                    topic = prev_line
                    break

            # 불필요한 기호 제거
            question_text = re.sub(r'\s+', ' ', question_text).strip()
            question_text = re.sub(r'[★*]+$', '', question_text).strip()

            questions.append({
                'id': f'minbub-ox-{q_num}',
                'round': '기출',
                'topic': topic[:50] if len(topic) > 50 else topic,
                'question': question_text,
                'options': ['O', 'X'],
                'answer': answer,
                'explanation': ''
            })

    print(f"✅ 민법 OX 문제 {len(questions)}개 추출")
    return questions


def save_full_db(gaeron: List[Dict], minbub: List[Dict]):
    """완전한 DB 저장"""
    output = Path.home() / '.claude' / 'exam_questions_database.json'

    db = {
        '개론': gaeron,
        '민법': minbub
    }

    with open(output, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

    print(f"📁 DB 저장: {output}")
    print(f"   개론: {len(gaeron)}개, 민법: {len(minbub)}개")

    return output


if __name__ == '__main__':
    base_dir = Path.home() / 'Desktop/0. 자비스/공인중개사/마크다운 형식'

    gaeron_md = base_dir / 'gaeron. ocr.md'
    minbub_md = base_dir / 'minbub.ocr.md'

    print("🚀 전체 문제 추출 시작...")
    gaeron_q = extract_gaeron_questions(gaeron_md)
    minbub_q = extract_minbub_ox_questions(minbub_md)

    save_full_db(gaeron_q, minbub_q)
    print("\n✅ 완료!")
