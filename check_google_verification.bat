@echo off
chcp 65001 > nul
echo ========================================
echo Google Search Console TXT 레코드 확인
echo ========================================
echo.
echo 도메인: 참소식.com (xn--9l4b4xi9r.com)
echo 확인할 TXT 레코드: google-site-verification=9uL_uu-SjwnPqAwADFbd7A1baOiWcr70czDRjwOqsec
echo.
echo [1] nslookup으로 확인
nslookup -type=TXT xn--9l4b4xi9r.com
echo.
echo [2] 다른 DNS 서버(8.8.8.8)로 확인
nslookup -type=TXT xn--9l4b4xi9r.com 8.8.8.8
echo.
echo ========================================
echo TXT 레코드가 보이면 인증 성공!
echo 안 보이면 DNS 전파 대기 필요 (1-24시간)
echo ========================================
pause
