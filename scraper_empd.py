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

def clean_num_first(text):
    """문자열에 숫자가 여러 개일 경우 가장 첫 번째 숫자만 추출 (EMPD 주가용)"""
    if not text: return 0
    # 모든 숫자(소수점 포함) 추출 후 첫 번째 것 선택
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try:
        return float(nums[0]) if nums else 0
    except: return 0

def clean_num(text):
    """일반적인 숫자 추출"""
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_empd_engine():
    url = "https://www.emperydigital.com/treasury-dashboard"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 EMPD(empd) 수집 시작...")
        driver.get(url)
        
        # 정밀 스캔 때 확인한 것처럼 로딩 시간이 넉넉해야 합니다.
        time.sleep(40) 

        # 모든 텍스트 수집 (정밀 스캔 V2와 동일한 로직으로 프레임까지 뒤집니다)
        all_texts = []
        # 메인 페이지 수집
        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_texts.extend([el.text.strip() for el in elements if el.text.strip()])

        # iframe 내부 수집
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                driver.switch_to.frame(iframe)
                time.sleep(2)
                inner_elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
                all_texts.extend([el.text.strip() for el in inner_elements if el.text.strip()])
                driver.switch_to.default_content()
            except:
                driver.switch_to.default_content()
                continue

        def get_by_key(idx_num):
            try:
                return all_texts[idx_num - 1]
            except: return ""

        # --- [데이터 추출] ---
        # 43번에서 첫 번째 숫자인 4.67 추출 (주가)
        empd_price = clean_num_first(get_by_key(43))
        # 52번에서 mNAV 추출
        empd_mnav = clean_num(get_by_key(52))

        # 사장님 웹사이트 인자 명칭: "empd price", "empd mnav"
        update_data = {
            "empd price": empd_price,
            "empd mnav": empd_mnav
        }

        # 데이터 검증 후 전송
        if empd_price > 0:
            db.reference('/params').update(update_data)
            print(f"✅ EMPD 업데이트 완료: {empd_price}$ / {empd_mnav}x")
        else:
            print("🚨 데이터를 찾지 못했습니다. 로딩 시간이 더 필요한지 확인해 주세요.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_empd_engine()