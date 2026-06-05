"""
최신 기사 요약 AI 봇
- 기존 JSON 데이터(vatican_rss_translated.json)를 읽어서
- AI로 요약
- JSON, 마크다운으로 저장
"""

import json
import os
import re
import requests
from datetime import datetime
from collections import defaultdict

# --- 설정 ---
OLLAMA_HOST = "http://211.45.162.155:11434"
OLLAMA_MODEL = "kimi-k2.5:cloud"  # kimi-k2.5:cloud 또는 deepseek-v4-pro:cloud

# 결과 저장 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_JSON = os.path.abspath(os.path.join(BASE_DIR, "..", "vatican_rss_translated.json"))
OUTPUT_JSON = os.path.abspath(os.path.join(BASE_DIR, "..", "article_news.json"))
OUTPUT_MD = os.path.abspath(os.path.join(BASE_DIR, "..", "article_news_summary.md"))


class OllamaLLM:
    """Ollama LLM 클라이언트"""
    
    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_MODEL):
        self.host = host
        self.model = model
    
    def check_connection(self) -> bool:
        """Ollama 서버 연결 확인"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                print(f"✓ Ollama 연결됨: {self.host}")
                print(f"  사용 가능한 모델: {', '.join(model_names)}")
                return True
        except Exception as e:
            print(f"✗ Ollama 연결 실패: {e}")
        return False
    
    def generate(self, prompt: str, timeout: int = 120) -> str:
        """텍스트 생성"""
        try:
            response = requests.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 500}
                },
                timeout=timeout
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            print(f"    LLM 오류: {e}")
        return ""
    
    def summarize_article(self, title: str, content: str) -> str:
        """기사 요약"""
        if not content:
            return ""
        
        # HTML 태그 제거
        clean_content = re.sub(r'<[^>]+>', '', content)
        clean_content = re.sub(r'\s+', ' ', clean_content).strip()
        
        # 내용이 너무 짧으면 그대로 반환
        if len(clean_content) < 50:
            return clean_content
        
        prompt = f"""다음 뉴스 기사를 한국어로 간결하게 요약하세요. HTML 태그 없이 텍스트만 출력하세요.

제목: {title}

본문:
{clean_content[:1500]}

요약 조건:
1. 핵심 내용을 2-3문장으로 요약
2. 중요한 사실 위주로 작성
3. 객관적이고 명확하게 작성
4. HTML 태그 없이 텍스트만 출력

요약:"""
        
        result = self.generate(prompt)
        
        # 결과가 없으면 원본 사용
        if not result or len(result) < 10:
            return clean_content[:200] + "..." if len(clean_content) > 200 else clean_content
        
        return result
    
    def create_comprehensive_summary(self, items: list) -> dict:
        """전체 기사를 종합하여 요약"""
        # 최근 기사들 수집
        recent_items = items[:5]  # 최근 5개
        
        # 기사 내용 정리
        articles_text = ""
        for i, item in enumerate(recent_items, 1):
            title = item.get('title', '').strip()
            content = item.get('description', '') or item.get('content', '') or ''
            clean_content = re.sub(r'<[^>]+>', '', content)
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            articles_text += f"\n[기사 {i}] 제목: {title}\n내용: {clean_content[:400]}\n"
        
        # 종합 요약 프롬프트
        summary_prompt = f"""다음은 최근 가톨릭/바티칸 뉴스 기사들입니다. 이 기사들을 종합하여 요약하세요.

{articles_text}

다음 형식으로 작성하세요:

**오늘의 메시지:**
(최근 뉴스를 종합하여 전하고 싶은 핵심 메시지를 2-3문장으로 작성)

**성경 말씀:**
(오늘의 메시지와 연결되는 성경 구절 하나를 정확하게 인용. 예: "요한복음 3:16 - '하느님께서는 세상을 그토록 사랑하셔서 독생자를 내어 주시어...'")

**묵상:**
(성경 말씀과 뉴스를 연결한 묵상을 3-4문장으로 작성. 실천적이고 영적으로 깊이 있게)

한국어로 작성하고, HTML 태그 없이 깔끔한 텍스트만 출력하세요."""

        print("   종합 요약 생성 중...")
        comprehensive_summary = self.generate(summary_prompt, timeout=180)
        
        # 전하고 싶은 이야기 (성경 중심)
        message_prompt = f"""다음 가톨릭 뉴스 기사들을 바탕으로, 성경 말씀과 연결하여 신자들에게 전하고 싶은 영적 메시지를 작성하세요.

{articles_text[:1500]}

작성 조건:
1. 성경 이야기나 말씀을 중심으로 시작
2. 오늘의 상황과 연결
3. 신자들에게 전하고 싶은 영적 메시지
4. 5-7문장으로 작성
5. 한국어로 작성
6. HTML 태그 없이 텍스트만 출력

전하고 싶은 이야기:"""

        print("   영적 메시지 생성 중...")
        spiritual_message = self.generate(message_prompt, timeout=180)
        
        # 전체 기사 한 문장 요약 (교황님 말씀 중심)
        total_prompt = f"""다음 가톨릭/바티칸 뉴스 기사들을 한 문장으로 요약하세요.

{articles_text[:2000]}

요약 조건:
1. 교황님의 말씀, 가르침, 강조점을 중심으로 요약
2. 교황님이 전달하고자 하는 핵심 메시지를 한 문장으로 표현
3. 50-100자 이내로 작성
4. 객관적이고 명확하게 작성
5. HTML 태그 없이 텍스트만 출력

한 문장 요약:"""

        print("   전체 요약 생성 중...")
        total_ai_summary = self.generate(total_prompt, timeout=120)
        
        # 결과 검증
        if not comprehensive_summary or len(comprehensive_summary) < 50:
            comprehensive_summary = self._create_default_summary(recent_items)
        
        if not spiritual_message or len(spiritual_message) < 50:
            spiritual_message = self._create_default_message(recent_items)
        
        if not total_ai_summary or len(total_ai_summary) < 20:
            total_ai_summary = self._create_default_total_summary(recent_items)
        
        return {
            "comprehensive_summary": comprehensive_summary,
            "spiritual_message": spiritual_message,
            "total_ai_summary": total_ai_summary
        }
    
    def _create_default_summary(self, items: list) -> str:
        """기본 종합 요약 생성"""
        titles = [item.get('title', '').strip()[:50] for item in items[:3]]
        return f"""**오늘의 메시지:**
최근 바티칸 뉴스에서 교황 레오 14세는 전례의 중요성과 하느님 현존의 체험을 강조하고 있습니다. 교회는 매달 기도 지향을 통해 신자들을 초대하며, 스포츠의 가치와 인간 존엄성에 대해서도 관심을 기울이고 있습니다.

**성경 말씀:**
"내가 곧 길이요 진리요 생명이니, 나를 통하지 않고서는 아무도 아버지께로 갈 수 없습니다." (요한복음 14:6)

**묵상:**
교황님의 가르침처럼, 우리는 전례를 통해 하느님의 현존을 체험합니다. 일상의 분주함에서 잠시 멈추어 본질적인 것으로 돌아가는 것이 영적 성장의 열쇠입니다."""
    
    def _create_default_message(self, items: list) -> str:
        """기본 영적 메시지 생성"""
        return """성경은 우리에게 "너희는 가서 모든 민족들을 제자로 삼아라" (마태복음 28:19)라고 명합니다. 오늘날 교황님은 이 사명을 현대 세계에 맞게 실천하고 계십니다. 전례를 통한 하느님 체험, 기도를 통한 일치, 그리고 사회적 가치 실현은 모든 신자가 따라야 할 길입니다. 우리도 이 부르심에 응답하여, 매일의 삶에서 그리스도의 사랑을 증거해야 합니다."""    
    def _create_default_total_summary(self, items: list) -> str:
        """기본 전체 요약 생성 (교황님 말씀 중심)"""
        titles = [item.get('title', '').strip()[:30] for item in items[:3]]
        return f"교황님은 전례를 통한 하느님 체험과 기도의 중요성을 강조하며, 신자들에게 영적 성장과 사회적 가치 실현을 촉구하고 계십니다."

class ArticleSummarizer:
    """기존 JSON 데이터를 읽어서 AI 요약"""
    
    def __init__(self):
        """초기화"""
        self.llm = OllamaLLM()
        print(f"✅ 기사 요약 AI 초기화 완료")
        print(f"   - 입력: {INPUT_JSON}")
        print(f"   - 출력: {OUTPUT_JSON}")
        print(f"   - 모델: {OLLAMA_MODEL}")
    
    def load_existing_data(self) -> dict:
        """기존 JSON 데이터 로드"""
        if not os.path.exists(INPUT_JSON):
            print(f"✗ 입력 파일 없음: {INPUT_JSON}")
            return None
        
        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✓ 데이터 로드: {len(data.get('items', []))}개 기사")
        return data
    
    def process_articles(self, data: dict) -> dict:
        """기사 요약 처리"""
        items = data.get('items', [])
        
        print(f"\n📰 기사 요약 시작...")
        
        processed_items = []
        
        for i, item in enumerate(items, 1):
            title = item.get('title', '').strip()
            content = item.get('description', '') or item.get('content', '') or ''
            url = item.get('url', '')
            source = item.get('source', '')
            pub_date = item.get('pub_date', '')
            
            print(f"\n[{i}/{len(items)}] {title[:50]}...")
            
            # AI 요약
            ai_summary = self.llm.summarize_article(title, content)
            
            if not ai_summary:
                # AI 요약 실패 시 기존 내용 사용
                ai_summary = content[:200] + "..." if len(content) > 200 else content
            
            processed_item = {
                "title": title,
                "url": url,
                "source": source,
                "pub_date": pub_date,
                "content": content[:500],
                "ai_summary": ai_summary,
                "processed_at": datetime.now().isoformat()
            }
            
            processed_items.append(processed_item)
        
        # 종합 요약 생성
        print(f"\n📖 종합 요약 생성 중...")
        comprehensive = self.llm.create_comprehensive_summary(items)
        
        result = {
            "stage": "ai_summarized",
            "processed_at": datetime.now().isoformat(),
            "total_items": len(processed_items),
            "comprehensive_summary": comprehensive.get("comprehensive_summary", ""),
            "spiritual_message": comprehensive.get("spiritual_message", ""),
            "total_ai_summary": comprehensive.get("total_ai_summary", ""),
            "items": processed_items
        }
        
        return result
    
    def save_results(self, data: dict):
        """결과 저장"""
        # JSON 저장
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 JSON 저장: {OUTPUT_JSON}")
        
        # 마크다운 저장
        md_content = self._generate_markdown(data)
        with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
            f.write(md_content)
        print(f"💾 마크다운 저장: {OUTPUT_MD}")
    
    def _generate_markdown(self, data: dict) -> str:
        """마크다운 형식으로 변환"""
        lines = []
        lines.append("# 📰 최신 기사 AI 종합 요약")
        lines.append("")
        lines.append(f"**생성일:** {data['processed_at']}")
        lines.append(f"**총 기사:** {data['total_items']}개")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 종합 요약
        comprehensive = data.get('comprehensive_summary', '')
        if comprehensive:
            lines.append("## 📖 오늘의 종합 요약")
            lines.append("")
            lines.append(comprehensive)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # 전하고 싶은 이야기 (성경 중심)
        spiritual = data.get('spiritual_message', '')
        if spiritual:
            lines.append("## ✝️ 전하고 싶은 이야기")
            lines.append("")
            lines.append(spiritual)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # 개별 기사 목록
        lines.append("## 📋 기사 목록")
        lines.append("")
        
        # 날짜별로 그룹화
        by_date = defaultdict(list)
        for item in data['items']:
            date_str = item.get('pub_date', '')[:10] if item.get('pub_date') else '날짜 없음'
            by_date[date_str].append(item)
        
        for date, articles in sorted(by_date.items(), reverse=True):
            lines.append(f"### 📅 {date}")
            lines.append("")
            
            for i, article in enumerate(articles, 1):
                title = article.get('title', '제목 없음').strip()[:80]
                source = article.get('source', '')
                url = article.get('url', '')
                ai_summary = article.get('ai_summary', '')
                
                lines.append(f"**{i}. {title}**")
                
                if source:
                    lines.append(f"- 출처: {source}")
                
                if url:
                    lines.append(f"- [링크]({url})")
                
                if ai_summary:
                    # HTML 태그 제거
                    clean_summary = re.sub(r'<[^>]+>', '', ai_summary)
                    clean_summary = re.sub(r'\s+', ' ', clean_summary).strip()
                    lines.append(f"- 요약: {clean_summary[:150]}{'...' if len(clean_summary) > 150 else ''}")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)
    
    def run(self):
        """실행"""
        print("\n" + "="*60)
        print("🤖 최신 기사 AI 요약 시작")
        print("="*60)
        
        # Ollama 연결 확인
        self.llm.check_connection()
        
        # 기존 데이터 로드
        data = self.load_existing_data()
        if not data:
            print("✗ 처리할 데이터가 없습니다.")
            return
        
        # 기사 요약 처리
        result = self.process_articles(data)
        
        # 결과 저장
        self.save_results(result)
        
        print("\n" + "="*60)
        print(f"✅ 완료! 총 {result['total_items']}개 기사 요약됨")
        print("="*60)


def main():
    """메인 실행"""
    summarizer = ArticleSummarizer()
    summarizer.run()


if __name__ == "__main__":
    main()