# macOS Full Disk Access 설정 가이드

## 목적
Launchd에서 자동으로 문자 요약 실행 (매일 5시)

## 설정 방법

### 1단계: 시스템 설정 열기
- `시스템 설정` (System Settings) 클릭
- 또는 단축키: `⌘ + Space` → "시스템 설정" 입력

### 2단계: 개인정보 보호 및 보안
- 왼쪽 메뉴에서 **개인정보 보호 및 보안** (Privacy & Security) 클릭

### 3단계: 전체 디스크 접근 권한
- **전체 디스크 접근 권한** (Full Disk Access) 클릭
- 우측하단 **잠금 아이콘** 클릭 (비밀번호 입력 필요)

### 4단계: 앱 추가 (3개 모두 추가)

#### 4-1. 터미널 추가
1. **+** 버튼 클릭
2. `⌘ + Shift + G` (폴더로 이동)
3. `/Applications` 입력
4. `Utilities` 폴더 → `Terminal` 선택
5. **열기** 클릭

#### 4-2. Python3 추가
1. **+** 버튼 클릭
2. `⌘ + Shift + G`
3. `/usr/bin/python3` 입력
4. **열기** 클릭

#### 4-3. launchd 추가 (선택)
1. **+** 버튼 클릭
2. `⌘ + Shift + G`
3. `/sbin/launchd` 입력
4. **열기** 클릭

### 5단계: 확인
- 3개 모두 체크박스가 켜져 있는지 확인
- 잠금 아이콘 다시 클릭

### 6단계: 재부팅 (권장)
- 맥 재부팅
- 재부팅 후 자동으로 실행됨

## 완료 후 테스트
```bash
launchctl unload ~/Library/LaunchAgents/com.user.daily-message-summary.plist
launchctl load ~/Library/LaunchAgents/com.user.daily-message-summary.plist
```

## 주의사항
- 권한 부여 후 재부팅 필수
- macOS 업데이트 후 권한 리셋될 수 있음
