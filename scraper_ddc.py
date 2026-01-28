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

def run_ddc_engine():
    # 🎯 DDC 트레저리 차트 페이지
    url = "https://treasury.ddc.xyz/?tab=charts"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 깃허브 액션 환경에서 번호 밀림 방지를 위해 창 크기 고정
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 DDC(ddc) 확정 번호 수집 시작...")
        driver.get(url)
        
        # 대시보드 및 iframe 로딩 대기 (넉넉하게 10초)
        time.sleep(10) 

        all_texts = []
        # 메인 페이지 텍스트 수집
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_texts.extend([el.text.strip() for el in elements if el.text.strip()])

        # iframe 내부 텍스트까지 샅샅이 수집
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

        # --- [데이터 추출 - ASST와 동일한 포맷] ---
        # 123번 인덱스의 두 번째 숫자 (주가)
        ddc_price = get_nth_number(get_by_key(123), 2)
        # 178번 인덱스의 첫 번째 숫자 (mNAV)
        ddc_mnav = get_nth_number(get_by_key(178), 1)

        # 사장님 웹사이트 인자 명칭 그대로 유지
        update_data = {
            "ddc price": ddc_price,
            "ddc mnav": ddc_mnav
        }

        # 데이터 검증 후 Firebase 전송
        if ddc_price > 0:
            db.reference('/params').update(update_data)
            print(f"✅ DDC 업데이트 완료: {ddc_price}$ / {ddc_mnav}x")
        else:
            print(f"🚨 데이터 추출 실패 (123번: {get_by_key(123)}, 178번: {get_by_key(178)})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_ddc_engine()