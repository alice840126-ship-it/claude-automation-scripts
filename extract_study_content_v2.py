#!/usr/bin/env python3
"""
공인중개사 시험 대비 상세 학습 자료 추출 스크립트 v2
텍스트 블록 단위로 핵심 내용을 추출
"""

import json
import re
from pathlib import Path

def extract_content_from_md(file_path):
    """MD 파일에서 핵심 학습 내용 추출"""

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    subject = "개론" if "gaeron" in file_path.lower() else "민법"
    result = {}

    # 현재 챕터와 내용 추적
    current_chapter = None
    current_content = []

    # 챕터 시작 패턴 (숫자 + 제목 형식)
    chapter_start_pattern = re.compile(r'^(\d{2})\s+([^\n]{5,50})$')

    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue

        # 불필요한 줄 필터링
        if any(skip in line for skip in [
            'www.pmg.co.kr', '김백중', '박문각', '공인중개사', '필수서',
            '브랜드만쪽', '비평', '기픽', '제 37 회', '2026',
            '페이지', 'PDF', 'OCR'
        ]):
            continue

        # 챕터 시작 확인
        chapter_match = chapter_start_pattern.match(line)
        if chapter_match:
            # 이전 챕터 저장
            if current_chapter and current_content:
                key_points = extract_key_points_from_lines(current_content)
                if key_points:
                    result[current_chapter] = " | ".join(key_points[:10])

            # 새 챕터 시작
            current_chapter = chapter_match.group(2).strip()
            current_content = []
            continue

        # 내용 수집 (의미 있는 줄만)
        if current_chapter and is_meaningful_line(line):
            current_content.append(line)

    # 마지막 챕터 저장
    if current_chapter and current_content:
        key_points = extract_key_points_from_lines(current_content)
        if key_points:
            result[current_chapter] = " | ".join(key_points[:10])

    return subject, result

def is_meaningful_line(line):
    """의미 있는 내용 라인인지 판단"""
    # 너무 짧거나 기호만 있는 줄 제외
    if len(line) < 10:
        return False

    # 기호로만 구성된 줄 제외
    if re.match(r'^[=_\-※○●■▶▷□▽▼▲△☆★]+$', line):
        return False

    # 숫자나 페이지 번호만 있는 줄 제외
    if re.match(r'^\d+$', line):
        return False

    # 계산문제나 수식 관련 제외
    if any(keyword in line for keyword in ['계산문제', '수식', '그래프', '출처:']):
        return False

    return True

def extract_key_points_from_lines(lines):
    """라인들에서 핵심 포인트 추출"""
    points = []
    full_text = " ".join(lines)

    # 정의 패턴
    def_patterns = [
        r'([^。.\n]{20,200})(?:이란|란|是指)\s*[:：]?\s*([^。.\n]{10,200})',
        r'([^。.\n]{15,150})\s*[:：]\s*(?:의\s*)?(?:정의|뜻|개념)\s*(?:은|는)\s*([^。.\n]{10,200})',
    ]

    # 분류/유형 패턴
    type_patterns = [
        r'([^。.\n]{15,200})(?:의\s*)?(?:종류|유형|분류|구분)\s*[:：]?\s*([^。.\n]{15,200})',
        r'([^。.\n]{20,250})(?:은|는|은)\s*(?:[^。.\n]{10,150})\s*(?:로\s*나뉜다|분류된다|구분된다)',
    ]

    # 예외/단서 패턴
    except_patterns = [
        r'(?:다만|단|예외|단서)(?:외에)?[:：]?\s*([^。.\n]{20,250})',
        r'([^。.\n]{20,250})(?:의\s*)?(?:예외|단서|특례)',
    ]

    # 비교 패턴
    compare_patterns = [
        r'비교\s*[:：]?\s*([^。.\n]{20,300})',
        r'차이점\s*[:：]?\s*([^。.\n]{20,300})',
        r'([^。.\n]{30,400})(?:과|와)\s*([^。.\n]{10,100})\s*(?:의\s*)?차이',
    ]

    # 일반 설명 패턴 (긴 문장)
    general_patterns = [
        r'([^。.\n]{50,400})[.。]',
        r'•\s*([^。\n]{30,300})',
        r'①\s*([^。\n]{30,300})',
    ]

    all_patterns = [
        ('정의', def_patterns),
        ('분류', type_patterns),
        ('예외', except_patterns),
        ('비교', compare_patterns),
        ('일반', general_patterns),
    ]

    for category, patterns in all_patterns:
        for pattern in patterns:
            matches = re.finditer(pattern, full_text)
            for match in matches:
                # 첫 번째 캡처 그룹 사용
                captured = match.group(1) if match.groups() else match.group(0)
                captured = captured.strip()

                # 불필요한 내용 필터링
                if any(skip in captured for skip in [
                    '계산문제', '수식', '그래프', '출처:', '페이지:',
                    '참고:', '○○○', 'XXX', '---', '→', '←'
                ]):
                    continue

                # 길이 체크
                if 25 <= len(captured) <= 400:
                    # 중복 확인
                    if not any(captured in p for p in points):
                        points.append(f"[{category}] {captured}")

    return points

def main():
    files = [
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/gaeron. ocr.md',
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'
    ]

    result = {}

    for file_path in files:
        print(f"Processing: {file_path}")
        subject, chapters = extract_content_from_md(file_path)

        if subject not in result:
            result[subject] = {}

        # 챕터 정렬 후 추가 (최대 20개)
        sorted_chapters = dict(list(chapters.items())[:20])
        result[subject].update(sorted_chapters)

        print(f"  - 추출된 챕터: {len(sorted_chapters)}개")

    # JSON 저장
    output_path = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / 'study_content_detailed.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 추출 완료!")
    print(f"📁 저장 위치: {output_path}")
    print(f"📊 개론 챕터: {len(result.get('개론', {}))}개")
    print(f"📊 민법 챕터: {len(result.get('민법', {}))}개")

    # 미리보기
    print("\n=== 상세 미리보기 ===")
    for subject, chapters in result.items():
        print(f"\n【{subject}】 ({len(chapters)}개 챕터)")
        for i, (chapter, content) in enumerate(list(chapters.items())[:5], 1):
            # 내용이 너무 길면 자르기
            preview = content[:150] + "..." if len(content) > 150 else content
            print(f"\n{i}. {chapter}")
            print(f"   {preview}")

if __name__ == "__main__":
    main()
