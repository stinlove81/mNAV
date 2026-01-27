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

        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://mnav-watcher-default-rtdb.firebaseio.com/'
        })
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}"); exit()

def clean_num_last(text):
    if not text: return 0
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try:
        return float(nums[-1]) if nums else 0
    except: return 0

def clean_num(text):
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_asst_engine():
    url = "https://treasury.strive.com/?tab=charts"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080") # 창 크기 고정 (번호 밀림 방지)
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 ASST(asst) 정밀 디버깅 수집 시작...")
        driver.get(url)
        time.sleep(25) # 로딩 시간 확보

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

        # --- [🔎 디버깅 출력부] ---
        print("\n" + "="*50)
        print("🚩 [디버그] ASST 데이터 주변 탐색 (행 번호 확인용)")
        
        target_indices = [84, 148]
        for target in target_indices:
            print(f"\n📍 {target}번 인덱스 근처 데이터 (위아래 5개):")
            for i in range(target - 5, target + 6):
                if 0 < i <= len(all_texts):
                    marker = " ⭐ [TARGET]" if i == target else ""
                    print(f"  [{i}] {all_texts[i-1]}{marker}")
        print("="*50 + "\n")

        def get_by_key(idx_num):
            try: return all_texts[idx_num - 1]
            except: return ""

        # 데이터 추출
        asst_price = clean_num_last(get_by_key(84))
        asst_mnav = clean_num(get_by_key(148))

        update_data = {
            "asst price": asst_price,
            "asst mnav": asst_mnav
        }

        if asst_price > 0:
            db.reference('/params').update(update_data)
            print(f"✅ 업데이트 완료: {asst_price}$ / {asst_mnav}x")
        else:
            print("🚨 84번에서 가격을 찾지 못했습니다. 위 로그에서 번호를 다시 확인하세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_asst_engine()