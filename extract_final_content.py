#!/usr/bin/env python3
"""
공인중개사 시험 대비 핵심 내용 최종 추출 스크립트
OCR 잡음을 제거하고 정의, 예외, 판례를 중심으로 추출
"""

import json
import re
from pathlib import Path

def extract_clean_content(file_path):
    """파일에서 깨끗한 내용 추출"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    subject = "개론" if "gaeron" in file_path.lower() else "민법"

    # 불필요한 부분 제거
    content = remove_noise(content)

    # 챕터 추출
    chapters = extract_chapters(content)

    return subject, chapters

def remove_noise(text):
    """OCR 잡음 제거"""

    # 불필요한 헤더/푸터 제거
    noise_patterns = [
        r'제\s*\d+\s*회.*?www\.pmg\.co\.kr',
        r'김백중\s*필수서',
        r'박문각\s*공인중개사',
        r'2026.*?공인중개사',
        r'필수서.*?부동산학개론',
        r'브랜드만쪽|비평|기픽',
        r'페이지\s*\d+',
        r'확인학습.*?OX\s*\d+',
        r'대표기출.*?\d+\s*회',
        r'→|←|↑|↓|▲|△|▽|▼',
        r'_+',  # 밑줄
        r'-{30,}',  # 긴 대시
        r'={30,}',  # 긴 등호
    ]

    for pattern in noise_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE | re.MULTILINE)

    # 여러 공백을 하나로
    text = re.sub(r'\s+', ' ', text)

    return text

def extract_chapters(content):
    """챕터별로 내용 추출"""

    chapters = {}

    # 챕터 패턴: 숫자로 시작하는 주제
    # 예: "01 부동산학 개요", "02 부동산의 분류"
    chapter_pattern = re.compile(
        r'(\d{2})\s+([A-Za-z가-힣\s]{5,40})(?=\s*\d{2}\s+[A-Za-z가-힣]|$)',
        re.MULTILINE
    )

    matches = list(chapter_pattern.finditer(content))

    for i, match in enumerate(matches):
        chapter_num = match.group(1)
        chapter_title = match.group(2).strip()

        # 다음 챕터까지의 내용 추출
        start_pos = match.end()
        end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        chapter_content = content[start_pos:end_pos].strip()

        # 내용에서 핵심 포인트 추출
        key_points = extract_key_points(chapter_content)

        if key_points:
            chapters[chapter_title] = key_points

        # 최대 20개 챕터만
        if len(chapters) >= 20:
            break

    return chapters

def extract_key_points(text):
    """텍스트에서 핵심 포인트 추출"""

    points = []

    # 정의 패턴: "~란", "~이다", "~를 말한다"
    definition_patterns = [
        r'([A-Za-z가-힣0-9()]{3,30})\s*(?:란|은|는)\s*([^\n。.]{10,150})(?:을|를\s*말한다|이다)[。.]',
        r'([^\n]{15,200})(?:의\s*)?정의\s*[:：]?\s*([^\n。.]{10,150})',
        r'([^\n]{20,250})\s*[:：]\s*([^\n。.]{10,150})(?:\s*이란|란)',
    ]

    # 법적 규정 패턴
    legal_patterns = [
        r'법\s*제?(\d+)조\s*[:：]?\s*([^\n。.]{20,250})[。.]',
        r'(민법|공인중개사법|부동산법)\s*[:：]?\s*([^\n。.]{20,250})[。.]',
    ]

    # 종류/분류/유형 패턴
    classification_patterns = [
        r'([A-Za-z가-힣0-9()]{3,30})\s*(?:의\s*)?(?:종류|유형|분류|구분)\s*[:：]?\s*([^\n。.]{20,250})',
        r'([^\n]{20,250})\s*(?:로|으로)\s*(?:나뉜다|분류된다|구분된다)',
    ]

    # 예외/단서 패턴
    exception_patterns = [
        r'(?:다만|단|예외외에?|단서)\s*[:：]?\s*([^\n。.]{20,250})[。.]',
        r'([^\n]{20,250})(?:의\s*)?(?:예외|단서|특례)\s*(?:으로|로)\s*([^\n。.]{10,150})',
    ]

    # 비교/차이점 패턴
    comparison_patterns = [
        r'비교\s*[:：]?\s*([^\n]{30,400})',
        r'차이점\s*[:：]?\s*([^\n]{30,400})',
        r'([^\n]{30,400})\s*(?:과|와)\s*([^\n]{10,50})\s*(?:의\s*)?차이',
    ]

    # 판례/기출 패턴
    precedent_patterns = [
        r'(?:판례|기출|출제)\s*[:：]?\s*([^\n。.]{30,400})[。.]',
        r'(?:대법원| Supreme Court)\s*[:：]?\s*([^\n。.]{30,400})',
    ]

    # 일반 중요 내용 (구조화된 문장)
    general_patterns = [
        r'①\s*([^\n。.]{30,300})[。.]',
        r'②\s*([^\n。.]{30,300})[。.]',
        r'③\s*([^\n。.]{30,300})[。.]',
        r'⑴\s*([^\n。.]{30,300})[。.]',
        r'⑵\s*([^\n。.]{30,300})[。.]',
        r'⑶\s*([^\n。.]{30,300})[。.]',
    ]

    all_patterns = [
        ('정의', definition_patterns),
        ('법조', legal_patterns),
        ('분류', classification_patterns),
        ('예외', exception_patterns),
        ('비교', comparison_patterns),
        ('판례', precedent_patterns),
        ('일반', general_patterns),
    ]

    seen = set()

    for category, patterns in all_patterns:
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                # 캡처 그룹에서 내용 추출
                if match.lastindex:
                    # 여러 그룹이 있는 경우 결합
                    captured = ' '.join([g.strip() for g in match.groups() if g.strip()])
                else:
                    captured = match.group(0).strip()

                # 불필요한 내용 필터링
                if not is_valid_content(captured):
                    continue

                # 중복 확인
                key = captured[:50]
                if key in seen:
                    continue
                seen.add(key)

                # 카테고시 라벨 추가
                point = f"[{category}] {captured}"
                points.append(point)

                # 최대 12개 포인트
                if len(points) >= 12:
                    break

            if len(points) >= 12:
                break
        if len(points) >= 12:
            break

    return points

def is_valid_content(text):
    """유효한 내용인지 확인"""

    # 길이 체크
    if len(text) < 20 or len(text) > 500:
        return False

    # 불필요한 키워드 필터링
    skip_keywords = [
        '계산문제', '수식', '그래프', '출처:',
        '페이지:', '참고:', '○○○', 'XXX',
        '---', '→', '←', 'www.pmg.co.kr',
        '김백중', '박문각',
    ]

    for keyword in skip_keywords:
        if keyword in text:
            return False

    # 의미 있는 단어 포함 확인
    meaningful_words = [
        '이다', '하다', '한다', '된다', '말한다',
        '규정', '법', '조', '의', '를', '은', '는',
        '분류', '종류', '유형', '예외', '단서',
        '판례', '기출', '비교',
    ]

    if not any(word in text for word in meaningful_words):
        return False

    return True

def main():
    files = [
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/gaeron. ocr.md',
        '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/마크다운 형식/minbub.ocr.md'
    ]

    result = {}

    for file_path in files:
        print(f"Processing: {file_path}")
        subject, chapters = extract_clean_content(file_path)

        if subject not in result:
            result[subject] = {}

        result[subject].update(chapters)
        print(f"  - 추출된 챕터: {len(chapters)}개")

    # JSON 저장
    output_path = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / '학습자료_최종.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 저장 완료: {output_path}")

    # 마크다운으로도 저장
    md_path = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / '학습자료_최종.md'

    with open(md_path, 'w', encoding='utf-8') as f:
        for subject, chapters in result.items():
            f.write(f"\n{'='*70}\n")
            f.write(f"# {subject}\n")
            f.write(f"{'='*70}\n\n")

            for i, (chapter, points) in enumerate(chapters.items(), 1):
                f.write(f"## {i}. {chapter}\n\n")
                for point in points:
                    f.write(f"  - {point}\n")
                f.write("\n")

    print(f"✅ 마크다운 저장 완료: {md_path}")

    # 통계
    for subject, chapters in result.items():
        total_points = sum(len(pts) for pts in chapters.values())
        print(f"\n📊 {subject}: {len(chapters)}개 챕터, {total_points}개 포인트")

    # 샘플 출력
    print("\n=== 샘플 미리보기 ===")
    for subject, chapters in result.items():
        print(f"\n【{subject}】")
        for i, (chapter, points) in enumerate(list(chapters.items())[:2], 1):
            print(f"\n{i}. {chapter}")
            for point in points[:3]:
                print(f"   {point[:100]}...")

if __name__ == "__main__":
    main()
