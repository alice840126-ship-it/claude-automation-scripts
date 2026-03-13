#!/usr/bin/env python3
"""
추출된 학습 자료를 정제하고 보기 좋게 정리
"""

import json
import re
from pathlib import Path

def refine_content(input_path, output_path):
    """학습 자료 정제"""

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    refined = {}

    for subject, chapters in data.items():
        refined[subject] = {}

        for chapter_name, content in chapters.items():
            # 불필요한 기호와 텍스트 정제
            content = clean_content(content)

            # 내용이 너무 짧으면 스킵
            if len(content) < 50:
                continue

            # 챕터명 정제
            clean_chapter_name = clean_chapter_name(chapter_name)

            # 중복 내용 제거하고 리스트로 변환
            points = split_into_points(content)

            if points:
                refined[subject][clean_chapter_name] = points

    # 정제된 데이터 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(refined, f, ensure_ascii=False, indent=2)

    return refined

def clean_content(content):
    """내용 정제"""
    # 불필요한 기호 제거
    content = re.sub(r'\[.*?\]\s*', '', content)  # [분류] 같은 태그 제거
    content = re.sub(r'\s+', ' ', content)  # 여러 공백을 하나로
    content = re.sub(r'→|←|↑|↓', '', content)  # 화살표 제거
    content = content.strip()

    return content

def clean_chapter_name(name):
    """챕터명 정제"""
    # 페이지 번호 제거
    name = re.sub(r'\d{2,}\s+\d{2,}\s+\d{2,}.*$', '', name)
    name = re.sub(r'\s+\d{2,}\s*\d{2,}\s*\d{2,}.*$', '', name)

    # 불필요한 기호 제거
    name = re.sub(r'^\d+\s+', '', name)
    name = re.sub(r'\s*[:：]\s*.*$', '', name)  # 콜론 뒤 내용 제거
    name = name.strip()

    # 너무 길면 자르기
    if len(name) > 50:
        name = name[:50]

    return name

def split_into_points(content):
    """내용을 개별 포인트로 분리"""
    # 파이프(|) 기준으로 분리
    raw_points = content.split('|')

    points = []
    seen = set()

    for point in raw_points:
        point = point.strip()

        # 길이 체크
        if 30 <= len(point) <= 500:
            # 불필요한 접두사 제거
            point = re.sub(r'^\[.*?\]\s*', '', point)

            # 중복 확인
            key = point[:50]  # 앞부분으로 중복 판단
            if key not in seen:
                seen.add(key)
                points.append(point)

    return points[:12]  # 챕터당 최대 12개

def format_for_display(data):
    """사람이 보기 좋은 형식으로 변환"""
    output = []

    for subject, chapters in data.items():
        output.append(f"\n{'='*60}")
        output.append(f"# {subject}")
        output.append(f"{'='*60}\n")

        for i, (chapter, points) in enumerate(chapters.items(), 1):
            output.append(f"## {i}. {chapter}")
            output.append("")

            for j, point in enumerate(points, 1):
                output.append(f"  {j}. {point}")

            output.append("")

    return "\n".join(output)

def refine_content(input_path, output_path):
    """학습 자료 정제"""

    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    refined = {}

    for subject, chapters in data.items():
        refined[subject] = {}

        for chapter_name, content in chapters.items():
            # 불필요한 기호와 텍스트 정제
            content = clean_content(content)

            # 내용이 너무 짧으면 스킵
            if len(content) < 50:
                continue

            # 챕터명 정제
            clean_name = clean_chapter_name(chapter_name)

            # 중복 내용 제거하고 리스트로 변환
            points = split_into_points(content)

            if points:
                refined[subject][clean_name] = points

    # 정제된 데이터 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(refined, f, ensure_ascii=False, indent=2)

    return refined

def main():
    input_path = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / 'study_content_detailed.json'
    output_json = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / 'study_content_final.json'
    output_md = Path.home() / 'Desktop' / '0. 자비스' / '공인중개사' / '학습자료_요약.md'

    print("📝 학습 자료 정제 중...")
    refined_data = refine_content(input_path, output_json)

    print(f"✅ JSON 저장 완료: {output_json}")
    print(f"   📊 개론: {len(refined_data.get('개론', {}))}개 챕터")
    print(f"   📊 민법: {len(refined_data.get('민법', {}))}개 챕터")

    # 마크다운으로도 저장
    md_content = format_for_display(refined_data)
    with open(output_md, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✅ 마크다운 저장 완료: {output_md}")

    # 통계
    total_points_gaeron = sum(len(pts) for pts in refined_data.get('개론', {}).values())
    total_points_minbub = sum(len(pts) for pts in refined_data.get('민법', {}).values())

    print(f"\n📈 통계")
    print(f"   개론 총 포인트: {total_points_gaeron}개")
    print(f"   민법 총 포인트: {total_points_minbub}개")
    print(f"   전체 포인트: {total_points_gaeron + total_points_minbub}개")

    # 샘플 출력
    print("\n=== 샘플 미리보기 (개론) ===")
    for i, (chapter, points) in enumerate(list(refined_data.get('개론', {}).items())[:3], 1):
        print(f"\n{i}. {chapter}")
        for point in points[:3]:
            print(f"   - {point[:80]}...")

if __name__ == "__main__":
    main()
