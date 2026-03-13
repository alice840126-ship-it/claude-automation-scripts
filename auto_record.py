#!/usr/bin/env python3
"""
자동 기록 시스템 - 4곳에 동시 저장
"""

import sys
import json
from pathlib import Path
from datetime import datetime
import re

NOW = datetime.now()
TIMESTAMP = NOW.strftime("%Y-%m-%d %H:%M")
TIME_ONLY = NOW.strftime("%H:%M")
TODAY_DATE = NOW.strftime("%Y-%m-%d")
TIME_ONLY_SHORT = NOW.strftime("%H:%M")

def record_all(content):
    """4곳에 기록"""
    
    print(f"\n📝 4곳에 기록 시작...\n")
    
    # 1. work_log.json
    try:
        work_log = Path.home() / ".claude" / "work_log.json"
        
        if work_log.exists():
            with open(work_log, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # current_session에 추가
            new_entry = {
                "time": TIME_ONLY_SHORT,
                "description": content,
                "status": "완료"
            }
            data["current_session"].append(new_entry)
            data["last_update"] = NOW.isoformat()
        else:
            # 새로 생성
            data = {
                "current_session": [
                    {
                        "time": TIME_ONLY_SHORT,
                        "description": content,
                        "status": "완료"
                    }
                ],
                "last_update": NOW.isoformat()
            }
        
        with open(work_log, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✅ 1. work_log.json")
    except Exception as e:
        print(f"❌ 1. work_log.json: {e}")
    
    # 2. session_log.md
    try:
        session_log = Path.home() / ".claude" / "session_log.md"
        
        with open(session_log, 'a', encoding='utf-8') as f:
            f.write(f"\n- [{TIME_ONLY_SHORT}] {content}")
        
        print("✅ 2. session_log.md")
    except Exception as e:
        print(f"❌ 2. session_log.md: {e}")
    
    # 3. shared_context.md - 최근 활동 로그 섹션 업데이트
    try:
        shared = Path.home() / ".claude-unified" / "shared_context.md"
        
        with open(shared, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 터미널 섹션에 추가
        terminal_pattern = r'(### 터미널 \(Claude Code\)\n)(.*?)(\n### 텔레그램 봇)'
        
        terminal_match = re.search(terminal_pattern, text, re.DOTALL)
        
        if terminal_match:
            section_start = terminal_match.group(1)
            section_content = terminal_match.group(2)
            section_end = terminal_match.group(3)
            
            # 새 로그 추가
            new_log = f"- {TODAY_DATE} {TIME_ONLY_SHORT} - {content}"
            updated_content = section_content.rstrip() + f"\n{new_log}\n"
            
            # 전체 업데이트
            updated = text.replace(
                section_start + section_content + section_end,
                section_start + updated_content + section_end
            )
            
            with open(shared, 'w', encoding='utf-8') as f:
                f.write(updated)
            
            print("✅ 3. shared_context.md (최근 활동 로그)")
        else:
            # 패턴 없으면 맨 아래에 추가
            with open(shared, 'a', encoding='utf-8') as f:
                f.write(f"\n## {TIMESTAMP}\n{content}\n")
            
            print("✅ 3. shared_context.md (맨 아래 추가)")
            
    except Exception as e:
        print(f"❌ 3. shared_context.md: {e}")
    
    # 4. 옵시디언 데일리 노트
    try:
        daily_path = Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents/류웅수/30. 자원 상자/01. 데일리 노트"
        daily_file = daily_path / f"{TODAY_DATE}.md"
        
        with open(daily_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 작업 로그 섹션에 추가
        new_log = f"- [{TIME_ONLY_SHORT}] {content}"
        
        # 작업 로그 섹션 찾기
        log_match = re.search(r'(## 작업 로그\n.*?)(\n##|\Z)', text, re.DOTALL)
        
        if log_match:
            log_section = log_match.group(1)
            rest = log_match.group(2)
            
            # 새 로그 추가
            updated_log = log_section.rstrip() + f"\n{new_log}\n"
            
            # 전체 업데이트
            updated = text.replace(log_section + rest, updated_log + rest)
            
            with open(daily_file, 'w', encoding='utf-8') as f:
                f.write(updated)
            
            print("✅ 4. 옵시디언 데일리 노트")
        else:
            print("⚠️  4. 옵시디언: 작업 로그 섹션 없음")
            
    except Exception as e:
        print(f"❌ 4. 옵시디언: {e}")
    
    print(f"\n✅ 기록 완료! ({TIMESTAMP})\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        content = " ".join(sys.argv[1:])
        record_all(content)
    else:
        print("사용법: python3 auto_record.py \"기록할 내용\"")
