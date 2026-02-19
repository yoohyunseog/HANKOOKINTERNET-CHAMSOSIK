"""
키워드 추출기
텍스트에서 중요한 키워드를 추출합니다.
"""

import re
from collections import Counter

class KeywordExtractor:
    def __init__(self):
        # 불용어 (키워드에서 제외할 단어)
        self.stopwords = {
            # 조사
            '이', '그', '저', '것', '수', '등', '및', '더', '를', '을', '가',
            '은', '는', '에', '의', '와', '과', '도', '로', '으로', '에서', '에게',
            # 동사
            '하다', '되다', '있다', '없다', '이다', '아니다', '하는', '한',
            '되는', '된', '있는', '없는', '하고', '되고', '하며', '되며',
            # 부사/접속사
            '그리고', '그러나', '하지만', '또한', '또는', '때문', '위해',
            '그래서', '따라서', '그런데', '즉', '또', '매우', '아주', '정말',
            # 기타
            '것', '때', '곳', '데', '점', '바', '분', '듯', '만큼', '뿐',
        }
        
        # 단어 가중치 패턴
        self.weight_patterns = {
            # 기술 관련 (가중치: 2)
            r'AI|인공지능|머신러닝|딥러닝|알고리즘|데이터|프로그래밍|개발|코딩': 2,
            r'파이썬|자바|자바스크립트|웹|앱|서버|클라우드|API': 2,
            # 뉴스 관련 (가중치: 2)
            r'발표|보도|속보|단독|취재|기자|정부|대통령|장관|의원': 2,
            # 일반 명사 (가중치: 1)
            r'[가-힣]{2,}': 1,
        }
    
    def extract_keywords(self, text, title='', max_keywords=7):
        """
        텍스트에서 키워드 추출
        
        Args:
            text (str): 키워드를 추출할 텍스트
            title (str): 페이지 제목 (중요 키워드로 우선 처리)
            max_keywords (int): 최대 키워드 개수
            
        Returns:
            list: 키워드 리스트
        """
        # 1. 단어 추출
        words = self.extract_words(text)
        title_words = self.extract_words(title) if title else []
        
        # 2. 단어 빈도 계산
        word_freq = Counter(words)
        
        # 3. 제목 단어에 가중치 추가
        for word in title_words:
            if word in word_freq:
                word_freq[word] += 5  # 제목 키워드 가중치
        
        # 4. 패턴별 가중치 적용
        weighted_freq = {}
        for word, freq in word_freq.items():
            weight = self.get_word_weight(word)
            weighted_freq[word] = freq * weight
        
        # 5. 상위 키워드 선택
        top_keywords = sorted(
            weighted_freq.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:max_keywords]
        
        # 키워드만 추출
        keywords = [word for word, _ in top_keywords]
        
        return keywords
    
    def extract_words(self, text):
        """텍스트에서 단어 추출"""
        # 한글, 영문, 숫자만 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        # 불용어 제거, 2글자 이상만
        words = [
            w for w in words 
            if len(w) >= 2 and w not in self.stopwords
        ]
        
        return words
    
    def get_word_weight(self, word):
        """단어의 가중치 계산"""
        for pattern, weight in self.weight_patterns.items():
            if re.search(pattern, word):
                return weight
        return 1  # 기본 가중치
    
    def extract_keywords_batch(self, items):
        """
        여러 항목에서 키워드 추출
        
        Args:
            items (list): [{title, content}, ...] 형식의 리스트
            
        Returns:
            list: 각 항목에 keywords 필드가 추가된 리스트
        """
        results = []
        
        for item in items:
            # content를 문자열로 변환
            content = item.get('content', '')
            if isinstance(content, list):
                content = ' '.join(content)
            
            keywords = self.extract_keywords(
                text=content,
                title=item.get('title', '')
            )
            
            item['keywords'] = keywords
            results.append(item)
        
        return results


def test_extractor():
    """테스트 함수"""
    extractor = KeywordExtractor()
    
    test_text = """
    OpenAI가 최신 인공지능 모델 GPT-4를 발표했습니다.
    이번 GPT-4는 이전 버전인 GPT-3.5보다 훨씬 뛰어난 성능을 보여줍니다.
    특히 한국어 처리 능력이 크게 향상되었으며, 복잡한 문맥을 이해하는 능력도 개선되었습니다.
    많은 개발자들이 GPT-4 API를 활용하여 다양한 애플리케이션을 개발하고 있습니다.
    인공지능 기술은 앞으로 더 많은 분야에서 활용될 전망입니다.
    """
    
    title = "OpenAI GPT-4 공개, 한국어 처리 능력 대폭 향상"
    
    keywords = extractor.extract_keywords(test_text, title)
    
    print("=" * 60)
    print("🔍 키워드 추출 테스트")
    print("=" * 60)
    print(f"\n제목: {title}")
    print(f"\n키워드: {', '.join(keywords)}")
    print(f"\n키워드 개수: {len(keywords)}개")


if __name__ == '__main__':
    test_extractor()
