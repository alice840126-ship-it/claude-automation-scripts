#!/usr/bin/env python3
"""
PDF → Markdown 변환 스크립트
사용법: python pdf_to_markdown.py input.pdf [output.md]
"""

import sys
import pymupdf4llm

def convert_pdf_to_markdown(pdf_path: str, md_path: str = None) -> str:
    """PDF를 Markdown으로 변환"""

    if md_path is None:
        md_path = pdf_path.replace(".pdf", ".md")

    print(f"📄 변환 중: {pdf_path}")

    # 변환
    md_text = pymupdf4llm.to_markdown(pdf_path)

    # 저장
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"✅ 완료: {md_path}")
    print(f"   크기: {len(md_text):,}자")

    return md_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python pdf_to_markdown.py input.pdf [output.md]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    md_path = sys.argv[2] if len(sys.argv) > 2 else None

    convert_pdf_to_markdown(pdf_path, md_path)
