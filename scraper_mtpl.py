import json
import time
import re
import os
import firebase_admin
from firebase_admin import credentials, db
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def clean_num(text):
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_mtpl_recon():
    url = "https://metaplanet.jp/jp/analytics"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 메타플래닛 정밀 정찰 모드 가동...")
        driver.get(url)
        time.sleep(25) # 데이터 렌더링 대기

        # 모든 텍스트 요소 추출
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        # 🎯 사장님 요청: 주요 지점 위아래 30개씩 출력
        targets = [27, 217]
        
        print("\n" + "="*50)
        print("🎯 메타플래닛 인덱스 정밀 분석 결과")
        print("="*50)

        for center in targets:
            start_idx = max(1, center - 30)
            end_idx = min(len(all_content), center + 30)
            
            print(f"\n📍 기준 번호 {center}번 주변 (범위: {start_idx} ~ {end_idx})")
            print("-" * 30)
            
            for i in range(start_idx, end_idx + 1):
                val = all_content[i-1]
                mark = " ⭐ [현재 타겟]" if i == center else ""
                print(f"[{i:3d}번] : {val}{mark}")
        
        print("\n" + "="*50)
        print("✅ 정찰 종료. 로그에서 새로운 번호를 확인하세요!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_mtpl_recon()