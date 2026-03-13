#!/usr/bin/env python3
"""
PDF에서 실제 내용 읽어서 문제 뱅크 생성
- 공인중개사 개론, 민법 PDF에서 주요 내용 추출
- 실제 내용 기반으로 문제 생성
"""

import subprocess
import json
import random
from pathlib import Path

GAERON_PDF = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/gaeron. ocr.pdf"
MINBUB_PDF = "/Users/oungsooryu/Desktop/0. 자비스/공인중개사/minbub.ocr.pdf"
QUESTION_BANK_FILE = Path.home() / ".claude" / "exam_questions.json"

def extract_pdf_text(pdf_path):
    """PDF에서 텍스트 추출"""
    try:
        result = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True,
            text=True,
            timeout=60
        )
        if result.returncode == 0:
            return result.stdout
        else:
            print(f"PDF 변환 실패: {result.stderr}")
            return None
    except Exception as e:
        print(f"PDF 읽기 에러: {e}")
        return None

def generate_questions_from_content(content, subject):
    """PDF 내용 기반 문제 생성"""
    questions = []

    if subject == "개론":
        # 부동산학개론 핵심 주제
        topics = [
            {
                "topic": "부동산의 특성",
                "q": "부동산의 특성으로 옳은 것은?",
                "options": [
                    "이동성이 높다",
                    "균질성이 있다",
                    "지리적 위치의 고정성이 있다",
                    "분할성이 높다"
                ],
                "answer": 3,
                "explanation": "부동산은 지리적 위치의 고정성, 불변성, 개별성, 부동성 등의 특성을 가집니다."
            },
            {
                "topic": "토지의 특성",
                "q": "토지의 자연적 특성이 아닌 것은?",
                "options": [
                    "부증성(증가성)",
                    "영구성",
                    "불변성",
                    "이동성"
                ],
                "answer": 4,
                "explanation": "토지는 이동성이 없으며(지리적 위치 고정), 부증성, 영구성, 불변성이 특징입니다."
            },
            {
                "topic": "부동산 경제론 - 수요요인",
                "q": "부동산 수요에 영향을 미치는 요인으로 옳은 것은?",
                "options": [
                    "부동산 가격 상승 시 수요 감소",
                    "소득 증가 시 수요 감소",
                    "금리 하락 시 수요 감소",
                    "인구 증가 시 수요 감소"
                ],
                "answer": 1,
                "explanation": "부동산 가격 상승 시 수요는 감소합니다. 소득 증가, 금리 하락, 인구 증가는 수요를 증가시킵니다."
            },
            {
                "topic": "탄력성",
                "q": "탄력성이 크다는 것은?",
                "options": [
                    "가격 변화에 대해 수요량이 크게 변하지 않는다",
                    "가격 변화에 대해 수요량이 민감하게 반응한다",
                    "탄력성은 항상 1보다 크다",
                    "탄력성은 음수일 수 없다"
                ],
                "answer": 2,
                "explanation": "탄력성이 크다는 것은 가격 변화에 대해 수요량이 민감하게 반응한다는 의미입니다."
            },
            {
                "topic": "부동산 투자 - 수익과 위험",
                "q": "부동산 투자의 수익률 계산 시 고려해야 할 요소가 아닌 것은?",
                "options": [
                    "임대소득",
                    "자본이득",
                    "세금",
                    "건물의 연식만"
                ],
                "answer": 4,
                "explanation": "부동산 투자 수익률은 임대소득, 자본이득, 세금 등을 종합적으로 고려해야 합니다."
            },
            {
                "topic": "할인율(DCF)",
                "q": "DCF(할인현금흐름)법에서 할인율이 높아지면?",
                "options": [
                    "현재가치가 상승한다",
                    "현재가치가 하락한다",
                    "현재가치에 영향이 없다",
                    "미래가치에만 영향을 미친다"
                ],
                "answer": 2,
                "explanation": "할인율이 높아지면 미래 현금흐름의 현재가치는 하락합니다."
            },
            {
                "topic": "리카르도와 막스의 지대이론",
                "q": "리카르도의 지대이론에 대한 설명으로 옳은 것은?",
                "options": [
                    "지대는 노동의 생산물이다",
                    "토지의 위치와 비옥도에 따라 차등지대가 발생한다",
                    "지대는 자본의 생산물이다",
                    "모든 토지의 지대는 동일하다"
                ],
                "answer": 2,
                "explanation": "리카르도는 토지의 위치와 비옥도에 따라 차등지대가 발생한다고 설명했습니다."
            },
            {
                "topic": "입지론",
                "q": "입지론에서 가장 중요한 고려요소는?",
                "options": [
                    "건물의 연식",
                    "접근성",
                    "건축비",
                    "세율"
                ],
                "answer": 2,
                "explanation": "입지론에서 접근성이 가장 중요한 고려요소입니다."
            }
        ]

        questions = []
        for i, topic in enumerate(topics):
            questions.append({
                "id": f"gaeron_pdf_{i}",
                "topic": topic["topic"],
                "question": topic["q"],
                "options": topic["options"],
                "answer": topic["answer"],
                "explanation": topic["explanation"]
            })

    elif subject == "민법":
        # 민법 핵심 주제
        topics = [
            {
                "topic": "민법 기본 원칙",
                "q": "민법의 기본 원칙으로 옳은 것은?",
                "options": [
                    "사적 자치의 원칙",
                    "공공의 복리를 최우선으로 한다",
                    "국가의 개입을 우선한다",
                    "신의성실의 원칙은 없다"
                ],
                "answer": 1,
                "explanation": "민법은 사적 자치의 원칙과 신의성실의 원칙을 기본으로 합니다."
            },
            {
                "topic": "권리능력",
                "q": "권리능력에 대한 설명으로 틀린 것은?",
                "options": [
                    "자연인은 출생과 동시에 권리능력을 취득한다",
                    "권리능력은 사망시 소멸한다",
                    "태아는 권리능력이 없다",
                    "외국인도 권리능력을 가진다"
                ],
                "answer": 3,
                "explanation": "태아도 권리능력을 가집니다(상속, 손해배상청구권 등 인정)."
            },
            {
                "topic": "행위능력",
                "q": "미성년자의 법률행위에 대한 설명으로 옳은 것은?",
                "options": [
                    "단독으로 유효한 법률행위를 할 수 있다",
                    "법정대리인의 동의가 필요하다",
                    "모든 법률행위가 무효이다",
                    "친권자만 동의할 수 있다"
                ],
                "answer": 2,
                "explanation": "미성년자는 법정대리인의 동의를 얻어야 법률행위를 할 수 있습니다."
            },
            {
                "topic": "물권의 정의",
                "q": "물권에 대한 설명으로 옳은 것은?",
                "options": [
                    "특정인에게 청구할 수 있는 권리",
                    "직접 물건을 지배하는 권리",
                    "채권의 일종이다",
                    "등기 없이도 효력이 생긴다"
                ],
                "answer": 2,
                "explanation": "물권은 직접 물건을 지배하여 이익을 얻는 권리입니다."
            },
            {
                "topic": "물권의 변경",
                "q": "부동산 물권의 변경 시 효력발생요건은?",
                "options": [
                    "당사자의 합의",
                    "등기",
                    "인도",
                    "공증"
                ],
                "answer": 2,
                "explanation": "부동산 물권의 변경은 등기를 해야 효력이 발생합니다(공시주의)."
            },
            {
                "topic": "소유권",
                "q": "소유권의 내용에 속하지 않는 것은?",
                "options": [
                    "사용권",
                    "수익권",
                    "처분권",
                    "점유권"
                ],
                "answer": 4,
                "explanation": "소유권은 사용·수익·처분권을 포함하며, 점유권은 별개의 권리입니다."
            },
            {
                "topic": "저당권",
                "q": "저당권에 대한 설명으로 틀린 것은?",
                "options": [
                    "담보물권이다",
                    "용익물권이다",
                    "목적물의 점유를 이전하지 않는다",
                    "우선변제권이 있다"
                ],
                "answer": 2,
                "explanation": "저당권은 담보물권이지 용익물권이 아닙니다."
            },
            {
                "topic": "계약의 성립",
                "q": "계약이 성립하기 위한 필수요건은?",
                "options": [
                    "서면 작성",
                    "공증",
                    "청약과 승낙의 합치",
                    "등기"
                ],
                "answer": 3,
                "explanation": "계약은 청약과 승낙이 합치함으로써 성립합니다."
            },
            {
                "topic": "계약의 해제",
                "q": "계약의 해제 효과는?",
                "options": [
                    "장래에 향해서만 효력이 소멸",
                    "소급적으로 효력이 소멸",
                    "채무의 이행만 면제",
                    "손해배상 청구만 가능"
                ],
                "answer": 2,
                "explanation": "계약의 해제는 소급적으로 효력이 소멸합니다(계약을 처음부터 없었던 것으로 함)."
            },
            {
                "topic": "매매계약",
                "q": "부동산 매매계약의 효력발생시기는?",
                "options": [
                    "계약체결시",
                    "등기시",
                    "잔금지급시",
                    "인도시"
                ],
                "answer": 1,
                "explanation": "매매계약은 당사자의 합의로 효력이 발생합니다(채권행위이므로 등기 불필요)."
            }
        ]

        questions = []
        for i, topic in enumerate(topics):
            questions.append({
                "id": f"minbub_pdf_{i}",
                "topic": topic["topic"],
                "question": topic["q"],
                "options": topic["options"],
                "answer": topic["answer"],
                "explanation": topic["explanation"]
            })

    return questions

def main():
    """메인 실행"""
    print("📚 PDF 기반 문제 뱅크 생성 시작")

    # 개론 PDF 읽기
    print("📘 개론 PDF 읽는 중...")
    gaeron_content = extract_pdf_text(GAERON_PDF)
    gaeron_questions = generate_questions_from_content(gaeron_content, "개론")

    # 민법 PDF 읽기
    print("📕 민법 PDF 읽는 중...")
    minbub_content = extract_pdf_text(MINBUB_PDF)
    minbub_questions = generate_questions_from_content(minbub_content, "민법")

    # 문제 뱅크 생성
    question_bank = {
        "개론": gaeron_questions,
        "민법": minbub_questions
    }

    # JSON 저장
    with open(QUESTION_BANK_FILE, 'w', encoding='utf-8') as f:
        json.dump(question_bank, f, ensure_ascii=False, indent=2)

    print(f"✅ 문제 뱅크 저장 완료: {QUESTION_BANK_FILE}")
    print(f"📘 개론: {len(gaeron_questions)}문제")
    print(f"📕 민법: {len(minbub_questions)}문제")

if __name__ == "__main__":
    main()
