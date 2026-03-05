"""
뉴스 저장 + N/B 계산 저장 테스트
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root_dir))

from ide.ollama_ide_gui import OllamaIDE


def main():
    dummy = OllamaIDE.__new__(OllamaIDE)
    question = "오늘 주요 뉴스"
    answer = (
        "1️⃣ 반도체 투톱 보도 - 19만전자와 90만닉스가 투자실적 논란을 일으켰습니다. "
        "2️⃣ 고 최진실 딸 최준희 결혼 소식, 축하보다 논란이 확대되고 있습니다. "
        "3️⃣ 정정보도 모음 발표, 최근 보도에 대한 정정 내용이 정리되었습니다."
    )

    formatted = dummy.format_news_answer(answer)
    dummy.save_news_result(question, formatted)
    print("saved")
    print(formatted)


if __name__ == "__main__":
    main()
