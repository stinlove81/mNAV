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
    """문자열에서 숫자와 소수점만 추출하여 숫자로 변환"""
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_mtpl_engine():
    # 🎯 메타플래닛 분석 페이지
    url = "https://metaplanet.jp/jp/analytics"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 메타플래닛(3350) 확정 번호 수집 시작...")
        driver.get(url)
        
        # 데이터 렌더링을 위해 15초 충분히 대기
        time.sleep(15) 

        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        def get_by_key(idx_num):
            try: return all_content[idx_num - 1]
            except: return "0"

        # --- [데이터 추출 - 사장님 확정 번호] ---
        # 27번: 주가(Price)
        price_raw = clean_num(get_by_key(36))
        # 217번: mNAV (확정된 위치)
        mtpl_mnav = clean_num(get_by_key(223))

        # 사장님 웹사이트 인자 명칭에 맞게 매핑
        update_data = {
            "3350 price": price_raw,
            "3350 mnav": mtpl_mnav,
        }

        # 데이터 검증 후 Firebase 전송
        if price_raw > 0:
            db.reference('/params').update(update_data)
            print(f"✅ MTPL 업데이트 완료: {price_raw}¥ / {mtpl_mnav}x")
        else:
            print(f"🚨 데이터 수집 실패 (27번: {get_by_key(27)}, 217번: {get_by_key(217)})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_mtpl_engine()