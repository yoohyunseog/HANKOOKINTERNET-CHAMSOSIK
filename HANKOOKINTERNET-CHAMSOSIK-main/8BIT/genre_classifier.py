"""
장르 분류기
URL과 컨텐츠를 분석하여 5가지 장르로 분류합니다.
- 기술: 기술 뉴스, 개발 블로그, IT 관련
- 뉴스: 일반 뉴스, 언론사
- 블로그: 개인 블로그, 티스토리, 네이버 블로그
- 쇼핑: 쇼핑몰, 상품 페이지
- 영상: YouTube, 동영상 플랫폼
"""

import re
from urllib.parse import urlparse

class GenreClassifier:
    def __init__(self):
        # 도메인별 장르 매핑
        self.domain_patterns = {
            '기술': [
                r'github\.com',
                r'stackoverflow\.com',
                r'medium\.com',
                r'dev\.to',
                r'techcrunch\.com',
                r'zdnet\.co\.kr',
                r'bloter\.net',
                r'itworld\.co\.kr',
                r'codingworldnews\.com',
                r'developerlife\.com',
                r'yozm\.wishket\.com',
                r'tech\.kakao\.com',
                r'techblog\.',
            ],
            '뉴스': [
                r'news\.naver\.com',
                r'news\.daum\.net',
                r'chosun\.com',
                r'joins\.com',
                r'donga\.com',
                r'khan\.co\.kr',
                r'hani\.co\.kr',
                r'mt\.co\.kr',
                r'mk\.co\.kr',
                r'yonhapnews\.co\.kr',
                r'jtbc\.co\.kr',
                r'sbs\.co\.kr',
                r'kbs\.co\.kr',
                r'news\.',
            ],
            '블로그': [
                r'blog\.naver\.com',
                r'tistory\.com',
                r'brunch\.co\.kr',
                r'velog\.io',
                r'wordpress\.com',
                r'tumblr\.com',
                r'blogger\.com',
                r'blog\.',
            ],
            '쇼핑': [
                r'coupang\.com',
                r'11st\.co\.kr',
                r'gmarket\.co\.kr',
                r'auction\.co\.kr',
                r'interpark\.com',
                r'gsshop\.com',
                r'hmall\.com',
                r'ssg\.com',
                r'amazon\.com',
                r'aliexpress\.com',
                r'shop\.',
                r'store\.',
                r'mall\.',
            ],
            '영상': [
                r'youtube\.com',
                r'youtu\.be',
                r'vimeo\.com',
                r'twitch\.tv',
                r'afreecatv\.com',
                r'chzzk\.naver\.com',
                r'tv\.naver\.com',
                r'tv\.kakao\.com',
            ],
        }
        
        # 키워드별 장르 매핑
        self.keyword_patterns = {
            '기술': [
                '개발', '프로그래밍', '코딩', '파이썬', '자바스크립트', 
                'AI', '인공지능', '머신러닝', '알고리즘', '데이터',
                '웹개발', '앱개발', 'API', '서버', '클라우드',
                'github', 'git', '오픈소스', '튜토리얼', '가이드',
            ],
            '뉴스': [
                '속보', '단독', '취재', '발표', '보도',
                '정치', '경제', '사회', '문화', '국제',
                '기자', '뉴스', '언론', '보도자료', '기삿거리',
            ],
            '블로그': [
                '일상', '후기', '리뷰', '경험', '여행',
                '맛집', '카페', '취미', '육아', '요리',
                '생각', '느낀점', '공유', '일기', '자기계발',
            ],
            '쇼핑': [
                '가격', '할인', '특가', '세일', '구매',
                '상품', '제품', '배송', '결제', '주문',
                '쿠폰', '포인트', '적립', '무료배송', '반품',
                '베스트', '인기', '추천상품', '장바구니',
            ],
            '영상': [
                '동영상', '비디오', '영상', '재생', '구독',
                '채널', '라이브', '스트리밍', '방송', '클립',
                '유튜브', '유투브', '시청', '조회수', '좋아요',
            ],
        }
    
    def classify(self, url, title='', content=''):
        """
        URL, 제목, 내용을 분석하여 장르 분류
        
        Args:
            url (str): 페이지 URL
            title (str): 페이지 제목
            content (str): 페이지 내용
            
        Returns:
            str: 장르 ('기술', '뉴스', '블로그', '쇼핑', '영상')
        """
        scores = {
            '기술': 0,
            '뉴스': 0,
            '블로그': 0,
            '쇼핑': 0,
            '영상': 0,
        }
        
        # 1. URL 도메인 분석 (가중치: 3)
        domain = urlparse(url).netloc.lower()
        for genre, patterns in self.domain_patterns.items():
            for pattern in patterns:
                if re.search(pattern, domain):
                    scores[genre] += 3
                    break  # 한 번만 카운트
        
        # 2. 제목 키워드 분석 (가중치: 2)
        title_lower = title.lower()
        for genre, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in title_lower:
                    scores[genre] += 2
        
        # 3. 내용 키워드 분석 (가중치: 1)
        content_lower = content[:1000].lower()  # 앞부분 1000자만
        for genre, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in content_lower:
                    scores[genre] += 1
        
        # 4. URL 경로 분석 (가중치: 1)
        url_lower = url.lower()
        if '/product/' in url_lower or '/item/' in url_lower:
            scores['쇼핑'] += 2
        if '/watch' in url_lower or '/video' in url_lower:
            scores['영상'] += 2
        if '/tech/' in url_lower or '/dev/' in url_lower:
            scores['기술'] += 2
        if '/news/' in url_lower or '/article/' in url_lower:
            scores['뉴스'] += 2
        if '/blog/' in url_lower or '/post/' in url_lower:
            scores['블로그'] += 2
        
        # 최고 점수 장르 반환
        max_genre = max(scores, key=scores.get)
        
        # 점수가 0이면 블로그로 기본 분류
        if scores[max_genre] == 0:
            return '블로그'
        
        return max_genre
    
    def classify_batch(self, items):
        """
        여러 항목을 한 번에 분류
        
        Args:
            items (list): [{url, title, content}, ...] 형식의 리스트
            
        Returns:
            list: 각 항목에 genre 필드가 추가된 리스트
        """
        results = []
        
        for item in items:
            genre = self.classify(
                url=item.get('url', ''),
                title=item.get('title', ''),
                content=item.get('content', '')
            )
            
            item['genre'] = genre
            results.append(item)
        
        return results


def test_classifier():
    """테스트 함수"""
    classifier = GenreClassifier()
    
    test_cases = [
        {
            'url': 'https://github.com/python/cpython',
            'title': 'Python 공식 저장소',
            'content': '파이썬 프로그래밍 언어 개발',
        },
        {
            'url': 'https://news.naver.com/main/article.nhn',
            'title': '경제 뉴스 속보',
            'content': '오늘 발표된 경제 지표',
        },
        {
            'url': 'https://blog.naver.com/user/123',
            'title': '오늘의 맛집 후기',
            'content': '맛있는 점심 먹고 카페 갔어요',
        },
        {
            'url': 'https://coupang.com/product/12345',
            'title': '최저가 상품 특가',
            'content': '무료배송 할인 쿠폰 적용',
        },
        {
            'url': 'https://youtube.com/watch?v=abc',
            'title': '재미있는 동영상',
            'content': '구독 좋아요 알림설정',
        },
    ]
    
    print("=" * 60)
    print("🎯 장르 분류 테스트")
    print("=" * 60)
    
    for i, test in enumerate(test_cases, 1):
        genre = classifier.classify(
            url=test['url'],
            title=test['title'],
            content=test['content']
        )
        
        print(f"\n{i}. {test['title']}")
        print(f"   URL: {test['url']}")
        print(f"   장르: {genre}")


if __name__ == '__main__':
    test_classifier()
