import json
import time
import re
import os
from datetime import datetime, timedelta, timezone
import firebase_admin
from firebase_admin import credentials, db
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# 1. Firebase 초기화 (mNAV WATCHER 전용)
firebase_key = os.environ.get('FIREBASE_KEY')
is_github = firebase_key is not None

try:
    if not firebase_admin._apps:
        if is_github:
            key_dict = json.loads(firebase_key)
            cred = credentials.Certificate(key_dict)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")

        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://mnav-watcher-default-rtdb.firebaseio.com/'
        })
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}")
    exit()

def clean_num(text):
    if not text: return 0
    text = str(text).split('\n')[0]
    cleaned = re.sub(r'[^\d.]', '', text)
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_mtpl_engine():
    url = "https://metaplanet.jp/jp/analytics"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 메타플래닛(3350) 수집 시작: {url}")
        start_time = time.time()
        driver.get(url)
        
        print("⏳ 대시보드 로딩 대기 (15초)...")
        time.sleep(15) 

        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        def get_by_key(idx_num):
            try:
                return all_content[int(idx_num) - 1]
            except: return "0"

        # --- [추출 및 단위 조정 - 사장님 기존 로직] ---
        # 27번: 가격, 90번: EV, 66번: BTC Reserve
        price_raw = clean_num(get_by_key("27"))
        ev_raw = clean_num(get_by_key("90")) / 10
        btc_reserve_raw = clean_num(get_by_key("66")) / 10

        # mNAV 계산
        mtpl_mnav = round(ev_raw / btc_reserve_raw, 2) if btc_reserve_raw != 0 else 0

        # 사장님 웹사이트 인자 명칭에 맞게 매핑 ("3350" 키워드 사용)
        update_data = {
            "3350 price": price_raw,
            "3350 mnav": mtpl_mnav,
        }

        # 데이터 검증 후 전송
        if price_raw > 0:
            db.reference('/params').update(update_data)
            print(f"✅ 메타플래닛 업데이트 완료: {price_raw}¥ / {mtpl_mnav}x")
        else:
            print("🚨 유효 데이터를 찾지 못했습니다. 업데이트를 스킵합니다.")

    except Exception as e:
        print(f"❌ 실행 중 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_mtpl_engine()