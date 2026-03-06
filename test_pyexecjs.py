#!/usr/bin/env python
# -*- coding: utf-8 -*-

import execjs
from pathlib import Path

# bitCalculation.v.0.1.js 로드
script_path = Path(__file__).parent / "youtube" / "bitCalculation.v.0.1.js"
print(f"Loading: {script_path}")

with open(script_path, 'r', encoding='utf-8') as f:
    js_code = f.read()

# 컨텍스트 생성
ctx = execjs.compile(js_code)

# 테스트 데이터
views = [100, 200, 150, 180, 220]

print(f"\nTest views: {views}")
print(f"Running BIT_MAX_NB(views, 5.5)...")

try:
    result_max = ctx.call("BIT_MAX_NB", views, 5.5)
    print(f"BIT_MAX_NB result: {result_max}")
except Exception as e:
    print(f"Error calling BIT_MAX_NB: {e}")

try:
    result_min = ctx.call("BIT_MIN_NB", views, 5.5)
    print(f"BIT_MIN_NB result: {result_min}")
except Exception as e:
    print(f"Error calling BIT_MIN_NB: {e}")
