"""
데이터 검증 및 정리 스크립트
수집된 데이터의 품질을 검사합니다.
"""

import json
import os
from pathlib import Path
from typing import List, Dict
from collections import Counter

# 기본 경로
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "raw"
PROCESSED_DIR = BASE_DIR / "processed"
METADATA_DIR = BASE_DIR / "metadata"


def validate_jsonl(file_path: Path) -> Dict:
    """
    JSONL 파일을 검증합니다.
    """
    issues = []
    stats = {
        "total": 0,
        "with_korean": 0,
        "with_original": 0,
        "with_people": 0,
        "with_keywords": 0,
        "empty_fields": []
    }
    
    with open(file_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            
            try:
                entry = json.loads(line)
                stats["total"] += 1
                
                # 필수 필드 확인
                if not entry.get("id"):
                    issues.append(f"행 {i}: id 없음")
                
                if not entry.get("original"):
                    issues.append(f"행 {i}: 원문(original) 없음")
                else:
                    stats["with_original"] += 1
                
                if entry.get("korean"):
                    stats["with_korean"] += 1
                
                if entry.get("people"):
                    stats["with_people"] += 1
                
                if entry.get("keywords"):
                    stats["with_keywords"] += 1
                
                # 빈 필드 확인
                for key, value in entry.items():
                    if not value and key not in ["korean"]:
                        stats["empty_fields"].append(key)
            
            except json.JSONDecodeError as e:
                issues.append(f"행 {i}: JSON 파싱 오류 - {e}")
    
    return {
        "file": file_path.name,
        "stats": stats,
        "issues": issues
    }


def check_duplicates(file_path: Path) -> List[str]:
    """
    중복 항목을 확인합니다.
    """
    ids = []
    duplicates = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                entry_id = entry.get("id", "")
                if entry_id in ids:
                    duplicates.append(entry_id)
                else:
                    ids.append(entry_id)
    
    return duplicates


def analyze_content(file_path: Path) -> Dict:
    """
    내용을 분석합니다.
    """
    people_counter = Counter()
    keyword_counter = Counter()
    chapter_counter = Counter()
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                
                for person in entry.get("people", []):
                    people_counter[person] += 1
                
                for keyword in entry.get("keywords", []):
                    keyword_counter[keyword] += 1
                
                chapter = entry.get("chapter", "미상")
                chapter_counter[chapter] += 1
    
    return {
        "people": dict(people_counter.most_common(20)),
        "keywords": dict(keyword_counter.most_common(20)),
        "chapters": dict(chapter_counter)
    }


def generate_report(results: List[Dict]) -> str:
    """
    검증 보고서를 생성합니다.
    """
    report = []
    report.append("="*60)
    report.append("데이터 검증 보고서")
    report.append("="*60)
    report.append("")
    
    for result in results:
        report.append(f"\n### {result['file']}")
        report.append("")
        
        # 통계
        stats = result["stats"]
        report.append("통계:")
        report.append(f"  - 총 항목: {stats['total']}")
        report.append(f"  - 원문 있음: {stats['with_original']} ({stats['with_original']/max(stats['total'],1)*100:.1f}%)")
        report.append(f"  - 번역 있음: {stats['with_korean']} ({stats['with_korean']/max(stats['total'],1)*100:.1f}%)")
        report.append(f"  - 인물 태그 있음: {stats['with_people']} ({stats['with_people']/max(stats['total'],1)*100:.1f}%)")
        report.append(f"  - 키워드 태그 있음: {stats['with_keywords']} ({stats['with_keywords']/max(stats['total'],1)*100:.1f}%)")
        
        # 문제점
        if result["issues"]:
            report.append("\n문제점:")
            for issue in result["issues"][:10]:  # 최대 10개만 표시
                report.append(f"  - {issue}")
            if len(result["issues"]) > 10:
                report.append(f"  ... 외 {len(result['issues'])-10}개")
        
        # 분석
        analysis = result.get("analysis", {})
        if analysis:
            report.append("\n분석:")
            
            if analysis.get("people"):
                report.append("  인물 빈도:")
                for person, count in list(analysis["people"].items())[:5]:
                    report.append(f"    - {person}: {count}회")
            
            if analysis.get("keywords"):
                report.append("  키워드 빈도:")
                for keyword, count in list(analysis["keywords"].items())[:5]:
                    report.append(f"    - {keyword}: {count}회")
    
    return "\n".join(report)


def main():
    """
    메인 실행 함수
    """
    print("="*60)
    print("데이터 검증기")
    print("="*60)
    
    # processed 폴더의 JSONL 파일 검증
    jsonl_files = list(PROCESSED_DIR.glob("*.jsonl"))
    
    if not jsonl_files:
        print("\n[WARN] processed 폴더에 JSONL 파일이 없습니다.")
        return
    
    print(f"\n검증할 파일 ({len(jsonl_files)}개):")
    for f in jsonl_files:
        print(f"  - {f.name}")
    
    results = []
    
    for file_path in jsonl_files:
        print(f"\n검증 중: {file_path.name}")
        
        # 기본 검증
        validation = validate_jsonl(file_path)
        
        # 중복 확인
        duplicates = check_duplicates(file_path)
        if duplicates:
            validation["issues"].append(f"중복 ID {len(duplicates)}개: {', '.join(duplicates[:5])}")
        
        # 내용 분석
        validation["analysis"] = analyze_content(file_path)
        
        results.append(validation)
    
    # 보고서 생성
    report = generate_report(results)
    
    # 보고서 저장
    report_path = BASE_DIR / "validation_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\n" + report)
    print(f"\n[SAVED] {report_path}")


if __name__ == "__main__":
    main()