#!/usr/bin/env python3
"""PDF를 텍스트로 변환하는 스크립트"""
import PyPDF2
import sys

def convert_pdf_to_text(pdf_path, txt_path):
    """PDF를 텍스트 파일로 변환"""
    try:
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f'총 페이지: {len(reader.pages)}', file=sys.stderr)

            text = ''
            for i, page in enumerate(reader.pages):
                text += page.extract_text() + '\n'
                if (i+1) % 50 == 0:
                    print(f'진행중: {i+1}/{len(reader.pages)}페이지', file=sys.stderr)

        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(text)

        print(f'✅ 변환 완료: {len(reader.pages)}페이지 -> {txt_path}')
        return True
    except Exception as e:
        print(f'❌ 에러: {e}', file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 convert_pdf_to_text.py <pdf_path> <txt_path>')
        sys.exit(1)

    convert_pdf_to_text(sys.argv[1], sys.argv[2])
