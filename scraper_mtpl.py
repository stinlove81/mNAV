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

# 1. Firebase 초기화
firebase_key = os.environ.get('FIREBASE_KEY')
is_github = firebase_key is not None

try:
    if not firebase_admin._apps:
        if is_github:
            key_dict = json.loads(firebase_key)
            cred = credentials.Certificate(key_dict)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://mnav-watcher-default-rtdb.firebaseio.com/'})
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}"); exit()

def clean_num(text):
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
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
        print(f"🌐 메타플래닛(3350) 정밀 스캔 시작...")
        driver.get(url)
        time.sleep(60) 

        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        def get_safe(idx):
            try: return all_content[idx - 1]
            except: return "N/A"

        # --- [정밀 스캔 구간 설정] ---
        # 1. 주가 주변 (27번 기준 ±20)
        print("\n🔍 [SECTION 1: PRICE SCAN (Index 7 ~ 47)]")
        for i in range(7, 48):
            val = get_safe(i)
            mark = "⭐️ [TARGET]" if i == 27 else ""
            print(f"Index {i:03d}: {val} {mark}")

        # 2. mNAV 주변 (217번 기준 ±20)
        print("\n🔍 [SECTION 2: MNAV SCAN (Index 197 ~ 237)]")
        for i in range(197, 238):
            val = get_safe(i)
            mark = "⭐️ [TARGET]" if i == 217 else ""
            print(f"Index {i:03d}: {val} {mark}")

        # --- [데이터 추출 및 업데이트] ---
        price_raw = clean_num(get_safe(27))
        mtpl_mnav = clean_num(get_safe(217))

        update_data = {
            "3350 price": price_raw,
            "3350 mnav": mtpl_mnav,
        }

        if price_raw > 0:
            db.reference('/params').update(update_data)
            print(f"\n✅ 업데이트 실행됨: {price_raw}¥ / {mtpl_mnav}x")
        else:
            print("\n🚨 주가 수집 실패: 로그를 보고 인덱스 번호를 다시 확인하세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_mtpl_engine()