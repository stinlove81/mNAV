import json
import time
import re
import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. Firebase 설정 (새로운 mnav-watcher 주소 적용)
firebase_key = os.environ.get('FIREBASE_KEY')
is_github = firebase_key is not None

try:
    if is_github:
        key_dict = json.loads(firebase_key)
        cred = credentials.Certificate(key_dict)
    else:
        # 로컬 실행 시에는 serviceAccountKey.json 파일이 필요합니다.
        cred = credentials.Certificate("serviceAccountKey.json")
    
    # 사장님의 새로운 파이어베이스 주소로 초기화
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://mnav-watcher-default-rtdb.firebaseio.com/'
    })
except Exception as e:
    print(f"Firebase 초기화 실패: {e}"); exit()

def clean_num(text):
    """문자열에서 숫자와 소수점만 남기고 제거"""
    if not text: return 0
    text = text.split('\n')[0]
    cleaned = re.sub(r'[^\d.]', '', str(text))
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_engine():
    url = "https://www.strategy.com" # MSTR 데이터 소스
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"[{datetime.now()}] MSTR 데이터 수집 시작...")
        driver.get(url)
        time.sleep(15) # 페이지 로딩 대기

        # 전체 텍스트 요소 추출
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        def get_by_key(key_num):
            try:
                idx = int(key_num) - 1
                return all_content[idx]
            except: return ""

        # ---------------------------------------------------------
        # 🎯 MSTR 핵심 데이터 추출 (사장님 지정 번호 기반)
        # ---------------------------------------------------------
        mstr_price = clean_num(get_by_key("19"))  # 19번: MSTR 가격
        ev = clean_num(get_by_key("46"))          # 46번: Enterprise Value
        btc_reserve = clean_num(get_by_key("83")) # 83번: BTC Reserve
        
        # mNAV 계산
        mstr_mnav = round(ev / btc_reserve, 2) if btc_reserve != 0 else 0

        # 사장님이 요청하신 인자 명칭으로 데이터 구성
        update_data = {
            "mstr price": mstr_price,
            "mstr mnav": mstr_mnav,
            "last_updated": datetime.now().strftime("%b %d, %Y, %H:%M UTC")
        }

        # 데이터 검증 (가격이 0이면 문제 있는 것으로 간주)
        if mstr_price > 0:
            db.reference('/params').update(update_data)
            print(f"✅ MSTR 업데이트 성공: {mstr_price}$ / {mstr_mnav}x")
        else:
            print("⚠️ 유효한 데이터를 찾지 못해 업데이트를 스킵합니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_engine()