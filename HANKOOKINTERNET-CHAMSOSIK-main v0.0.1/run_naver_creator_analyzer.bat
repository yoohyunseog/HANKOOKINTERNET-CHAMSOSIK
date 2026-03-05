@echo off
chcp 65001 > nul
echo ======================================================
echo   네이버 크리에이터 트렌드 분석기 실행
echo ======================================================
echo.

cd /d "%~dp0"

REM Python 버전 확인
echo [1/3] Python 확인 중...
py --version
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    pause
    exit /b 1
)

REM 패키지 설치 (가상환경 없이 직접 설치)
echo [2/3] 필요한 패키지 설치 중...
py -m pip install --upgrade pip --quiet
py -m pip install -r 8BIT\requirements_naver_creator.txt --quiet

echo.
echo ✅ 준비 완료
echo.

REM 프로그램 실행
echo [3/3] 프로그램 실행...
py 8BIT\naver_creator_trend_analyzer.py

REM 비트코인 및 주식 키워드 수집
echo.
echo [4/4] 비트코인 & 주식 키워드 수집 중...
echo.

REM 비트코인 키워드 50개 검색
(
echo 비트코인
echo 이더리움
echo 비트코인 가격
echo 암호화폐
echo 비트코인 뉴스
echo 이더리움 가격
echo 비트코인 채굴
echo 암호화폐 거래소
echo 비트코인 전망
echo 디지털 자산
echo 블록체인
echo 코인 투자
echo 암호화폐 시세
echo 비트코인 반감기
echo 코인베이스
echo 업비트
echo 빗썸
echo 코인원
echo 바이낸스
echo 크립토
echo 블록체인 기술
echo 가상자산
echo NFT
echo 암호화폐 투자
echo 비트코인 채산성
echo 마이닝 풀
echo 월렛
echo 키 관리
echo 거래소 수수료
echo 암호화폐 보안
echo 스마트 컨트랙트
echo DeFi
echo 스테이킹
echo 시드 프레이즈
echo 콜드 지갑
echo 핫 지갑
echo 암호화폐 세금
echo 비트코인 선물
echo 옵션 거래
echo 레버리지
echo 숏팅
echo 차트 분석
echo 테크니컬 분석
echo 펀더멘탈
echo 시장 분석
echo 트레이딩 봇
echo 자동 매매
echo 기술적 지표
echo RSI
echo MACD
) > temp_bitcoin_keywords.txt

REM 주식 키워드 50개 검색
(
echo 주식
echo 한국 주식
echo 미국 주식
echo 코스피
echo 코스닥
echo S&P 500
echo 나스닥
echo 다우지수
echo 삼성
echo 현대자동차
echo 카카오
echo 네이버
echo 삼성전자
echo SK하이닉스
echo 삼성화학
echo 현대제철
echo LG화학
echo 포스코
echo 한국전력
echo 기아
echo 원유
echo 금
echo 달러
echo 인제
echo GDP
echo 인플레이션
echo 금리 인상
echo 경기 침체
echo 베어마켓
echo 불마켓
echo 주식 분석
echo 기술 분석
echo 펀더멘탈 분석
echo PER
echo PBR
echo ROE
echo 배당금
echo 주식 배당
echo 우량주
echo 성장주
echo 가치주
echo 소형주
echo 대형주
echo 중형주
echo ETF
echo 뮤추얼펀드
echo 펀드
echo 분산 투자
echo 포트폴리오
echo 재무 제표
) > temp_stock_keywords.txt

REM 애니메이션 키워드 50개 검색
(
echo 애니메이션
echo 열혈강호
echo 열혈강호 애니메이션
echo 열혈강호 웹툰
echo 원피스
echo 원피스 애니메이션
echo 원피스 웹툰
echo 네이버 웹툰
echo 카카오 웹툰
echo 웹툰 애니메이션
echo 만화 애니메이션
echo 일본 애니메이션
echo 진격의 거인
echo 진격의 거인 애니메이션
echo 진격의 거인 웹툰
echo 귀멸의 칼날
echo 귀멸의 칼날 애니메이션
echo 귀멸의 칼날 웹툰
echo 주술회전
echo 주술회전 애니메이션
echo 주술회전 웹툰
echo 나루토
echo 나루토 애니메이션
echo 나루토 웹툰
echo 블리치
echo 블리치 애니메이션
echo 블리치 웹툰
echo 드래곤볼
echo 드래곤볼 애니메이션
echo 슬램덩크
echo 슬램덩크 애니메이션
echo 슬램덩크 웹툰
echo 데스노트
echo 데스노트 애니메이션
echo 어떤 과학의 초전자포
echo 어떤 과학의 초전자포 애니메이션
echo 강철의 연금술사
echo 강철의 연금술사 애니메이션
echo 보이싱크
echo 보이싱크 웹툰
echo 신과함께
echo 신과함께 애니메이션
echo 신과함께 웹툰
echo 플래시
echo 플래시 웹툰
echo Webtoon
echo 만화
echo 한국 웹툰
echo 외국 애니메이션
echo 2D 애니메이션
echo 3D 애니메이션
) > temp_animation_keywords.txt

echo.
echo ✅ 키워드 수집 완료
echo.

REM 임시 파일 정리
if exist temp_bitcoin_keywords.txt del temp_bitcoin_keywords.txt
if exist temp_stock_keywords.txt del temp_stock_keywords.txt
if exist temp_animation_keywords.txt del temp_animation_keywords.txt

pause
