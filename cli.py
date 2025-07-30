import requests
import time
import os
import json
import undetected_chromedriver as uc

# Puter 관련 상수
PUTER_URL = "https://puter.com"
PUTER_RESPONSE_URL = "https://api.puter.com/drivers/call"
PUTER_MODELS_LIST_URL = "https://puter.com/puterai/chat/models"

# 전역 토큰 변수
puter_token = None

def get_puter_auth_token(force_refresh=False):
    """
    Puter 인증 토큰을 파일에서 읽거나, 필요시 새로 획득합니다.
    """
    global puter_token
    if not force_refresh and puter_token:
        return puter_token

    if force_refresh and os.path.exists("puter_auth_token"):
        os.remove("puter_auth_token")
        puter_token = None

    if os.path.exists("puter_auth_token"):
        with open("puter_auth_token", encoding='UTF-8', mode='r') as f:
            puter_token = f.read().strip()
            return puter_token

    # 새로 획득 (브라우저 자동화)
    try:
        with uc.Chrome() as driver:
            driver.get(PUTER_URL)
            print("[Puter] 로그인 후 10초 대기...")
            time.sleep(10)
            for cookie in driver.get_cookies():
                if cookie['name'] == 'puter_auth_token':
                    with open('puter_auth_token', encoding='UTF-8', mode='w+') as f:
                        f.write(cookie['value'])
                    puter_token = cookie['value']
                    return puter_token
    except Exception as e:
        print(f"[Puter] 토큰 획득 실패: {e}")
    return None

def generate_puter_response(token, messages, model, stream=True):
    """
    Puter API로 메시지를 전송하고 응답을 반환합니다.
    """
    headers = {
        "authorization": f"Bearer {token}",
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
            "stream": stream,
            "web_search_options": {
                "search_context_size": "high"
            }
        }
    }
    return requests.post(PUTER_RESPONSE_URL, headers=headers, json=data, stream=stream)

def puter_chat(messages, model, stream=True):
    """
    Puter API를 통해 AI와 대화하고, 스트리밍 텍스트를 yield합니다.
    messages: [{"role": "user", "content": "질문"}, ...]
    model: "openrouter:openai/gpt-4.1" 등
    """
    global puter_token
    if not puter_token:
        puter_token = get_puter_auth_token()
    if not puter_token:
        raise RuntimeError("Puter 토큰을 획득할 수 없습니다.")

    retried = False
    while True:
        response = generate_puter_response(puter_token, messages, model, stream=stream)
        if response.status_code in (401, 403) or response.status_code >= 500:
            print("[Puter] 토큰 오류/서버 오류. 토큰 갱신 후 재시도.")
            puter_token = get_puter_auth_token(force_refresh=True)
            if retried:
                raise RuntimeError(f"Puter API Error: {response.status_code} - {response.text}")
            retried = True
            continue
        if response.status_code != 200:
            raise RuntimeError(f"Puter API Error: {response.status_code} - {response.text}")

        buffer = ""
        for chunk in response.iter_lines(decode_unicode=True):
            if not chunk:
                continue
            if isinstance(chunk, bytes):
                chunk = chunk.decode('utf-8')
            buffer += chunk
            try:
                data = json.loads(buffer)
                buffer = ""
                # Puter 특유의 에러 JSON 처리
                if (
                    isinstance(data, dict) and
                    data.get("success") is False and
                    data.get("error", {}).get("code") == "error_400_from_delegate"
                ):
                    print("[Puter] 내부 에러 JSON 감지. 토큰 갱신 후 재시도.")
                    puter_token = get_puter_auth_token(force_refresh=True)
                    if retried:
                        raise RuntimeError(data.get('error', {}).get('message', 'Unknown error'))
                    retried = True
                    break  # while True로 돌아가서 재시도
                if "text" in data:
                    yield data["text"]
            except json.JSONDecodeError:
                continue
        break

if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "현재 채팅은 사용자와의 1대1 채팅이다. 한국 청소년의 채팅 기법과 어투를 욕과 유행어를 좀 사용해서 정확하게 따라하며 사용자와 채팅. 챗봇의 이름은 지민. 이모지는 사용 자제. 답변은 짧게 작성. 줄바꿈을 두번 사용. 한국 청소년 채팅 기법, 어투, 욕, 유행어를 사용하여 진짜 청소년처럼 보이고 사용자의 답변에만 답할 것."},
    ]
    model = "openrouter:x-ai/grok-4"

    while True:
        user = input("User: ")
        messages.append({"role": "user", "content": user})
        context = []
        for text in puter_chat(messages, model):
            context.append(text)
            # print(text, end="", flush=True)
        # print()
        response = ''.join(context)
        print(response)
        messages.append({"role": "assistant", "content": response})