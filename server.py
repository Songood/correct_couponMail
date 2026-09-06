from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import time, os
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

app = Flask(__name__)
CORS(app)

ATTACH_BASE_DIR = r"C:\Users\외부망\Desktop\첨부파일"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

driver = None
is_logged_in = False

def get_driver():
    options = webdriver.EdgeOptions()
    return webdriver.Edge(options=options)

def compose_and_draft(data):
    send_mode = data.get("status") == "sent"
    sender = data.get("sender", "")
    wait = WebDriverWait(driver, 20)
    compose_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-hotkey=newMailWriteKey]")))
    compose_btn.click()
    time.sleep(2)
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(2)
    if sender:
        try:
            sender_btns = driver.find_elements(By.CSS_SELECTOR, ".btn_recentaddr a")
            sender_btn = sender_btns[1] if len(sender_btns) > 1 else sender_btns[0]
            sender_btn.click()
            time.sleep(1)
            xpath = "//a[contains(text(), '" + sender + "')]"
            sender_option = driver.find_element(By.XPATH, xpath)
            sender_option.click()
            time.sleep(0.5)
        except Exception as e:
            print("보내는 사람 변경 실패:", e)
    subject = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[name=subject], input.subject")))
    subject.clear()
    subject.send_keys(data["subject"])
    to_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[aria-label=받는사람]")))
    to_input.clear()
    to_input.send_keys(data["to"])
    to_input.send_keys(Keys.ENTER)
    time.sleep(0.5)
    if data.get("cc"):
        try:
            cc_input = driver.find_element(By.CSS_SELECTOR, "input[aria-label=참조]")
            cc_input.send_keys(data["cc"])
            cc_input.send_keys(Keys.ENTER)
            time.sleep(0.5)
        except:
            print("CC 입력 실패")
    try:
        iframe = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "iframe")))
        driver.switch_to.frame(iframe)
        editor = driver.find_element(By.CSS_SELECTOR, "div.workseditor-content")
        driver.execute_script("arguments[0].innerHTML = arguments[1]", editor, data["body"])
        driver.switch_to.default_content()
    except Exception as e:
        print("본문 입력 실패:", e)
    time.sleep(0.5)
    if data.get("attachDir"):
        attach_path = os.path.join(ATTACH_BASE_DIR, data["attachDir"])
        if os.path.exists(attach_path):
            files = [f for f in os.listdir(attach_path) if os.path.isfile(os.path.join(attach_path, f))]
            if files:
                try:
                    file_input = driver.find_element(By.CSS_SELECTOR, "input[type=file]")
                    for fname in files:
                        file_input.send_keys(os.path.abspath(os.path.join(attach_path, fname)))
                        time.sleep(1)
                except:
                    print("파일 첨부 실패")
    try:
        if send_mode:
            btn = driver.find_element(By.CSS_SELECTOR, "button[data-hotkey=sendKey]")
            btn.click()
            print("발송 완료:", data["subject"])
        else:
            btn = driver.find_element(By.CSS_SELECTOR, "button[data-hotkey=saveKey]")
            btn.click()
            print("임시저장 완료:", data["subject"])
        time.sleep(2)
        driver.switch_to.window(driver.window_handles[0])
    except Exception as e:
        print("버튼 클릭 실패:", e)
    time.sleep(1)

@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

@app.route("/status", methods=["GET"])
def status():
    return jsonify({"logged_in": is_logged_in})

@app.route("/send", methods=["POST"])
def send():
    data = request.json
    print("메일 작성 요청:", data.get("subject"))
    try:
        compose_and_draft(data)
        return jsonify({"success": True})
    except Exception as e:
        print("오류:", e)
        return jsonify({"success": False, "error": str(e)})

if __name__ == "__main__":
    print("쿠칩 정산 메일 자동화 서버")
    driver = get_driver()
    driver.get("https://mail.worksmobile.com/")
    print("브라우저가 열렸습니다! 로그인 후 메일함까지 이동한 뒤 Enter를 눌러주세요.")
    input(">> 준비되면 Enter: ")
    is_logged_in = True
    print("서버 시작! http://localhost:5000 으로 접속하세요.")
    app.run(port=5000)
