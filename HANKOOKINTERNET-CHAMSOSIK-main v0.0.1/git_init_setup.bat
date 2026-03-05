@echo off
chcp 65001 > nul
echo ========================================
echo GitHub 저장소 초기 설정
echo ========================================
echo.

cd /d "e:\Ai project\사이트"

:: Git 초기화
echo [1/6] Git 저장소 초기화...
git init
echo.

:: 기본 브랜치를 main으로 설정
echo [2/6] 기본 브랜치 설정...
git branch -M main
echo.

:: 원격 저장소 추가
echo [3/6] 원격 저장소 추가...
git remote add origin https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK.git
echo.

:: 모든 파일 추가
echo [4/6] 파일 추가 중...
git add .
echo.

:: 첫 커밋
echo [5/6] 첫 커밋 생성...
git commit -m "Initial commit: N/B Database System with Category Feature"
echo.

:: Push
echo [6/6] GitHub에 업로드 중...
git push -u origin main
echo.

if errorlevel 1 (
    echo.
    echo ❌ 업로드 실패!
    echo.
    echo 다음을 확인해주세요:
    echo 1. GitHub 저장소가 생성되어 있는지 확인
    echo 2. Git 인증 정보 확인 (Personal Access Token 필요)
    echo 3. 기존 저장소라면 git pull origin main 먼저 실행
    echo.
    pause
    exit /b 1
) else (
    echo.
    echo ✅ GitHub 저장소 초기 설정 완료!
    echo Repository: https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK
    echo.
    echo 다음부터는 upload_to_github.bat 을 사용하세요.
    echo.
)

pause
