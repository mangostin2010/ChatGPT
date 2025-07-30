import undetected_chromedriver as uc
import time
import requests
import os
import json

URL = "https://puter.com"
RESPONSE_URL = "https://api.puter.com/drivers/call"
MODELS_LIST_URL = "https://puter.com/puterai/chat/models"

# ---------- 필요한 함수들 ----------

def fetch_models():
    response = requests.get(MODELS_LIST_URL)
    data = response.json()
    return data

def check_model(model_name):
    models = fetch_models()
    if model_name in models["models"]:
        return True
    return False

def get_puter_auth_token(save_as_file=True):
    dirs = os.listdir()
    if "puter_auth_token" in dirs:
        # File exists
        with open("puter_auth_token", encoding='UTF-8', mode='r') as f:
            content = f.read()
            print("[LOG] 이미 존재하는 token을 사용합니다.")
            print(f"[LOG] token: {content}")
            return content

    with uc.Chrome() as driver:
        driver.get(URL)
        print("[LOG] 로그인 후 10초 기다립니다...")
        time.sleep(10)  # 접속하면 알아서 로그인해주드라 ㅋ
        for cookie in driver.get_cookies():
            if cookie['name'] == 'puter_auth_token':
                print("[LOG] token:", cookie['value'])
                
                if save_as_file:
                    with open('puter_auth_token', encoding='UTF-8', mode='w+') as f:
                        f.write(cookie['value'])
                return cookie['value']
    return None

def generate_response(API_KEY: str, messages: list, model: str, stream: bool = False):
    model_status = check_model(model)
    if model_status != True:
        raise Exception(f"Model {model} doesn't exist. Please visit {MODELS_LIST_URL} to find correct model.")
    if "openrouter" not in model:
        print(f"[RECOMMENDATION] We recommend you to use openrouter models. Please visit {MODELS_LIST_URL}")

    headers = {
        "authorization": f"Bearer {API_KEY}",
        "content-type": "application/json;charset=UTF-8",
        "origin": "https://docs.puter.com",
        "referer": "https://docs.puter.com/",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6806.60 Safari/537.36"
    }
    data = {
        "driver": "openrouter",
        "interface": "puter-chat-completion",
        "test_mode": False,
        "method": "complete",
        "args": {
            "messages": messages,
            "model": model,
            "stream": stream,  # stream 인자 반영
            "web_search_options": {
                "search_context_size": "high"
            }
        }
    }
    if stream:
        with requests.post(RESPONSE_URL, headers=headers, json=data, stream=True) as response:
            if response.status_code != 200:
                print("에러:", response.status_code, response.text)
                return
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        # 예시: text 필드가 있으면 출력
                        if "text" in data:
                            print(data["text"], end="", flush=True)
                    except Exception:
                        continue
    else:
        response = requests.post(RESPONSE_URL, headers=headers, json=data)
        
        status_code = response.status_code
        result = response.text

        try:
            assistant = json.loads(result)["result"]["message"]
        except:
            print(result)
            return result, status_code
        return assistant, status_code


if __name__ == "__main__":
    token = get_puter_auth_token()

    messages = [
        {"role": "system", "content": "현재 채팅은 사용자와의 1대1 채팅이다. 한국 청소년의 채팅 기법과 어투를 욕과 유행어를 좀 사용해서 정확하게 따라하며 사용자와 채팅. 챗봇의 이름은 지민. 이모지는 사용 자제. 답변은 짧게 작성. 줄바꿈을 두번 사용. 한국 청소년 채팅 기법, 어투, 욕, 유행어를 사용하여 진짜 청소년처럼 보이고 사용자의 답변에만 답할 것."},
    ]

    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})
        response, status_code = generate_response(token, messages, model='claude-3-5-sonnet-latest')
        messages.append({"role": "assistant", "content": response})
        try:
            print(response["content"])
        except Exception as e:
            print(e)