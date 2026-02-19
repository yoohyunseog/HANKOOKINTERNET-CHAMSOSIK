"""
N/B 계산 결과 자동 정리 프로그램
- 결과 정렬
- 중복 제거
- 통계 생성
- 결과 저장 (JSON, CSV)
"""

import json
import os
import csv
from datetime import datetime
from pathlib import Path
from collections import Counter

class NBResultOrganizer:
    def __init__(self):
        self.data_dir = "data/nb_max"
        self.output_dir = "data/nb_results"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def scan_results(self):
        """모든 결과 파일 스캔"""
        results = []
        
        # data/nb_max 디렉토리 스캔
        if os.path.exists(self.data_dir):
            for root, dirs, files in os.walk(self.data_dir):
                for file in files:
                    if file.endswith('.json'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                results.append({
                                    'path': filepath,
                                    'data': data,
                                    'timestamp': os.path.getmtime(filepath)
                                })
                        except:
                            pass
        
        print(f"✅ {len(results)}개의 결과 파일 발견")
        return results
    
    def extract_calculations(self, results):
        """계산 결과 추출"""
        calculations = []
        
        for item in results:
            data = item['data']
            
            # 결과 추출 (구조에 따라 조정 필요)
            if isinstance(data, dict):
                if 'results' in data:
                    for calc in data['results']:
                        calculations.append(calc)
                elif 'nb_max' in data:
                    calculations.append(data)
            elif isinstance(data, list):
                calculations.extend(data)
        
        print(f"📊 {len(calculations)}개의 계산 결과 추출")
        return calculations
    
    def remove_duplicates(self, calculations):
        """중복 제거"""
        unique_calcs = []
        seen = set()
        
        for calc in calculations:
            # 키로 사용할 값 생성
            if isinstance(calc, dict):
                key = json.dumps(calc, sort_keys=True)
                if key not in seen:
                    seen.add(key)
                    unique_calcs.append(calc)
        
        removed = len(calculations) - len(unique_calcs)
        print(f"🗑️ {removed}개의 중복 제거")
        return unique_calcs
    
    def generate_statistics(self, calculations):
        """통계 생성"""
        stats = {
            'total_count': len(calculations),
            'collection_time': datetime.now().isoformat(),
            'breakdown': {
                'by_type': {},
                'by_category': {}
            }
        }
        
        # 유형별 분류
        for calc in calculations:
            if isinstance(calc, dict):
                calc_type = calc.get('type', 'unknown')
                stats['breakdown']['by_type'][calc_type] = \
                    stats['breakdown']['by_type'].get(calc_type, 0) + 1
        
        print(f"📈 통계 생성 완료")
        return stats
    
    def save_results(self, calculations, stats):
        """결과 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = os.path.join(self.output_dir, f"organized_results_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'results': calculations
            }, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON 저장: {json_file}")
        
        # CSV 저장
        if calculations and isinstance(calculations[0], dict):
            csv_file = os.path.join(self.output_dir, f"organized_results_{timestamp}.csv")
            try:
                with open(csv_file, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.DictWriter(f, fieldnames=calculations[0].keys())
                    writer.writeheader()
                    writer.writerows(calculations)
                print(f"✅ CSV 저장: {csv_file}")
            except:
                print("⚠️ CSV 저장 실패")
        
        # 최신 결과도 저장 (항상 덮어쓰기)
        latest_json = os.path.join(self.output_dir, "latest_results.json")
        with open(latest_json, 'w', encoding='utf-8') as f:
            json.dump({
                'statistics': stats,
                'results': calculations[:100]  # 최근 100개만
            }, f, ensure_ascii=False, indent=2)
        
        return json_file, csv_file
    
    def display_summary(self, stats):
        """요약 표시"""
        print("\n" + "="*60)
        print("📋 정리 결과 요약")
        print("="*60)
        print(f"✅ 총 항목: {stats['total_count']:,}개")
        print(f"📅 정리 시간: {stats['collection_time']}")
        
        if stats['breakdown']['by_type']:
            print("\n📊 유형별 분류:")
            for key, count in sorted(stats['breakdown']['by_type'].items()):
                print(f"   - {key}: {count:,}개")
        
        print("="*60 + "\n")
    
    def organize(self):
        """전체 정리 프로세스"""
        try:
            print("\n" + "="*60)
            print("🔄 N/B 계산 결과 자동 정리 시작")
            print("="*60 + "\n")
            
            # 1. 결과 스캔
            print("[1/5] 결과 파일 스캔 중...")
            results = self.scan_results()
            
            if not results:
                print("⚠️ 결과 파일이 없습니다.")
                return False
            
            # 2. 계산 결과 추출
            print("[2/5] 계산 결과 추출 중...")
            calculations = self.extract_calculations(results)
            
            # 3. 중복 제거
            print("[3/5] 중복 제거 중...")
            unique_calcs = self.remove_duplicates(calculations)
            
            # 4. 통계 생성
            print("[4/5] 통계 생성 중...")
            stats = self.generate_statistics(unique_calcs)
            
            # 5. 결과 저장
            print("[5/5] 결과 저장 중...")
            json_file, csv_file = self.save_results(unique_calcs, stats)
            
            # 요약 표시
            self.display_summary(stats)
            
            print("✅ 정리 완료!")
            return True
            
        except Exception as e:
            print(f"❌ 정리 실패: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    organizer = NBResultOrganizer()
    organizer.organize()

if __name__ == "__main__":
    main()
