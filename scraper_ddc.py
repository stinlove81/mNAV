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
    if not text: return 0
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try:
        return float(nums[n-1]) if len(nums) >= n else 0
    except: return 0

def run_ddc_engine():
    url = "https://treasury.ddc.xyz/?tab=charts"
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 DDC 주가 끝장 수색 시작...")
        driver.get(url)
        time.sleep(35) # 로딩 시간 최대 확보

        all_texts = []
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_texts.extend([el.text.strip() for el in elements if el.text.strip()])

        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(5)
                inner_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
                all_texts.extend([f"[Frame] {el.text.strip()}" for el in inner_elements if el.text.strip()])
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content(); continue

        # --- [🔎 사장님 전용: DDC 1~200번 전수조사] ---
        print("\n" + "🔥"*20)
        print("🚩 [DDC 전수조사] 1번부터 200번까지 싹 다 보여드립니다!")
        
        for i in range(0, min(200, len(all_texts))):
            idx = i + 1
            marker = " 👈 [현재 주가 타겟 123번]" if idx == 123 else ""
            print(f"  [{idx}] {all_texts[i]}{marker}")
        
        print("🔥"*20 + "\n")

        def get_by_key(idx_num):
            try: return all_texts[idx_num - 1]
            except: return ""

        # mNAV는 성공하셨으니 그대로 유지 (번호는 178번 맞으시죠?)
        ddc_mnav = get_nth_number(get_by_key(178), 1)
        
        # 주가는 일단 실패한 123번으로 두되, 로그를 보고 번호를 바꿀 예정입니다.
        ddc_price = get_nth_number(get_by_key(123), 2)

        print(f"📢 현재 설정 기준 결과: Price(${ddc_price}) / mNAV({ddc_mnav}x)")

        if ddc_price > 0:
            db.reference('/params').update({"ddc price": ddc_price, "ddc mnav": ddc_mnav})
            print(f"✅ 업데이트 성공!")
        else:
            print("🚨 주가 찾기 실패! 위 200개 목록에서 '$숫자'가 있는 번호를 찾아주세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_ddc_engine()