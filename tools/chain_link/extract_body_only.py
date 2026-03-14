from bs4 import BeautifulSoup
import os

DATA_TXT = os.path.join(os.path.dirname(__file__), 'data.txt')
BODY_TXT = os.path.join(os.path.dirname(__file__), 'body_only.txt')

with open(DATA_TXT, 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
body = soup.body

with open(BODY_TXT, 'w', encoding='utf-8') as f:
    f.write(str(body))

print(f'body 태그 내용이 {BODY_TXT}에 저장되었습니다.')
