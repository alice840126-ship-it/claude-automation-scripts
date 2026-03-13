#!/usr/bin/env python3
"""
네이버 검색 API를 활용한 검색 스크립트
사용법: python naaver_search.py '검색어' [검색타입]
검색타입: webkr (웹문서), blog (블로그), cafe (카페), news (뉴스), kin (지식iN), shop (쇼핑)
기본값: webkr
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')


def naver_search(query, search_type='web', display=10, start=1, sort='sim'):
    """
    네이버 검색 API 호출

    Args:
        query: 검색어
        search_type: 검색 타입 (blog, cafe, news, kin, shop, doc)
                    주의: web 타입은 지원하지 않음
        display: 검색 결과 출력 수 (1-100)
        start: 검색 시작 위치 (1-1000)
        sort: 정렬 방식 (sim: 유사도순, date: 날짜순)

    Returns:
        검색 결과 JSON
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("Error: NAVER_CLIENT_ID or NAVER_CLIENT_SECRET not found in .env file")
        return None

    # API 엔드포인트 URL
    url = f"https://openapi.naver.com/v1/search/{search_type}"

    # 요청 헤더
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }

    # 요청 파라미터
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        if hasattr(e.response, 'json'):
            print(f"에러 상세: {e.response.json()}")
        return None


def format_result(result, search_type):
    """검색 결과를 보기 좋게 포맷팅"""
    if not result or 'items' not in result:
        return "검색 결과가 없습니다."

    items = result['items']
    total = result.get('total', 0)

    output = []
    output.append(f"검색 결과 총 {total:,}건 중 {len(items)}건 표시\n")
    output.append("=" * 80)

    for i, item in enumerate(items, 1):
        output.append(f"\n[{i}]")

        # 검색 타입에 따라 필드 다름
        if search_type in ['blog', 'cafe']:
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            link = item.get('link', '')
            description = item.get('description', '').replace('<b>', '').replace('</b>', '')
            bloggername = item.get('bloggername', item.get('cafename', ''))

            output.append(f"제목: {title}")
            output.append(f"작성자: {bloggername}")
            output.append(f"내용: {description[:200]}...")
            output.append(f"링크: {link}")

        elif search_type == 'web':
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            link = item.get('link', '')
            description = item.get('description', '').replace('<b>', '').replace('</b>', '')

            output.append(f"제목: {title}")
            output.append(f"내용: {description[:200]}...")
            output.append(f"링크: {link}")

        elif search_type == 'webkr':
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            link = item.get('link', '')
            description = item.get('description', '').replace('<b>', '').replace('</b>', '')

            output.append(f"제목: {title}")
            output.append(f"내용: {description[:200]}...")
            output.append(f"링크: {link}")

        elif search_type == 'news':
            title = item.get('title', '').replace('<b>', '').replace('</b>', '')
            link = item.get('link', '')
            description = item.get('description', '').replace('<b>', '').replace('</b>', '')
            pubDate = item.get('pubDate', '')

            output.append(f"제목: {title}")
            output.append(f"날짜: {pubDate}")
            output.append(f"내용: {description[:200]}...")
            output.append(f"링크: {link}")

        output.append("-" * 80)

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("사용법: python naaver_search.py '검색어' [검색타입]")
        print("검색타입: webkr (웹문서), blog (블로그), cafe (카페), news (뉴스), kin (지식iN), shop (쇼핑)")
        print("기본값: webkr")
        sys.exit(1)

    query = sys.argv[1]
    search_type = sys.argv[2] if len(sys.argv) > 2 else 'webkr'

    # 유효한 검색 타입 체크
    valid_types = ['webkr', 'blog', 'cafe', 'news', 'kin', 'shop', 'doc']
    if search_type not in valid_types:
        print(f"Error: 유효하지 않은 검색타입 '{search_type}'")
        print(f"가능한 검색타입: {', '.join(valid_types)}")
        sys.exit(1)

    print(f"네이버 {search_type.upper()} 검색: '{query}'\n")

    result = naver_search(query, search_type=search_type)

    if result:
        print(format_result(result, search_type))

        # JSON 파일로 저장 (선택사항)
        output_file = os.path.join(os.path.dirname(__file__), '..', 'logs', f'search_{search_type}_{query[:10]}.json')
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n검색 결과가 저장되었습니다: {output_file}")


if __name__ == '__main__':
    main()
