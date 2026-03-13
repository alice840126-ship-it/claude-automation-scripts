#!/usr/bin/env python3
"""
공인중개사 시험 학습 자료 최종 추출
개론과 민법 모두에서 핵심 내용 추출
"""

import json
import re
from pathlib import Path

def extract_gaeron(file_path):
    """개론 파일 추출"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chapters = {}

    # 챕터 패턴: "01 부동산학 개요" 형식
    chapter_pattern = re.compile(r'^(\d{2})\s+([A-Za-z가-힣\s]{5,40})$', re.MULTILINE)

    matches = list(chapter_pattern.finditer(content))

    for i, match in enumerate(matches):
        chapter_title = match.group(2).strip()

        # 다음 챕터까지의 내용
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        chapter_text = content[start:end]

        # 핵심 포인트 추출
        points = extract_points(chapter_text)
        if points:
            chapters[chapter_title] = points

        if len(chapters) >= 15:
            break

    return chapters

def extract_minbub(file_path):
    """민법 파일 추출"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    chapters = {}

    # 실제 내용 시작점 찾기 (## 01 민법총칙 이후)
    main_start = content.find('## 01')
    if main_start == -1:
        main_start = content.find('01 I 총설')

    if main_start == -1:
        return chapters

    main_content = content[main_start:]

    # 챕터 패턴: "01 I 총설", "02 I 목적의 확정성" 형식
    chapter_pattern = re.compile(
        r'^\d{2}\s+[IVX]+\.?\s*([A-Za-z가-힣0-9,\s]{10,60})$',
        re.MULTILINE
    )

    matches = list(chapter_pattern.finditer(main_content))

    for i, match in enumerate(matches):
        chapter_title = match.group(1).strip()

        # 다음 챕터까지의 내용
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(main_content)
        chapter_text = main_content[start:end]

        # 핵심 포인트 추출
        points = extract_points(chapter_text, is_civil_law=True)
        if points:
            chapters[chapter_title] = points

        if len(chapters) >= 20:
            break

    return chapters

def extract_points(text, is_civil_law=False):
    """텍스트에서 핵심 포인트 추출"""

    points = []
    seen = set()

    # 개론용 패턴
    if not is_civil_law:
        patterns = [
            # 정의
            (r'[A-Za-z가-힣0-9()]{2,20}\s*(?:란|은|는)\s*[^\n。.]{15,200}(?:을|를\s*말한다|이다|한다)[。.]', '정의'),
            # 법적 규정
            (r'법\s*제?\s*\d+조\s*[:：]?\s*[^\n。.]{20,250}[。.]', '법조'),
            # 분류
            (r'[A-Za-z가-힣0-9()]{2,20}\s*(?:의\s*)?(?:종류|유형|분류|구분)\s*[:：]?\s*[^\n。.]{20,200}', '분류'),
            # 예외
            (r'(?:다만|단|예외외에?)\s*[:：]?\s*[^\n。.]{20,200}[。.]', '예외'),
            # 번호 매겨진 내용
            (r'[①②③⑴⑵⑶]\s*[^\n。.]{30,300}[。.]', '핵심'),
        ]
    else:
        # 민법용 패턴
        patterns = [
            # OX 문제에서의 설명
            (r'-\s*([^\n]{20,300})', '핵심'),
            # 번호 문장
            (r'^\d+\.\s*([^\n。.]{20,300})[。.]', '핵심'),
            # 정의
            (r'[^\n]{20,200}(?:이란|란|은|는)\s*[^\n。.]{10,150}(?:이다|한다)[。.]', '정의'),
            # 법조
            (r'법\s*제?\s*\d+조\s*[:：]?\s*[^\n。.]{20,250}', '법조'),
            # 예외/단서
            (r'(?:다만|단|예외)\s*[:：]?\s*[^\n。.]{20,200}', '예외'),
        ]

    for pattern, category in patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            # 캡처된 내용 추출
            if match.groups():
                captured = match.group(1).strip() if match.group(1) else match.group(0).strip()
            else:
                captured = match.group(0).strip()

            # 불필요한 기호 제거
            captured = re.sub(r'^[-\s]+', '', captured)
            captured = re.sub(r'\s+', ' ', captured)

            # 유효성 검사
            if not is_valid_point(captured):
                continue

            # 중복 확인
            key = captured[:60]
            if key in seen:
                continue
            seen.add(key)

            point = f"[{category}] {captured}"
            points.append(point)

            if len(points) >= 10:
                break

        if len(points) >= 10:
            break

    return points

def is_valid_point(text):
    """유효한 포인트인지 확인"""

    # 길이 체크
    if len(text) < 25 or len(text) > 400:
        return False

    # 불필요한 내용 필터링
    skip_keywords = [
        '계산문제', '수식', '그래프', 'www.pmg.co.kr',
        '김백중', '박문각', '확인학습', '대표기출',
        '→', '←', '↑', '↓',
    ]

    text_lower = text.lower()
    for keyword in skip_keywords:
        if keyword.lower() in text_lower:
            return False

    # 의미 있는 단어 포함 확인
    meaningful_words = [
        '이다', '하다', '한다', '된다', '말한다', '아니다',
        '규정', '법', '조', '분류', '종류', '유형',
        '예외', '단서', '판례', '기출',
        '유효', '무효', '취소', '효력',
    ]

    if not any(word in text for word in meaningful_words):
        return False

    return True

def main():
    # 파일 경로
    gaeron_path = '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/gaeron. ocr.md'
    minbub_path = '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'

    result = {}

    print("📚 개론 추출 중...")
    result['개론'] = extract_gaeron(gaeron_path)
    print(f"  ✅ {len(result['개론'])}개 챕터 추출 완료")

    print("\n📚 민법 추출 중...")
    result['민법'] = extract_minbub(minbub_path)
    print(f"  ✅ {len(result['민법'])}개 챕터 추출 완료")

    # JSON 저장
    output_json = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / '학습자료_완성.json'
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n💾 JSON 저장: {output_json}")

    # 마크다운 저장
    output_md = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / '학습자료_완성.md'
    with open(output_md, 'w', encoding='utf-8') as f:
        for subject, chapters in result.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"# {subject} 학습 자료\n")
            f.write(f"{'='*70}\n\n")

            for i, (chapter, points) in enumerate(chapters.items(), 1):
                f.write(f"## {i}. {chapter}\n\n")
                for point in points:
                    f.write(f"{point}\n")
                f.write("\n")

    print(f"💾 마크다운 저장: {output_md}")

    # 통계
    print("\n📊 추출 통계")
    for subject, chapters in result.items():
        total_points = sum(len(pts) for pts in chapters.values())
        avg_points = total_points / len(chapters) if chapters else 0
        print(f"  {subject}: {len(chapters)}개 챕터, 총 {total_points}개 포인트 (평균 {avg_points:.1f}개/챕터)")

    # 샘플
    print("\n📖 샘플 미리보기")
    for subject, chapters in result.items():
        print(f"\n【{subject}】")
        for i, (chapter, points) in enumerate(list(chapters.items())[:3], 1):
            print(f"\n{i}. {chapter}")
            for point in points[:2]:
                preview = point[:120] + "..." if len(point) > 120 else point
                print(f"   {preview}")

if __name__ == "__main__":
    main()
