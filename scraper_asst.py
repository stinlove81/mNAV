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

def get_nth_number(text, n):
    """문자열에서 n번째 숫자 덩어리를 추출 (1부터 시작)"""
    if not text: return 0
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try:
        return float(nums[n-1]) if len(nums) >= n else 0
    except: return 0

def run_asst_engine():
    url = "https://treasury.strive.com/?tab=charts"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 ASST(asst) 확정 번호 수집 시작...")
        driver.get(url)
        time.sleep(30) # 대시보드 로딩 대기

        all_texts = []
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_texts.extend([el.text.strip() for el in elements if el.text.strip()])

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(3)
                inner_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
                all_texts.extend([el.text.strip() for el in inner_elements if el.text.strip()])
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content(); continue

        def get_by_key(idx_num):
            try: return all_texts[idx_num - 1]
            except: return ""

        # --- [데이터 추출 - 사장님 확정 번호] ---
        # 123번의 두 번째 숫자 (주가)
        asst_price = get_nth_number(get_by_key(123), 2)
        # 178번의 첫 번째 숫자 (mNAV)
        asst_mnav = get_nth_number(get_by_key(178), 1)

        if asst_price > 0:
            db.reference('/params').update({
                "asst price": asst_price,
                "asst mnav": asst_mnav
            })
            print(f"✅ ASST 업데이트 완료: {asst_price}$ / {asst_mnav}x")
        else:
            print(f"🚨 데이터 추출 실패 (123번: {get_by_key(123)}, 178번: {get_by_key(178)})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_asst_engine()