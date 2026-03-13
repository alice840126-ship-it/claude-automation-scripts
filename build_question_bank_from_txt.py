#!/usr/bin/env python3
"""텍스트 파일에서 기출문제를 추출하여 JSON으로 저장"""
import json
import re
from pathlib import Path

def extract_questions_from_txt(txt_path):
    """텍스트 파일에서 기출문제 추출"""
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 정답 위치 찾기
    answer_pattern = r'/\s*[\'\']?\s*정답\s*([①-④⑤@©®①②③④⑤])'
    answer_matches = list(re.finditer(answer_pattern, content))

    print(f'🔍 찾은 정답 마커: {len(answer_matches)}개')

    questions = []

    for match in answer_matches:
        answer_pos = match.start()
        answer_symbol = match.group(1)

        # 정답 변환
        answer_map = {
            '①': 1, '②': 2, '③': 3, '④': 4, '⑤': 5,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            '@': 1, '©': 2, '®': 3, '♠': 4,
            '⑴': 1, '⑵': 2, '⑶': 3, '⑷': 4
        }
        correct_answer = answer_map.get(answer_symbol, 1)

        # 정답 이전 텍스트 분석 (뒤에서부터)
        before_text = content[:answer_pos]

        # 가장 가까운 보기 찾기
        # 보기 패턴: ①, ②, ③, ④ 등
        option_pattern = r'([①-④⑤@©®①②③④⑤⑴-⑸])\s*'

        # 가장 마지막 5개 보기 위치 찾기
        option_positions = []
        for opt_match in re.finditer(option_pattern, before_text):
            option_positions.append((opt_match.start(), opt_match.group(1)))

        if len(option_positions) < 2:
            continue  # 보기가 부족하면 스킵

        # 마지막 5개 보기 사용
        last_options = option_positions[-5:] if len(option_positions) >= 5 else option_positions

        # 보기 사이의 텍스트 추출
        options = []
        for k in range(len(last_options)):
            opt_start, opt_symbol = last_options[k]
            # 다음 보기 또는 문제 끝
            if k < len(last_options) - 1:
                opt_end = last_options[k + 1][0]
            else:
                opt_end = answer_pos

            opt_text = before_text[opt_start + len(last_options[k][1]):opt_end].strip()
            # 줄바꿈과 공백 정리
            opt_text = re.sub(r'\s+', ' ', opt_text)
            opt_text = opt_text[:100]  # 길이 제한

            if opt_text:
                options.append(opt_text)

        # 문제 텍스트 추출 (첫 번째 보기 이전)
        if last_options:
            first_option_pos = last_options[0][0]

            # 첫 번째 보기 앞에서 문제 시작 찾기
            # 대표기출, 참고기출, 또는 빈 줄 이후
            problem_start = before_text.rfind('|대표기출', first_option_pos - 500, first_option_pos)
            if problem_start == -1:
                problem_start = before_text.rfind('! 참고기출', first_option_pos - 500, first_option_pos)
            if problem_start == -1:
                # 빈 줄 2개 이상 연속된 위치
                double_newline = before_text.rfind('\n\n\n', first_option_pos - 500, first_option_pos)
                problem_start = double_newline if double_newline != -1 else first_option_pos - 300
            else:
                problem_start = before_text.rfind('\n', problem_start - 100, problem_start)

            if problem_start != -1:
                question_text = before_text[problem_start + 1:first_option_pos].strip()
            else:
                question_text = before_text[max(0, first_option_pos - 200):first_option_pos].strip()

            # 정리
            question_text = re.sub(r'\s+', ' ', question_text)
            question_text = question_text[:200]

            # 유효성 확인
            if question_text and len(options) >= 2:
                # 주제 추출
                context_start = max(0, first_option_pos - 300)
                context = content[context_start:answer_pos + 50]
                topic = extract_topic_from_context(context)

                question = {
                    'id': f'gaeron_{len(questions) + 1}',
                    'subject': '개론',
                    'topic': topic,
                    'question': question_text,
                    'options': options[:4],
                    'answer': correct_answer if correct_answer <= 4 else 1,
                    'explanation': '기출문제'
                }
                questions.append(question)

    return questions

def extract_topic_from_context(context):
    """주변 텍스트에서 주제 추출"""
    keywords = {
        '부동산경제론': ['수요', '공급', '탄력성', '경기', '시장', '균형', '효율', '한계'],
        '부동산투자론': ['수익', '위험', '할인', 'DCF', '폴리오', '융자', '상환', '투자'],
        '감정평가론': ['감정', '평가', '가격', '비교', '원가', '거래사례', '공시'],
        '부동산시장론': ['입지', '리카르도', '호이트', '버제스', '거미집'],
        '부동산정책론': ['정책', '주택', '세금', '개입', '부동산정책', '공급'],
        '부동산금융론': ['금융', '융자', '상환', 'MBS', '대출', '담보', '이자'],
        '부동산개발론': ['개발', '재개발', '신개발', '개발위험'],
        '부동산관리론': ['관리', '마케팅']
    }

    context_lower = context.lower()
    max_score = 0
    best_topic = '부동산학개론'

    for topic, keys in keywords.items():
        score = sum(1 for key in keys if key in context_lower)
        if score > max_score:
            max_score = score
            best_topic = topic

    return best_topic

def main():
    txt_path = '/Users/oungsooryu/Desktop/0. 자비스/공인중개사/gaeron.txt'
    output_path = '/Users/oungsooryu/.claude/exam_questions_from_pdf.json'

    print('📚 개론 텍스트에서 기출문제 추출 시작')

    questions = extract_questions_from_txt(txt_path)

    print(f'✅ 추출 완료: {len(questions)}개')

    # JSON 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)

    print(f'💾 저장 완료: {output_path}')

    # 통계
    topics = {}
    for q in questions:
        topic = q['topic']
        topics[topic] = topics.get(topic, 0) + 1

    print('\n📊 주제별 분포:')
    for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True):
        print(f'  {topic}: {count}개')

    # 샘플 출력
    if questions:
        print('\n📝 샘플 문제 (3개):')
        for i, sample in enumerate(questions[:3], 1):
            print(f'\n[{i}] {sample["topic"]}')
            print(f'Q: {sample["question"][:80]}...')
            print(f'정답: {sample["answer"]}번')
            print(f'보기: {len(sample["options"])}개')

if __name__ == '__main__':
    main()
