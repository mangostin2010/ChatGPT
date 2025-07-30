from flask import Flask, render_template, request, Response, jsonify, make_response
import requests
import re
import uuid
import sqlite3
import os
from datetime import datetime
import json
import random
import string
import codecs
import time
import undetected_chromedriver as uc
from fake_useragent import UserAgent

from g4f.client import Client
from g4f.Provider import Startnest

app = Flask(__name__)
app.secret_key = 'Ryanisstupid'

DB_PATH = 'chat.db'
client = Client()

ua = UserAgent()

# Puter API URLs
PUTER_URL = "https://puter.com"
PUTER_RESPONSE_URL = "https://api.puter.com/drivers/call"
PUTER_MODELS_LIST_URL = "https://puter.com/puterai/chat/models"

EXOML_GENID_URL = "https://exomlapi.com/api/genid"
EXOML_CHAT_URL = "https://exomlapi.com/api/chat"
EXOML_ANTIBOT_ID = "bB0zbFxpjIvh3CzdYBtxyxWnAhhe5a4K-de37df91"

MODEL_LIST = [
    {"label": "Perplexity Sonar Pro", "desc": "실시간 웹 검색과 여러 출처를 인용해 정확한 답변을 제공하는 고성능 검색 및 질의응답 모델. 대규모 문맥 처리와 복잡한 다단계 질문에 특화됨.", "value": "openrouter:perplexity/sonar-pro"},
    {"label": "Perplexity Sonar Reasoning Pro", "desc": "심층 추론에 최적화된 모델로, 실시간 웹 데이터를 기반으로 복잡한 논리적 질문과 분석을 처리함.", "value": "openrouter:perplexity/sonar-reasoning-pro"},
    # {"label": "Perplexity Sonar Deep Research", "desc": "광범위하고 심층적인 인터넷 리서치에 최적화된 모델. 다수의 최신 출처와 긴 텍스트 분석 기능 제공.", "value": "openrouter:perplexity/sonar-deep-research"},

    # OpenAI Models
    # {"label": "GPT 4o", "desc": "ChatGPT에 사용되는 GPT-4o 모델.", "value": "openrouter:openai/chatgpt-4o-latest"},
    {"label": "GPT 4.1", "desc": "다양한 복잡한 작업에 강력하며, 텍스트 생성, 요약, 분석 등에서 최신 성능을 보이는 OpenAI의 주력 모델 중 하나.", "value": "openrouter:openai/gpt-4.1"},
    # {"label": "GPT 4.5 Preview", "desc": "GPT-4 라인업의 최신 프리뷰 버전으로, 더 향상된 자연어 처리와 작업 효율을 제공하는 플래그십 모델.", "value": "openrouter:openai/gpt-4.5-preview"},
    # {"label": "o3 Pro", "desc": "OpenAI의 고성능 대형 언어모델로, 전문적인 작업과 다단계 추론에 특화됨.", "value": "openrouter:openai/o3-pro"},
    {"label": "o3", "desc": "빠른 응답과 수학적으로 높은 정확도를 지향하는 OpenAI의 차세대 기반 모델.", "value": "openrouter:openai/o3"},
    {"label": "o4 Mini High", "desc": "높은 성능과 속도를 동시에 제공하는 초소형 플래그십 모델.", "value": "openrouter:openai/o4-mini-high"},
    # {"label": "o1 Pro", "desc": "복잡한 질의와 분석에 최적화된 OpenAI의 프로페셔널 대형 모델.", "value": "openrouter:openai/o1-pro"},

    # Anthropic Models
    # {"label": "Claude Opus 4", "desc": "Anthropic의 최상위 모델로, 인간 수준의 자연어 이해력과 창의적 문장 생성 능력을 가짐.", "value": "openrouter:anthropic/claude-opus-4"},
    {"label": "Claude Sonnet 4", "desc": "다양한 작업에서 준수한 속도와 정확성을 제공하는 고급 대형언어 모델.", "value": "openrouter:anthropic/claude-sonnet-4"},
    {"label": "Claude 3.7 Sonnet", "desc": "복잡한 추론과 자연스러운 언어 처리를 구현하는 Anthropic의 최신 플래그십 모델.", "value": "openrouter:anthropic/claude-3.7-sonnet"},
    # {"label": "Claude 3.7 Sonnet Thinking", "desc": "장기 문맥 이해와 심화 분석 능력을 강화한 Claude Sonnet 모델의 확장 버전.", "value": "openrouter:anthropic/claude-3.7-sonnet:thinking"},
    {"label": "Claude 3.5 Sonnet", "desc": "균형 잡힌 속도와 정확도를 제공하는 Anthropic의 첨단 자연어 처리 모델.", "value": "openrouter:anthropic/claude-3.5-sonnet"},

    # Google Models
    # {"label": "Gemini 2.5 Pro", "desc": "구글의 차세대 AI 플래그십 모델로, 실시간 정보 검색과 신속한 자연어 처리에 최적화됨.", "value": "openrouter:google/gemini-2.5-pro"},
    {"label": "Gemini 2.5 Flash", "desc": "실시간 처리와 응답 속도가 뛰어난 Google의 경량 AI 모델.", "value": "openrouter:google/gemini-2.5-flash"},

    # X AI Models
    # {"label": "Grok 3", "desc": "X AI의 강력한 대화형 AI 모델로, 실시간 인터넷 정보를 활용해 빠른 답변 제공.", "value": "openrouter:x-ai/grok-3-mini"},
    {"label": "Grok 3 Mini", "desc": "경량화된 구조로 빠르고 효율적인 실시간 처리에 특화된 Grok의 소형 버전.", "value": "openrouter:x-ai/grok-3-mini"},

    # Deepseek Models
    {"label": "Deepseek", "desc": "다양한 전문 작업에 활용할 수 있는 Deepseek의 플래그십 오픈소스 대형언어모델.", "value": "openrouter:deepseek/deepseek-chat-v3-0324:free"},
    {"label": "Deepseek r1", "desc": "강화된 추론과 논리 기능을 지닌 Deepseek의 최신 모델.", "value": "openrouter:deepseek/deepseek-r1-0528:free"},
]

puter_token = None  # 전역 변수로 선언

# Puter 관련 함수들
def get_puter_auth_token(force_refresh=False):
    global puter_token
    if not force_refresh and puter_token:
        return puter_token

    # force_refresh일 때 파일 삭제
    if force_refresh and os.path.exists("puter_auth_token"):
        os.remove("puter_auth_token")
        puter_token = None

    # 기존 파일에서 읽기
    if os.path.exists("puter_auth_token"):
        with open("puter_auth_token", encoding='UTF-8', mode='r') as f:
            content = f.read().strip()
            print("[LOG] 기존 토큰을 사용합니다.")
            puter_token = content
            return puter_token

    # 새로 획득
    try:
        with uc.Chrome() as driver:
            driver.get(PUTER_URL)
            print("[LOG] 로그인 후 10초 기다립니다...")
            time.sleep(10)
            for cookie in driver.get_cookies():
                if cookie['name'] == 'puter_auth_token':
                    print("[LOG] 새 토큰을 획득했습니다.")
                    with open('puter_auth_token', encoding='UTF-8', mode='w+') as f:
                        f.write(cookie['value'])
                    puter_token = cookie['value']
                    return puter_token
    except Exception as e:
        print(f"[ERROR] 토큰 획득 실패: {e}")
    return None

def check_puter_model(model_name):
    try:
        response = requests.get(PUTER_MODELS_LIST_URL)
        data = response.json()
        return model_name in data.get("models", [])
    except:
        return False

def generate_puter_response(token, messages, model, stream=True):
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
    print("USED MODEL", model)
    
    return requests.post(PUTER_RESPONSE_URL, headers=headers, json=data, stream=stream)

# 기존 데이터베이스 함수들
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id TEXT PRIMARY KEY,
            user_token TEXT,
            title TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS message (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            user_token TEXT,
            role TEXT,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chat(id)
        )
    """)
    db.commit()

def create_chat(chat_id, user_token, title="새 채팅"):
    db = get_db()
    db.execute("INSERT INTO chat (id, user_token, title) VALUES (?, ?, ?)", (chat_id, user_token, title))
    db.commit()

def save_message(chat_id, user_token, role, content):
    db = get_db()
    db.execute("INSERT INTO message (chat_id, user_token, role, content) VALUES (?, ?, ?, ?)", (chat_id, user_token, role, content))
    db.commit()

def get_messages(chat_id, user_token):
    db = get_db()
    cur = db.execute("SELECT role, content FROM message WHERE chat_id=? AND user_token=? ORDER BY id", (chat_id, user_token))
    return cur.fetchall()

def get_chat_list(user_token):
    db = get_db()
    cur = db.execute("SELECT id, title FROM chat WHERE user_token=? ORDER BY created_at DESC", (user_token,))
    return cur.fetchall()

def update_chat_title(chat_id, user_token, title):
    db = get_db()
    db.execute("UPDATE chat SET title=? WHERE id=? AND user_token=?", (title, chat_id, user_token))
    db.commit()

def chat_exists(chat_id, user_token):
    db = get_db()
    cur = db.execute("SELECT 1 FROM chat WHERE id=? AND user_token=?", (chat_id, user_token))
    return cur.fetchone() is not None

def has_user_messages(chat_id, user_token):
    db = get_db()
    cur = db.execute("SELECT 1 FROM message WHERE chat_id=? AND user_token=? AND role='user' LIMIT 1", (chat_id, user_token))
    return cur.fetchone() is not None

# ExoML 관련 함수들 (기존 유지)
def make_exoml_chat_id(timestamp):
    rand9 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=9))
    return f"chat-{timestamp}-{rand9}"

def generate_antiBotId():
    URL = "https://exomlapi.com/api/genid"
    payload = {
        "antiBotId": "",
        "timestamp": int(time.time() * 1000)
    }
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': ua.random
    }
    response = requests.post(URL, json=payload, headers=headers)
    return response.json()["antiBotId"]

def parse_exoml_stream(stream):
    decoder = codecs.getincrementaldecoder('utf-8')()
    buffer = ""
    for chunk in stream:
        if chunk:
            buffer += decoder.decode(chunk)
            while '\n' in buffer:
                line, buffer = buffer.split('\n', 1)
                line = line.strip()
                if not line:
                    continue
                if line.startswith('0:'):
                    try:
                        value = line[2:].strip()
                        if value.startswith('"') and value.endswith('"'):
                            value = json.loads(value)
                        yield value
                    except Exception:
                        pass
    if buffer:
        for line in buffer.split('\n'):
            line = line.strip()
            if line.startswith('0:'):
                value = line[2:].strip()
                if value.startswith('"') and value.endswith('"'):
                    value = json.loads(value)
                yield value

def convert_messages_for_exoml(messages):
    result = []
    for m in messages:
        result.append({
            "role": m['role'],
            "content": m['content'],
            "parts": [{"type": "text", "text": m['content']}]
        })
    return result

@app.route("/", methods=["GET"])
def index():
    user_token = request.cookies.get("user_token")
    if not user_token:
        user_token = str(uuid.uuid4())
        resp = make_response(render_template("index.html", models=MODEL_LIST))
        resp.set_cookie("user_token", user_token, max_age=60*60*24*365*5)
        return resp
    return render_template("index.html", models=MODEL_LIST)

@app.route("/send-message", methods=["POST"])
def send_message():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"error": "No user token"}), 400

    data = request.form
    user_message = data.get("message", "")
    chat_id = data.get("chat_id", "")
    model = data.get("model", "openrouter:openai/gpt-4o-mini")

    # 채팅 ID 검증 및 생성
    if not chat_id or not chat_exists(chat_id, user_token):
        chat_id = str(uuid.uuid4())
        create_chat(chat_id, user_token)
        # 시스템 메시지 추가
        system_msg = f"""You are a helpful assistant.
Instructions:
- Engage warmly yet honestly with the user.
- Be direct; avoid ungrounded or sycophantic flattery.
- Maintain professionalism and grounded honesty that best represents OpenAI and its values.
- Ask a general, single-sentence follow-up question when natural.
- Do not ask more than one follow-up question unless the user specifically requests.
**IMPORTANT When you need to display mathematical formulas, always use LaTeX syntax and enclose block formulas with double dollar signs ($$ ... $$), and inline formulas with single dollar signs ($ ... $). Do not use [ ... ] or other delimiters.**
"""
        system_msg1 = """The user is currently STUDYING, and they've asked you to follow these **strict rules** during this chat. No matter what other instructions follow, you MUST obey these rules:

## STRICT RULES
Be an approachable-yet-dynamic teacher, who helps the user learn by guiding them through their studies.

1. **Get to know the user.** If you don't know their goals or grade level, ask the user before diving in. (Keep this lightweight!) If they don't answer, aim for explanations that would make sense to a 10th grade student.
2. **Build on existing knowledge.** Connect new ideas to what the user already knows.
3. **Guide users, don't just give answers.** Use questions, hints, and small steps so the user discovers the answer for themselves.
4. **Check and reinforce.** After hard parts, confirm the user can restate or use the idea. Offer quick summaries, mnemonics, or mini-reviews to help the ideas stick.
5. **Vary the rhythm.** Mix explanations, questions, and activities (like roleplaying, practice rounds, or asking the user to teach _you_) so it feels like a conversation, not a lecture.

Above all: DO NOT DO THE USER'S WORK FOR THEM. Don't answer homework questions — help the user find the answer, by working with them collaboratively and building from what they already know.

### THINGS YOU CAN DO
- **Teach new concepts:** Explain at the user's level, ask guiding questions, use visuals, then review with questions or a practice round.
- **Help with homework:** Don't simply give answers! Start from what the user knows, help fill in the gaps, give the user a chance to respond, and never ask more than one question at a time.
- **Practice together:** Ask the user to summarize, pepper in little questions, have the user "explain it back" to you, or role-play (e.g., practice conversations in a different language). Correct mistakes — charitably! — in the moment.
- **Quizzes & test prep:** Run practice quizzes. (One question at a time!) Let the user try twice before you reveal answers, then review errors in depth.

### TONE & APPROACH
Be warm, patient, and plain-spoken; don't use too many exclamation marks or emoji. Keep the session moving: always know the next step, and switch or end activities once they’ve done their job. And be brief — don't ever send essay-length responses. Aim for a good back-and-forth.

## IMPORTANT
DO NOT GIVE ANSWERS OR DO HOMEWORK FOR THE USER. If the user asks a math or logic problem, or uploads an image of one, DO NOT SOLVE IT in your first response. Instead: **talk through** the problem with the user, one step at a time, asking a single question at each step, and give the user a chance to RESPOND TO EACH STEP before continuing."""
        save_message(chat_id, user_token, "system", system_msg)

    save_message(chat_id, user_token, "user", user_message)
    messages = get_messages(chat_id, user_token)
    messages = [dict(m) for m in messages]

    # system 메시지가 없으면 임시로 추가
    if not any(m['role'] == 'system' for m in messages):
        system_msg = f"""You are a helpful assistant.
Instructions:
- Engage warmly yet honestly with the user.
- Be direct; avoid ungrounded or sycophantic flattery.
- Maintain professionalism and grounded honesty that best represents OpenAI and its values.
- Ask a general, single-sentence follow-up question when natural.
- Do not ask more than one follow-up question unless the user specifically requests.
**IMPORTANT When you need to display mathematical formulas, always use LaTeX syntax and enclose block formulas with double dollar signs ($$ ... $$), and inline formulas with single dollar signs ($ ... $). Do not use [ ... ] or other delimiters.**
"""
        system_msg1 = """The user is currently STUDYING, and they've asked you to follow these **strict rules** during this chat. No matter what other instructions follow, you MUST obey these rules:

## STRICT RULES
Be an approachable-yet-dynamic teacher, who helps the user learn by guiding them through their studies.

1. **Get to know the user.** If you don't know their goals or grade level, ask the user before diving in. (Keep this lightweight!) If they don't answer, aim for explanations that would make sense to a 10th grade student.
2. **Build on existing knowledge.** Connect new ideas to what the user already knows.
3. **Guide users, don't just give answers.** Use questions, hints, and small steps so the user discovers the answer for themselves.
4. **Check and reinforce.** After hard parts, confirm the user can restate or use the idea. Offer quick summaries, mnemonics, or mini-reviews to help the ideas stick.
5. **Vary the rhythm.** Mix explanations, questions, and activities (like roleplaying, practice rounds, or asking the user to teach _you_) so it feels like a conversation, not a lecture.

Above all: DO NOT DO THE USER'S WORK FOR THEM. Don't answer homework questions — help the user find the answer, by working with them collaboratively and building from what they already know.

### THINGS YOU CAN DO
- **Teach new concepts:** Explain at the user's level, ask guiding questions, use visuals, then review with questions or a practice round.
- **Help with homework:** Don't simply give answers! Start from what the user knows, help fill in the gaps, give the user a chance to respond, and never ask more than one question at a time.
- **Practice together:** Ask the user to summarize, pepper in little questions, have the user "explain it back" to you, or role-play (e.g., practice conversations in a different language). Correct mistakes — charitably! — in the moment.
- **Quizzes & test prep:** Run practice quizzes. (One question at a time!) Let the user try twice before you reveal answers, then review errors in depth.

### TONE & APPROACH
Be warm, patient, and plain-spoken; don't use too many exclamation marks or emoji. Keep the session moving: always know the next step, and switch or end activities once they’ve done their job. And be brief — don't ever send essay-length responses. Aim for a good back-and-forth.

## IMPORTANT
DO NOT GIVE ANSWERS OR DO HOMEWORK FOR THE USER. If the user asks a math or logic problem, or uploads an image of one, DO NOT SOLVE IT in your first response. Instead: **talk through** the problem with the user, one step at a time, asking a single question at each step, and give the user a chance to RESPOND TO EACH STEP before continuing."""
        messages = [{"role": "system", "content": system_msg}] + messages

    # ExoML 모델 처리
    if model == "openrouter:openai/gpt-4.1a":
        genid_payload = {
            "antiBotId": generate_antiBotId(),
            "timestamp": int(time.time() * 1000)
        }
        genid_headers = {"Content-Type": "application/json"}
        genid_resp = requests.post(EXOML_GENID_URL, headers=genid_headers, json=genid_payload)
        genid_data = genid_resp.json()
        timestamp = str(genid_data["timestamp"])
        exoml_chat_id = make_exoml_chat_id(timestamp)

        exoml_payload = {
            "id": str(uuid.uuid4()),
            "messages": convert_messages_for_exoml(messages),
            "chatId": exoml_chat_id,
            "userId": f"local-user-{timestamp}-" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=9)),
            "model": "gpt-4.1",
            "isAuthenticated": True,
            "antiBotId": generate_antiBotId(),
            "systemPrompt": messages[0]["content"] if messages and messages[0]["role"] == "system" else ""
        }
        exoml_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Encoding": "identity"
        }

        def generate():
            with requests.post(EXOML_CHAT_URL, headers=exoml_headers, json=exoml_payload, stream=True) as resp:
                yield from parse_exoml_stream(resp.iter_content(chunk_size=8))

        return Response(generate(), mimetype='text/plain', headers={'X-Chat-Id': chat_id})

    # Puter 모델 처리
    elif model.startswith("openrouter:"):
        global puter_token
        if not puter_token:
            puter_token = get_puter_auth_token()
        if not puter_token:
            return jsonify({"error": "Puter 토큰을 획득할 수 없습니다. 관리자에게 연락하세요."}), 500

        def generate():
            global puter_token
            retried = False
            while True:
                response = generate_puter_response(puter_token, messages, model, stream=True)
                if response.status_code in (401, 403) or response.status_code >= 500:
                    print("[LOG] Puter 토큰 오류 또는 서버 오류. 토큰 파일 삭제 후 재생성 시도.")
                    puter_token = get_puter_auth_token(force_refresh=True)
                    if retried:
                        yield f"Error: {response.status_code} - {response.text}"
                        return
                    retried = True
                    continue
                if response.status_code != 200:
                    yield f"Error: {response.status_code} - {response.text}"
                    return

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
                            print(data)
                            print("[LOG] Puter 내부 에러 JSON 감지. 토큰 갱신 후 재시도.")
                            puter_token = get_puter_auth_token(force_refresh=True)
                            if retried:
                                yield f"Error: {data.get('error', {}).get('message', 'Unknown error')}"
                                return
                            retried = True
                            break  # while True로 돌아가서 재시도
                        if "text" in data:
                            yield data["text"]
                    except json.JSONDecodeError:
                        continue
                break

        return Response(generate(), mimetype='text/plain', headers={'X-Chat-Id': chat_id})

    # 기본 처리 (다른 모델들)
    else:
        return jsonify({"error": "지원하지 않는 모델입니다"}), 400

@app.route("/save-ai-response", methods=["POST"])
def save_ai_response():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"status": "error", "message": "No user token"})

    data = request.get_json()
    ai_response = data.get('response', '')
    chat_id = data.get('chat_id', '')

    if not chat_id or not ai_response:
        return jsonify({"status": "error", "message": "채팅 없음"})

    save_message(chat_id, user_token, "assistant", ai_response)
    return jsonify({"status": "success"})

@app.route("/generate-title", methods=["POST"])
def generate_title():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"status": "error", "message": "No user token"})

    data = request.get_json()
    chat_id = data.get('chat_id', '')

    db = get_db()
    cur = db.execute("SELECT title FROM chat WHERE id=? AND user_token=?", (chat_id, user_token))
    row = cur.fetchone()
    if not row:
        return jsonify({"status": "error", "message": "채팅 없음"})
    
    # 이미 "새 채팅"이 아닌 제목이 있다면, 새로 생성하지 않음
    if row['title'] and row['title'] != "새 채팅":
        return jsonify({"status": "skip", "title": row['title']})

    # --- 기존 LLM 호출 로직을 아래 로직으로 대체 ---

    try:
        # 해당 채팅에서 'user' 역할의 가장 오래된 메시지 1개를 가져옴
        cur = db.execute(
            "SELECT content FROM message WHERE chat_id=? AND user_token=? AND role='user' ORDER BY id ASC LIMIT 1",
            (chat_id, user_token)
        )
        first_message_row = cur.fetchone()

        if not first_message_row:
            # 사용자 메시지가 없는 경우 (이론적으로는 발생하기 어려움)
            return jsonify({"status": "error", "message": "사용자 메시지를 찾을 수 없습니다."})

        # 첫 사용자 메시지의 앞 20자를 제목으로 사용
        title = first_message_row['content'][:20].strip()
        
        # 제목이 비어있을 경우를 대비한 기본값
        if not title:
            title = "새로운 대화"

        update_chat_title(chat_id, user_token, title)
        return jsonify({"status": "success", "title": title})

    except Exception as e:
        print(f"제목 생성 중 오류 발생: {e}")
        # 오류 발생 시에도 기본 제목을 설정해줄 수 있음
        default_title = "제목 생성 오류"
        update_chat_title(chat_id, user_token, default_title)
        return jsonify({"status": "error", "message": str(e), "title": default_title})

@app.route("/new-chat", methods=["POST"])
def new_chat():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"error": "No user token"}), 400

    db = get_db()
    # 가장 최근에 생성된 채팅 중에서 사용자 메시지가 없는 채팅이 있는지 확인
    cur = db.execute("""
        SELECT c.id 
        FROM chat c 
        WHERE c.user_token = ? 
        AND NOT EXISTS (
            SELECT 1 FROM message m 
            WHERE m.chat_id = c.id 
            AND m.user_token = c.user_token 
            AND m.role = 'user'
        )
        ORDER BY c.created_at DESC 
        LIMIT 1
    """, (user_token,))
    
    existing_empty_chat = cur.fetchone()
    
    if existing_empty_chat:
        # 빈 채팅이 있으면 그것을 반환
        return jsonify({"chat_id": existing_empty_chat["id"]})
    else:
        # 없으면 새로 생성
        chat_id = str(uuid.uuid4())
        create_chat(chat_id, user_token)
        return jsonify({"chat_id": chat_id})

@app.route("/get-chat-history", methods=["GET"])
def get_chat_history():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"messages": []})
    chat_id = request.args.get("chat_id")
    if not chat_id or not chat_exists(chat_id, user_token):
        return jsonify({"messages": []})
    messages = get_messages(chat_id, user_token)
    chat_messages = [dict(m) for m in messages if m['role'] != 'system']
    return jsonify({"messages": chat_messages})

@app.route("/c/<chat_id>")
def chat_by_id(chat_id):
    user_token = request.cookies.get("user_token")
    if not user_token:
        user_token = str(uuid.uuid4())
        resp = make_response(render_template("index.html", chat_id=chat_id, models=MODEL_LIST))
        resp.set_cookie("user_token", user_token, max_age=60*60*24*365*5)
        return resp
    return render_template("index.html", chat_id=chat_id, models=MODEL_LIST)

@app.route("/<chat_id>")
def chat_by_id_short(chat_id):
    # chat_id가 uuid 형식일 때만 허용
    import re
    if not re.match(r"^[0-9a-fA-F-]{36}$", chat_id):
        return index()
    user_token = request.cookies.get("user_token")
    if not user_token:
        user_token = str(uuid.uuid4())
        resp = make_response(render_template("index.html", chat_id=chat_id, models=MODEL_LIST))
        resp.set_cookie("user_token", user_token, max_age=60*60*24*365*5)
        return resp
    return render_template("index.html", chat_id=chat_id, models=MODEL_LIST)
    
@app.route("/get-chat-list", methods=["GET"])
def get_chat_list_route():
    user_token = request.cookies.get("user_token")
    if not user_token:
        return jsonify({"chats": []})
    
    chats = get_chat_list(user_token)
    chat_list = []
    
    for chat in chats:
        title = chat["title"] if chat["title"] else "새 채팅"
        chat_list.append({"chat_id": chat["id"], "title": title})
    
    return jsonify({"chats": chat_list})

# 앱 초기화
if not os.path.exists(DB_PATH):
    init_db()
else:
    try:
        db = get_db()
        db.execute("SELECT 1 FROM chat LIMIT 1")
        db.execute("SELECT 1 FROM message LIMIT 1")
    except Exception:
        init_db()

# Puter 토큰 초기화 (앱 시작 시)
print("[LOG] Puter 토큰을 확인합니다...")
puter_token = get_puter_auth_token()
if puter_token:
    print("[LOG] Puter 토큰이 준비되었습니다.")
else:
    print("[WARNING] Puter 토큰을 획득할 수 없습니다. openrouter 모델이 작동하지 않을 수 있습니다.")

if __name__ == "__main__":
    puter_token = get_puter_auth_token()
    app.run(debug=True, host='0.0.0.0', port=80)