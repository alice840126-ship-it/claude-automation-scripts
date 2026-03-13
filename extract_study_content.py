#!/usr/bin/env python3
"""
공인중개사 시험 대비 상세 학습 자료 추출 스크립트
개론 및 민법 MD 파일에서 각 챕터별 핵심 개념, 정의, 예외사항, 판례를 추출
"""

import json
import re
from pathlib import Path

def parse_markdown_file(file_path):
    """마크다운 파일을 챕터별로 파싱"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 파일명에서 과목 구분
    subject = "개론" if "gaeron" in file_path.lower() else "민법"

    # 챕터 구분 패턴 (### 으로 시작하는 주제들)
    chapter_pattern = r'(#{3,6}\s+[\\[\\[]?([^\\]\\]]+))[^#\n]*\n(.*?)(?=\n#{3,6}\s+[\\[\\[]?|$)'

    chapters = {}
    matches = re.finditer(chapter_pattern, content, re.DOTALL)

    for match in matches:
        chapter_title = match.group(2).strip()
        chapter_content = match.group(3).strip()

        # 불필요한 챕터 필터링
        if any(keyword in chapter_title for keyword in ['김백중', '박문각', '공인중개사', '필수서', '2026', '합격']):
            continue

        # 챕터명 정제
        chapter_title = re.sub(r'^[\d\.\s]+', '', chapter_title)
        chapter_title = chapter_title.split('(')[0].strip()

        if len(chapter_title) > 50 or len(chapter_title) < 2:
            continue

        if chapter_title not in chapters:
            chapters[chapter_title] = []

        # 챕터 내용에서 핵심 내용 추출
        key_points = extract_key_points(chapter_content)
        chapters[chapter_title].extend(key_points)

    return subject, chapters

def extract_key_points(content):
    """챕터 내용에서 핵심 포인트 추출"""
    points = []

    # 불필요한 부분 제거 (계산문제, 그래프 설명 등)
    content = re.sub(r'계산문제.*?\n\n', '', content, flags=re.DOTALL)
    content = re.sub(r'그래프.*?\n\n', '', content, flags=re.DOTALL)
    content = re.sub(r'수식.*?\n\n', '', content, flags=re.DOTALL)
    content = re.sub(r'######? *\d+\.?\s*', '', content)  # 번호 제거

    # 정의 관련 패턴
    definition_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?([^*\n]{10,150})(?:이란|란|是指)\s*[:：]?\s*([^.\n]{10,200})[.。])',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?([^*\n]{10,100})\s*[:：]\s*(?:의\s*)?(?:정의|뜻|개념)\s*(?:은|는|란)\s*([^.\n]{10,200})[.。])',
    ]

    # 법적 규정 패턴
    legal_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?법\s*제?\s*(\d+조)\s*[:：]?\s*([^.\n]{15,300})[.。])',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(부동산법|공인중개사법|민법)\s*[:：]?\s*([^.\n]{15,200})[.。])',
    ]

    # 유형/분류 패턴
    classification_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(?:[\w\s]{5,30})\s*(?:의\s*)?(?:종류|유형|분류|구분)\s*[:：]?\s*([^.\n]{15,200})[.。])',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(?:[\w\s]{5,30})\s*(?:은|는)\s*(?:[^.\n]{10,100})\s*(?:로\s*나뉜다|분류된다|구분된다)[.。]?\s*([^.\n]{10,200})[.。]?)',
    ]

    # 예외사항 패턴
    exception_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(?:다만|However|단|예외)(?:외에)?[:：]?\s*([^.\n]{15,200})[.。]',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?([^.\n]{15,200})(?:의\s*)?(?:예외|단서|특례)[.。]?',
    ]

    # 판례/기출 패턴
    precedent_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(판례|기출|출제)(?:[：:])?\s*([^.\n]{20,300})[.。]',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?(?:대법원| Supreme Court)[\s:*]([^.\n]{20,300})[.。])',
    ]

    # 비교 패턴
    comparison_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?비교\s*[:：:]\s*([^.\n]{20,300})',
        r'(?:(?:^|\n)[\s]*(?:•?\s*)?(?:\*?\s*)?차이점\s*[:：]?\s*([^.\n]{20,300})',
    ]

    # 일반 핵심 내용 (bullet points)
    general_patterns = [
        r'(?:(?:^|\n)[\s]*(?:•|※|○|●)\s*([^*\n]{15,250})[.。]?\s*(?=\n|$|•|※|○|●))',
        r'(?:(?:^|\n)[\s]*(?:\d+[\).])\s*([^*\n]{15,250})[.。]?\s*(?=\n|$|\d+[\).]))',
    ]

    all_patterns = [
        ('definition', definition_patterns),
        ('legal', legal_patterns),
        ('classification', classification_patterns),
        ('exception', exception_patterns),
        ('precedent', precedent_patterns),
        ('comparison', comparison_patterns),
        ('general', general_patterns),
    ]

    for category, patterns in all_patterns:
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                if category == 'definition':
                    term = match.group(1).strip()
                    definition = match.group(2).strip() if len(match.groups()) > 1 else ''
                    point = f"{term}의 정의: {definition}" if definition else term
                elif category == 'legal':
                    article = match.group(1).strip()
                    content_text = match.group(2).strip() if len(match.groups()) > 1 else ''
                    point = f"법 제{article}조: {content_text}" if content_text else f"법 제{article}조 관련"
                elif category == 'precedent':
                    source = match.group(1).strip()
                    text = match.group(2).strip() if len(match.groups()) > 1 else source
                    point = f"{source}: {text}"
                else:
                    point = match.group(1).strip() if match.group(1) else match.group(0).strip()

                # 불필요한 내용 필터링
                if any(skip in point for skip in [
                    '계산문제', '수식', '그래프', '출처:', '페이지:',
                    '참고:', '※', '○○○', 'XXX', '---'
                ]):
                    continue

                # 중복 제거 및 길이 체크
                if 20 <= len(point) <= 300 and point not in points:
                    points.append(point)

    return points[:15]  # 챕터당 최대 15개

def main():
    # 파일 경로
    files = [
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/gaeron. ocr.md',
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'
    ]

    result = {}

    for file_path in files:
        print(f"Processing: {file_path}")
        subject, chapters = parse_markdown_file(file_path)

        if subject not in result:
            result[subject] = {}

        # 챕터별로 정리 (최대 20개 챕터)
        for chapter_name, points in list(chapters.items())[:20]:
            if points:  # 내용이 있는 챕터만
                # 포인트들을 하나의 문장으로 결합
                combined_content = " | ".join(points)
                result[subject][chapter_name] = combined_content

    # JSON으로 저장
    output_path = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / 'study_content.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 추출 완료!")
    print(f"📁 저장 위치: {output_path}")
    print(f"📊 개론 챕터: {len(result.get('개론', {}))}개")
    print(f"📊 민법 챕터: {len(result.get('민법', {}))}개")

    # 미리보기
    print("\n=== 미리보기 ===")
    for subject, chapters in result.items():
        print(f"\n【{subject}】")
        for i, (chapter, content) in enumerate(list(chapters.items())[:3], 1):
            preview = content[:100] + "..." if len(content) > 100 else content
            print(f"{i}. {chapter}: {preview}")

if __name__ == "__main__":
    main()
