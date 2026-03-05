"""
Ollama IDE - GPT 같은 채팅 인터페이스
터미널 기반 대화형 AI 챗봇
"""

import os
import json
import requests
from datetime import datetime
from pathlib import Path

# 설정
OLLAMA_URL = "http://localhost:11434"
HISTORY_DIR = "data/ollama_chat"
os.makedirs(HISTORY_DIR, exist_ok=True)

# 색상 코드
class Color:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    GRAY = '\033[90m'


def print_colored(text, color=Color.RESET):
    print(f"{color}{text}{Color.RESET}")


def get_available_models():
    """사용 가능한 Ollama 모델 조회"""
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        response.raise_for_status()
        data = response.json()
        models = [m['name'] for m in data.get('models', [])]
        return models
    except Exception as e:
        print_colored(f"❌ Ollama 연결 실패: {e}", Color.RED)
        print_colored("   Ollama 앱이 실행 중인지 확인하세요.", Color.GRAY)
        return []


def select_model(models):
    """모델 선택"""
    if not models:
        return None
    
    print_colored("\n사용 가능한 모델:", Color.CYAN)
    for i, model in enumerate(models, 1):
        print(f"  {i}. {model}")
    
    while True:
        try:
            choice = input(f"\n모델 선택 (1-{len(models)}) [기본: 1]: ").strip()
            if not choice:
                return models[0]
            idx = int(choice) - 1
            if 0 <= idx < len(models):
                return models[idx]
            print_colored("잘못된 선택입니다.", Color.RED)
        except (ValueError, KeyboardInterrupt):
            return models[0]


def chat_with_ollama(model, prompt, stream=False):
    """Ollama API 호출"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": stream
            },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()
        return data.get('response', ''), None
    except Exception as e:
        return None, str(e)


def save_chat_history(model, history):
    """채팅 히스토리 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(HISTORY_DIR, f"chat_{timestamp}.json")
    
    data = {
        "model": model,
        "timestamp": datetime.now().isoformat(),
        "messages": history
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filename


def load_recent_chats(limit=5):
    """최근 대화 불러오기"""
    files = list(Path(HISTORY_DIR).glob("chat_*.json"))
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    chats = []
    for file in files[:limit]:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chats.append({
                    'file': file.name,
                    'timestamp': data.get('timestamp', ''),
                    'model': data.get('model', ''),
                    'message_count': len(data.get('messages', []))
                })
        except Exception:
            continue
    
    return chats


def print_banner():
    """시작 배너 출력"""
    print_colored("\n" + "="*60, Color.CYAN)
    print_colored("  🤖 Ollama IDE - GPT 같은 채팅 인터페이스", Color.BOLD + Color.GREEN)
    print_colored("="*60, Color.CYAN)
    print_colored("  명령어:", Color.YELLOW)
    print_colored("    /exit   - 종료", Color.GRAY)
    print_colored("    /clear  - 화면 지우기", Color.GRAY)
    print_colored("    /save   - 대화 저장", Color.GRAY)
    print_colored("    /model  - 모델 변경", Color.GRAY)
    print_colored("    /history - 최근 대화 보기", Color.GRAY)
    print_colored("="*60 + "\n", Color.CYAN)


def print_message(role, content, color):
    """메시지 출력"""
    prefix = "👤 You" if role == "user" else "🤖 AI"
    print_colored(f"\n{prefix}:", color + Color.BOLD)
    print_colored(content, color)


def main():
    """메인 실행 함수"""
    print_banner()
    
    # 모델 선택
    models = get_available_models()
    if not models:
        print_colored("사용 가능한 모델이 없습니다.", Color.RED)
        return
    
    current_model = select_model(models)
    print_colored(f"\n✅ 선택된 모델: {current_model}\n", Color.GREEN)
    
    # 최근 대화 표시
    recent = load_recent_chats(3)
    if recent:
        print_colored("최근 대화:", Color.CYAN)
        for chat in recent:
            print(f"  • {chat['file']} - {chat['message_count']}개 메시지 ({chat['model']})")
        print()
    
    # 대화 시작
    history = []
    
    while True:
        try:
            # 사용자 입력
            user_input = input(f"{Color.BLUE}You > {Color.RESET}").strip()
            
            if not user_input:
                continue
            
            # 명령어 처리
            if user_input.startswith('/'):
                cmd = user_input.lower()
                
                if cmd == '/exit' or cmd == '/quit':
                    if history:
                        save_path = save_chat_history(current_model, history)
                        print_colored(f"\n💾 대화 저장됨: {save_path}", Color.GREEN)
                    print_colored("👋 종료합니다.\n", Color.CYAN)
                    break
                
                elif cmd == '/clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print_banner()
                    continue
                
                elif cmd == '/save':
                    save_path = save_chat_history(current_model, history)
                    print_colored(f"💾 저장됨: {save_path}", Color.GREEN)
                    continue
                
                elif cmd == '/model':
                    models = get_available_models()
                    current_model = select_model(models)
                    print_colored(f"✅ 모델 변경: {current_model}", Color.GREEN)
                    continue
                
                elif cmd == '/history':
                    recent = load_recent_chats(5)
                    if recent:
                        print_colored("\n최근 대화:", Color.CYAN)
                        for i, chat in enumerate(recent, 1):
                            print(f"  {i}. {chat['file']} - {chat['message_count']}개 ({chat['model']})")
                    else:
                        print_colored("저장된 대화가 없습니다.", Color.GRAY)
                    continue
                
                else:
                    print_colored("알 수 없는 명령어입니다.", Color.RED)
                    continue
            
            # 사용자 메시지 저장
            history.append({"role": "user", "content": user_input})
            
            # AI 응답 생성
            print_colored(f"\n{Color.GRAY}생성 중...{Color.RESET}", Color.GRAY)
            response, error = chat_with_ollama(current_model, user_input)
            
            if error:
                print_colored(f"❌ 오류: {error}", Color.RED)
                history.pop()  # 실패한 메시지 제거
                continue
            
            if not response:
                print_colored("❌ 응답을 생성할 수 없습니다.", Color.RED)
                history.pop()
                continue
            
            # AI 응답 저장 및 출력
            history.append({"role": "assistant", "content": response})
            print_message("assistant", response, Color.GREEN)
            
        except KeyboardInterrupt:
            print_colored("\n\n⚠️  Ctrl+C 감지됨. 종료하려면 /exit 입력", Color.YELLOW)
            continue
        except Exception as e:
            print_colored(f"\n❌ 예상치 못한 오류: {e}", Color.RED)
            continue
    
    print()


if __name__ == "__main__":
    main()
