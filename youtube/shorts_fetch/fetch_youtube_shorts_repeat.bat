@echo off
setlocal
chcp 65001 >nul
REM 반복적으로 유튜브 쇼츠를 fetch하고, 결과 파일을 서버에 업로드

REM 환경설정
set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/chamsosik"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com"
set "DIAGRAM_FILE=shorts_feed.xml"
set "INDEX_FILE=index.html"


:loop

REM 1. 네이버 블로그 RSS 다운로드
curl -L -o "%LOCAL_DIR%\naver_blog_rss.xml" "https://rss.blog.naver.com/dbghwns2.xml"

REM 2. 유튜브 쇼츠 수집
call fetch_youtube_shorts.bat

REM 3. 결과 XML을 참소식.com 폴더로 복사
copy /Y shorts_feed.xml "%LOCAL_DIR%\%DIAGRAM_FILE%" >nul

REM 4. sync_diagram.bat 실행 (동일 폴더 내에 있다고 가정)
call sync_diagram.bat

:wait
REM 10분(600초) 대기
ping -n 601 127.0.0.1 >nul
goto loop
