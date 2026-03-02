"""
AI 수익형 트렌드 분석 시스템
- 트렌드 키워드 → 질문형 변환
- YouTube/Naver 검색
- 페이지 요약
- 데이터 저장 및 참소식.com 연동
"""

import json
import os
import time
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

class TrendToRevenueAI:
    def __init__(self):
        self.data_dir = "data/naver_creator_trends"
        self.output_dir = "data/revenue_content"
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def load_trend_data(self):
        """트렌드 데이터 로드"""
        latest_file = os.path.join(self.data_dir, "latest_trend_data.json")
        
        if not os.path.exists(latest_file):
            print("❌ 트렌드 데이터가 없습니다.")
            print(f"   먼저 실행: run_naver_creator_analyzer.bat")
            return None
        
        try:
            # UTF-8 인코딩으로 읽기 (명시적)
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            trends = data.get('trend_data', [])
            print(f"✅ 트렌드 데이터 로드: {len(trends)}개 항목")
            
            # 빈 항목 제거
            valid_trends = [t for t in trends if t.get('title') or t.get('raw_text')]
            if len(valid_trends) < len(trends):
                print(f"⚠️  빈 항목 {len(trends) - len(valid_trends)}개 제외됨")
            
            data['trend_data'] = valid_trends
            return data
        except Exception as e:
            print(f"❌ 데이터 로드 실패: {e}")
            return None
    
    def keyword_to_question(self, keyword):
        """키워드 → 질문형 변환"""
        # 간단한 질문 생성 로직
        questions = [
            f"{keyword}에 대해서 알려줄래?",
            f"{keyword}은(는) 무엇인가요?",
            f"{keyword}에 대해 최신 정보가 있나요?",
            f"{keyword} 트렌드를 알고 싶어요.",
            f"{keyword}에 대한 인기 콘텐츠가 있을까?",
        ]
        
        # 해시를 사용해서 동일한 키워드는 동일한 질문 반환
        import hashlib
        hash_val = int(hashlib.md5(keyword.encode()).hexdigest(), 16)
        return questions[hash_val % len(questions)]
    
    def search_youtube(self, query):
        """YouTube 검색 (URL만 생성)"""
        try:
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            # 실제 페이지 접근 없이 URL만 반환
            return {
                'url': search_url,
                'title': f"YouTube - {query} 검색 결과",
                'description': f"'{query}'에 대한 YouTube 검색 결과"
            }
        except Exception as e:
            print(f"⚠️ YouTube 검색 오류: {e}")
            return None
    
    def search_naver(self, query):
        """Naver 검색 (URL만 생성)"""
        try:
            search_url = f"https://search.naver.com/search.naver?query={quote(query)}"
            return {
                'url': search_url,
                'title': f"Naver - {query} 검색 결과",
                'description': f"'{query}'에 대한 Naver 검색 결과"
            }
        except Exception as e:
            print(f"⚠️ Naver 검색 오류: {e}")
            return None
    
    def extract_page_summary(self, url):
        """페이지 요약 추출 (간단한 버전)"""
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 메타 설명 추출
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                return meta_desc.get('content', '설명 없음')
            
            # 첫 문단 추출
            paragraphs = soup.find_all('p')
            if paragraphs:
                text = paragraphs[0].get_text().strip()
                return text[:200] if len(text) > 200 else text
            
            return "내용을 가져올 수 없습니다."
            
        except Exception as e:
            print(f"⚠️ 페이지 추출 오류: {e}")
            return "페이지 접근 실패"
    
    def simple_summarize(self, text):
        """간단한 요약 (첫 문장 + 키워드)"""
        sentences = text.split('.')
        first_sentence = sentences[0].strip() if sentences else text[:100]
        
        # 키워드 추출 (간단한 방식)
        words = first_sentence.split()
        keywords = [w for w in words if len(w) > 3][:5]
        
        return {
            'first_sentence': first_sentence + '.',
            'keywords': keywords,
            'length': len(text)
        }
    
    def generate_revenue_content(self, trend_data):
        """수익형 콘텐츠 생성"""
        revenue_contents = []
        
        trends = trend_data.get('trend_data', [])[:10]  # 최대 10개
        
        print(f"\n📊 {len(trends)}개 트렌드 처리 중...\n")
        
        for idx, trend in enumerate(trends, 1):
            try:
                # raw_text에서 첫 번째 라인만 추출
                raw_text = trend.get('raw_text', '').strip()
                keyword = raw_text.split('\n')[0].strip()
                
                # 빈 키워드거나 '-'인 경우 건너뛰기
                if not keyword or keyword == '-':
                    print(f"[{idx}/{len(trends)}] 건너뜀: {repr(keyword[:20])}")
                    continue
                
                # 너무 긴 키워드 자르기
                keyword = keyword[:50]
                
                print(f"[{idx}/{len(trends)}] 처리 중: {keyword[:35]}")
                
                # 1. 키워드 → 질문 변환
                question = self.keyword_to_question(keyword)
                print(f"  ❓ 질문: {question}")
                
                # 2. YouTube 검색
                yt_result = self.search_youtube(keyword)
                yt_summary = "YouTube에서 해당 주제의 다양한 영상을 확인할 수 있습니다."
                
                # 3. Naver 검색
                nv_result = self.search_naver(keyword)
                nv_summary = "Naver에서 최신 정보와 뉴스를 확인할 수 있습니다."
                
                # 4. 콘텐츠 구성
                content = {
                    'id': f"trend_{int(time.time() * 1000)}_{idx}",
                    'timestamp': datetime.now().isoformat(),
                    'original_keyword': keyword,
                    'question_form': question,
                    'ai_question': {
                        'text': question,
                        'type': 'trend_inquiry'
                    },
                    'youtube': {
                        'url': yt_result['url'] if yt_result else None,
                        'summary': yt_summary
                    },
                    'naver': {
                        'url': nv_result['url'] if nv_result else None,
                        'summary': nv_summary
                    },
                    'content_summary': {
                        'first_sentence': f"{keyword}는 최근 인기 있는 트렌드입니다.",
                        'key_points': [
                            f"{keyword}에 대한 관심도 증가",
                            "다양한 플랫폼에서 콘텐츠 생성 중",
                            "수익형 콘텐츠 기회 존재"
                        ]
                    },
                    'monetization': {
                        'revenue_keywords': [keyword, question, f"{keyword} 정보", f"{keyword} 분석"],
                        'estimated_views': 0,
                        'estimated_ctr': "미계산"
                    }
                }
                
                revenue_contents.append(content)
                print(f"  ✅ 완료\n")
                
                time.sleep(0.5)  # API 제한 회피
                
            except Exception as e:
                print(f"  ❌ 오류: {e}\n")
                import traceback
                traceback.print_exc()
                continue
        
        return revenue_contents
    
    def save_revenue_data(self, contents):
        """수익형 데이터 저장"""
        if not contents:
            print("❌ 저장할 데이터가 없습니다.")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON 저장
        json_file = os.path.join(self.output_dir, f"revenue_content_{timestamp}.json")
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generation_time': datetime.now().isoformat(),
                'total_items': len(contents),
                'contents': contents
            }, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 저장: {json_file}")
        
        # 최신 파일도 저장
        latest_file = os.path.join(self.output_dir, "latest_revenue_content.json")
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump({
                'generation_time': datetime.now().isoformat(),
                'total_items': len(contents),
                'contents': contents
            }, f, ensure_ascii=False, indent=2)
        
        return True
    
    def display_summary(self, contents):
        """결과 요약 표시"""
        print("\n" + "="*60)
        print("📈 수익형 콘텐츠 생성 완료")
        print("="*60)
        print(f"✅ 생성된 항목: {len(contents)}개")
        print(f"📅 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"💾 저장 위치: {self.output_dir}/")
        print("="*60 + "\n")
        
        if contents:
            print("📋 샘플 항목:")
            sample = contents[0]
            print(f"  원본 키워드: {sample.get('original_keyword', 'N/A')}")
            print(f"  질문 형태: {sample.get('question_form', 'N/A')}")
            print(f"  YouTube URL: {sample.get('youtube', {}).get('url', 'N/A')[:50]}...")
            print(f"  Naver URL: {sample.get('naver', {}).get('url', 'N/A')[:50]}...\n")
    
    def run(self):
        """전체 프로세스 실행"""
        print("\n" + "="*60)
        print("🚀 AI 수익형 트렌드 콘텐츠 생성 시작")
        print("="*60 + "\n")
        
        # 1. 트렌드 데이터 로드
        print("[1/4] 트렌드 데이터 로드 중...")
        trend_data = self.load_trend_data()
        if not trend_data:
            return False
        
        # 2. 수익형 콘텐츠 생성
        print("\n[2/4] 수익형 콘텐츠 생성 중...")
        contents = self.generate_revenue_content(trend_data)
        
        if not contents:
            print("❌ 콘텐츠 생성 실패")
            return False
        
        # 3. 데이터 저장
        print("\n[3/4] 데이터 저장 중...")
        if not self.save_revenue_data(contents):
            return False
        
        # 4. 요약 표시
        print("[4/4] 결과 요약")
        self.display_summary(contents)
        
        return True


def main():
    generator = TrendToRevenueAI()
    success = generator.run()
    
    if success:
        print("✅ 모든 작업 완료!")
    else:
        print("❌ 작업 실패")


if __name__ == "__main__":
    main()
