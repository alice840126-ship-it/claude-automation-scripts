#!/usr/bin/env python3
"""
데일리 노트 자동 생성 스크립트
매일 아침 7시 실행 (Launchd)
"""

import os
import datetime
from pathlib import Path

# 설정
DAILY_NOTE_DIR = "/Users/oungsooryu/Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수/30. 자원 상자/01. 데일리 노트"

def get_daily_note_template(date: datetime.date) -> str:
    """데일리 노트 템플릿 생성"""
    date_str = date.strftime('%Y-%m-%d')
    weekday = date.strftime('%a')

    template = f"""---
TYPE: "[[{date_str}]]"
tags:
  - daily-note
date: {date_str}
date created: {date_str}
date modified: {date_str}
---

## 핵심 목표
- 운동
- 명상은 언제나 늘 가까이
- 나는 2026년에 공인중개사 1차 합격했다.
- 나는 돈이 들어오는 수많은 파이프라인으로 일하지 않아도 세계를 여행하며 문화를 즐긴다.
- 나는 매달 3000만원의 실적을 올린다.
- 나는 표현을 잘 하는 person이고, 애정표현도 잘 하며, 잘 웃는다.
- 주변의 생각, 말을 의식하지 말고, 내가 스스로 당당하게 열심히 살면 된다.
- 지금 이순간이 최고다.

---

## 오늘의 개요


### 핵심 목표


### 오늘의 일정


---

## 작업 로그




---

## 아이디어 & 노트




---

## 회고

### 오늘의 성과 및 배운 점


### 개선할 점 및 내일 할 일

"""
    return template

def main():
    """메인 함수"""
    today = datetime.date.today()
    date_str = today.strftime('%Y-%m-%d')
    filename = f"{date_str}.md"
    filepath = os.path.join(DAILY_NOTE_DIR, filename)

    # 이미 존재하면 건너뜀
    if os.path.exists(filepath):
        print(f"✅ 데일리 노트 이미 존재: {filename}")
        return 0

    # 디렉토리 확인
    os.makedirs(DAILY_NOTE_DIR, exist_ok=True)

    # 템플릿 생성
    content = get_daily_note_template(today)

    # 파일 저장
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ 데일리 노트 생성 완료: {filename}")
    return 0

if __name__ == "__main__":
    exit(main())
