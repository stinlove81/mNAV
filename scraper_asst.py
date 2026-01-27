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
        firebase_admin.initialize_app(cred, {'databaseURL': 'https://mnav-watcher-default-rtdb.firebaseio.com/'})
except Exception as e:
    print(f"❌ Firebase 초기화 실패: {e}"); exit()

def clean_num_last(text):
    if not text: return 0
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try: return float(nums[-1]) if nums else 0
    except: return 0

def clean_num(text):
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try: return float(cleaned) if '.' in cleaned else int(cleaned)
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
        print(f"🌐 ASST(asst) 광범위 디버깅 시작...")
        driver.get(url)
        time.sleep(35) # 로딩 시간 더 넉넉히

        all_texts = []
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_texts.extend([el.text.strip() for el in elements if el.text.strip()])

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(5)
                inner_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
                all_texts.extend([el.text.strip() for el in inner_elements if el.text.strip()])
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content(); continue

        # --- [🔎 초광범위 디버깅 출력부] ---
        print("\n" + "🚨"*20)
        print("🚩 [초광범위 디버그] ASST 데이터 투망 감시 (위아래 30개)")
        
        # 84번과 148번 주변을 훑습니다.
        scan_targets = [84, 148]
        for target in scan_targets:
            print(f"\n🎯 {target}번 인덱스 기준 위아래 30개 탐색:")
            start = max(1, target - 30)
            end = min(len(all_texts), target + 30)
            for i in range(start, end + 1):
                marker = " <--- ★ 현재 타겟 설정 위치" if i == target else ""
                print(f"  [{i}] {all_texts[i-1]}{marker}")
        
        print("\n" + "🚨"*20 + "\n")

        def get_by_key(idx_num):
            try: return all_texts[idx_num - 1]
            except: return ""

        # 우선 기존 번호대로 시도는 해봅니다.
        asst_price = clean_num_last(get_by_key(84))
        asst_mnav = clean_num(get_by_key(148))

        if asst_price > 0:
            db.reference('/params').update({"asst price": asst_price, "asst mnav": asst_mnav})
            print(f"✅ 일단 업데이트 시도 완료: {asst_price}$ / {asst_mnav}x")
        else:
            print("🚨 현재 설정된 84번에서 숫자를 못 찾았습니다. 위 로그에서 정답 번호를 찾으세요!")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_asst_engine()