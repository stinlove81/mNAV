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
    """문자열에 숫자가 여러 개일 경우 가장 마지막 숫자만 추출 (DDC 주가용)"""
    if not text: return 0
    # 모든 숫자(소수점 포함) 추출 후 마지막 것 선택
    nums = re.findall(r'\d+\.\d+|\d+', str(text).replace(',', ''))
    try:
        return float(nums[-1]) if nums else 0
    except: return 0

def clean_num(text):
    """일반적인 숫자 추출"""
    if not text: return 0
    cleaned = re.sub(r'[^\d.]', '', str(text).split('\n')[0])
    try:
        return float(cleaned) if '.' in cleaned else int(cleaned)
    except: return 0

def run_ddc_engine():
    url = "https://treasury.ddc.xyz/?tab=charts"
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        print(f"🌐 DDC(ddc) 수집 시작...")
        driver.get(url)
        
        # 대시보드 로딩 대기
        time.sleep(5) 

        elements = driver.find_elements(By.CSS_SELECTOR, "h1, h2, h3, h4, p, span, div")
        all_content = [el.text.strip() for el in elements if el.text.strip()]

        def get_by_key(idx_num):
            try:
                return all_content[idx_num - 1]
            except: return ""

        # --- [데이터 추출] ---
        # 90번에서 마지막 숫자인 2.88 추출 (주가)
        ddc_price = clean_num_last(get_by_key(90))
        # 147번에서 mNAV 추출
        ddc_mnav = clean_num(get_by_key(147))

        # 사장님 웹사이트 인자 명칭: "ddc price", "ddc mnav"
        update_data = {
            "ddc price": ddc_price,
            "ddc mnav": ddc_mnav
        }

        # 데이터 검증 후 전송
        if ddc_price > 0:
            db.reference('/params').update(update_data)
            print(f"✅ DDC 업데이트 완료: {ddc_price}$ / {ddc_mnav}x")
        else:
            print("🚨 데이터를 찾지 못했습니다. 번호가 바뀌었는지 확인이 필요합니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_ddc_engine()