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
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 메타플래닛(mtpl) mNAV 타겟 수색 시작...")
        driver.get(url)
        time.sleep(25) # 메타플래닛 사이트 특성상 충분히 대기

        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        # --- [🔎 210번 주변 집중 디버깅 출력] ---
        print("\n" + "🔍"*20)
        print("🚩 [mNAV 수색] 210번 인덱스 기준 위아래 50개 리스트")
        
        target = 210
        start = max(1, target - 50)
        end = min(len(all_content), target + 50)
        
        for i in range(start, end + 1):
            marker = " ⭐ [현재 210번 설정 위치]" if i == target else ""
            print(f"  [{i}] {all_content[i-1]}{marker}")
        
        print("🔍"*20 + "\n")

        def get_by_key(idx_num):
            try: return all_content[idx_num - 1]
            except: return "0"

        # 주가는 기존 27번 그대로!
        price_raw = clean_num(get_by_key(27))
        # mNAV는 일단 210번으로 시도 (로그 보고 수정 예정)
        mtpl_mnav = clean_num(get_by_key(210))

        if price_raw > 0:
            db.reference('/params').update({
                "3350 price": price_raw,
                "3350 mnav": mtpl_mnav,
            })
            print(f"✅ 주가(27번) 수집 성공: {price_raw}¥")
            print(f"✅ mNAV(현재 210번) 시도 수치: {mtpl_mnav}x")
        else:
            print("🚨 주가(27번)를 찾지 못했습니다. 번호가 전체적으로 밀렸는지 확인 필요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_mtpl_engine()