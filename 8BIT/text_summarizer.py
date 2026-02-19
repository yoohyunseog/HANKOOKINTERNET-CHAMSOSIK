"""
텍스트 요약기
페이지 내용을 1줄로 요약합니다.
"""

import re
from collections import Counter

class TextSummarizer:
    def __init__(self):
        # 불용어 (요약에서 제외할 단어)
        self.stopwords = {
            '이', '그', '저', '것', '수', '등', '및', '더', '를', '을', '가', '이',
            '은', '는', '에', '의', '와', '과', '도', '로', '으로', '에서', '에게',
            '한', '하는', '하다', '있다', '없다', '되다', '이다', '아니다',
            '그리고', '그러나', '하지만', '또한', '또는', '때문', '위해',
        }
    
    def summarize(self, text, title='', max_length=100):
        """
        텍스트를 1줄로 요약
        
        Args:
            text (str): 요약할 텍스트
            title (str): 페이지 제목
            max_length (int): 최대 요약 길이
            
        Returns:
            str: 1줄 요약문
        """
        if not text:
            return title[:max_length] if title else "내용 없음"
        
        # 1. 문장 분리
        sentences = self.split_sentences(text)
        
        if not sentences:
            return title[:max_length] if title else "내용 없음"
        
        # 2. 각 문장 점수 계산
        sentence_scores = self.score_sentences(sentences, title)
        
        # 3. 최고 점수 문장 선택
        if sentence_scores:
            best_sentence = max(sentence_scores, key=sentence_scores.get)
            summary = best_sentence.strip()
        else:
            summary = sentences[0] if sentences else title
        
        # 4. 길이 조정
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'
        
        return summary
    
    def split_sentences(self, text):
        """텍스트를 문장으로 분리"""
        # 개행 문자 제거
        text = ' '.join(text.split())
        
        # 문장 분리 (마침표, 물음표, 느낌표 기준)
        sentences = re.split(r'[.!?]+', text)
        
        # 빈 문장 제거, 20자 이상만 유지
        sentences = [s.strip() for s in sentences if len(s.strip()) >= 20]
        
        return sentences[:10]  # 최대 10개 문장만 분석
    
    def score_sentences(self, sentences, title=''):
        """문장별 중요도 점수 계산"""
        scores = {}
        
        # 제목 키워드 추출
        title_words = set(self.extract_words(title))
        
        for sentence in sentences:
            score = 0
            words = self.extract_words(sentence)
            
            # 1. 제목과의 단어 일치도 (가중치: 3)
            title_match = len(set(words) & title_words)
            score += title_match * 3
            
            # 2. 문장 위치 (앞쪽 문장에 가중치)
            position_score = (10 - sentences.index(sentence)) / 10
            score += position_score * 2
            
            # 3. 문장 길이 (너무 짧거나 길지 않은 문장 선호)
            length = len(sentence)
            if 50 <= length <= 150:
                score += 2
            elif 30 <= length < 50 or 150 < length <= 200:
                score += 1
            
            # 4. 숫자 포함 (통계, 날짜 등)
            if re.search(r'\d+', sentence):
                score += 1
            
            scores[sentence] = score
        
        return scores
    
    def extract_words(self, text):
        """텍스트에서 단어 추출"""
        # 한글, 영문, 숫자만 추출
        words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        
        # 불용어 제거, 2글자 이상만
        words = [w for w in words if len(w) >= 2 and w not in self.stopwords]
        
        return words
    
    def summarize_batch(self, items):
        """
        여러 항목을 한 번에 요약
        
        Args:
            items (list): [{title, content}, ...] 형식의 리스트
            
        Returns:
            list: 각 항목에 summary 필드가 추가된 리스트
        """
        results = []
        
        for item in items:
            # paragraphs를 하나의 텍스트로 결합
            content = item.get('content', '')
            if isinstance(content, list):
                content = ' '.join(content)
            
            summary = self.summarize(
                text=content,
                title=item.get('title', '')
            )
            
            item['summary'] = summary
            results.append(item)
        
        return results


def test_summarizer():
    """테스트 함수"""
    summarizer = TextSummarizer()
    
    test_text = """
    인공지능 기술이 빠르게 발전하고 있습니다. 
    OpenAI는 최근 GPT-4를 공개했으며, 이는 이전 버전보다 더 뛰어난 성능을 보여줍니다.
    특히 한국어 처리 능력이 크게 향상되었다고 합니다.
    많은 기업들이 AI 기술을 적용하여 업무 효율을 높이고 있습니다.
    전문가들은 앞으로 AI가 더 많은 분야에서 활용될 것으로 전망합니다.
    """
    
    title = "OpenAI GPT-4 공개, 한국어 처리 능력 대폭 향상"
    
    summary = summarizer.summarize(test_text, title)
    
    print("=" * 60)
    print("📝 텍스트 요약 테스트")
    print("=" * 60)
    print(f"\n제목: {title}")
    print(f"\n요약: {summary}")
    print(f"\n요약 길이: {len(summary)}자")


if __name__ == '__main__':
    test_summarizer()
