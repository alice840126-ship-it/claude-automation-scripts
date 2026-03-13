#!/usr/bin/env python3
"""
CSV 파일 정렬 스크립트
- 동별 순서: S → A → B
- 층별 번갈아: A201 → B201 → A202 → B202...
"""

import csv
import re
from pathlib import Path

def extract_sort_key(row):
    """정렬 키 추출 - 층별로 A동 B동 번갈아"""
    building = row[1]  # 동별 (S, A, B)
    room = row[2]      # 호실 (201, 1001, etc.)

    # 동별 순서: S=0, A=1, B=2
    if building == 'S':
        building_order = 0
    elif building == 'A':
        building_order = 1
    elif building == 'B':
        building_order = 2
    else:
        building_order = 99

    # 호실에서 층과 번호 추출
    floor = 999  # 기본값을 크게 설정 (뒤로 보내기)
    room_num = 999

    if not room or room == '':
        pass
    elif room.startswith('S'):
        # S401 → 층=4, 번=01
        match = re.match(r'S(\d+)(\d{2})', room)
        if match:
            floor = int(match.group(1))
            room_num = int(match.group(2))
    elif building in ['A', 'B']:
        # A201, B201 → 층=2, 번=01 (3자리)
        # A1001, B1001 → 층=10, 번=01 (4자리)
        # A1101, B1101 → 층=11, 번=01 (4자리)
        room_digits = room[2:]  # '201', '1001', '1101'

        if len(room_digits) == 3:
            # 201 → 2층 01호
            floor = int(room_digits[0])
            room_num = int(room_digits[1:])
        elif len(room_digits) == 4:
            # 1001 → 10층 01호
            # 1101 → 11층 01호
            floor = int(room_digits[:2])
            room_num = int(room_digits[2:])
        elif len(room_digits) == 5:
            # 10001 → 100층 01호 (예외 처리)
            floor = int(room_digits[:3])
            room_num = int(room_digits[3:])

    # 정렬 우선순위:
    # 1. S동 먼저 (building_order=0)
    # 2. 그 다음 층별 (floor)
    # 3. 같은 층에서 호실 번호 (room_num) → A201, B201, A202, B202...
    # 4. 같은 호실에서 A→B 순서 (building_order)
    if building == 'S':
        return (0, floor, room_num, building, room)
    else:
        # A/B동은 층→호실→동 순서 (번갈아 나오게)
        return (1, floor, room_num, building_order, building, room)

# CSV 파일 경로
input_file = Path.home() / "Downloads/3. 덕은_8,9,10블럭_지산 매물장 - 6,7블럭.csv"
output_file = Path.home() / "Downloads/3. 덕은_8,9,10블럭_지산 매물장 - 6,7블럭_정렬.csv"

# CSV 읽기
rows = []
with open(input_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)  # 헤더 저장
    for row in reader:
        rows.append(row)

# 정렬
print(f"총 {len(rows)}개 행 정렬 중...")
sorted_rows = sorted(rows, key=extract_sort_key)

# 결과 저장
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(sorted_rows)

print(f"✅ 정렬 완료: {output_file}")

# 정렬 결과 미리보기 (첫 30개)
print("\n📋 정렬 결과 미리보기:")
print("-" * 100)
with open(output_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    print(f"{header[0]:<5} {header[1]:<5} {header[2]:<8}")
    print("-" * 100)
    for i, row in enumerate(reader):
        if i >= 30:
            break
        print(f"{row[0]:<5} {row[1]:<5} {row[2]:<8}")
