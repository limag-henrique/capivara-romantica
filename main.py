import os
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from openai import AsyncOpenAI
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI(title="Capivara Romantica Webhook")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-3.5-turbo") 

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME", "MinhaInstancia")

HEADERS = {
    "apikey": EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

# ==========================================
# 🧠 O CÉREBRO: Dicionário para guardar a memória das conversas
# ==========================================
historico_conversas = {}

async def process_webhook_event(payload: dict):
    event_type = payload.get("event", "")
    if event_type != "messages.upsert":
        return

    data = payload.get("data", {})
    key = data.get("key", {})
    message = data.get("message", {})

    if key.get("fromMe", False):
        return

    remote_jid = key.get("remoteJid", "")
    if "@g.us" in remote_jid:
        return

    number = remote_jid.split("@")[0]

    text_content = ""
    if "conversation" in message:
        text_content = message["conversation"]
    elif "extendedTextMessage" in message:
        text_content = message["extendedTextMessage"].get("text", "")
    
    if not text_content:
        return

    # Simulate Typing Delay
    presence_url = f"{EVOLUTION_API_URL}/chat/sendPresence/{INSTANCE_NAME}"
    try:
        requests.post(
            presence_url, 
            json={"number": number, "presence": "composing", "delay": 2000},
            headers=HEADERS,
            timeout=5
        )
    except Exception as e:
        pass

    # ==========================================
    # LÓGICA DE MEMÓRIA APLICADA AQUI
    # ==========================================
    
    # 1. Se é a primeira vez que a pessoa manda mensagem, cria a lista dela com o System Prompt
    if number not in historico_conversas:
        historico_conversas[number] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # 2. Adiciona a mensagem que o usuário acabou de mandar no histórico
    historico_conversas[number].append({"role": "user", "content": text_content})

    # 3. Limite de memória: Mantém o System Prompt (índice 0) e as últimas 10 mensagens
    # Isso evita gastar todos os seus tokens da OpenAI se a pessoa conversar por 3 horas seguidas
    if len(historico_conversas[number]) > 11:
        historico_conversas[number] = [historico_conversas[number][0]] + historico_conversas[number][-10:]

    try:
        # 4. Envia o HISTÓRICO INTEIRO para a OpenAI, não apenas a última mensagem
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_ID,
            messages=historico_conversas[number],
            temperature=0.85 # Aumentei um pouquinho para ela ser mais criativa nas perguntas aleatórias
        )
        
        reply_text = response.choices[0].message.content
        reply_text = "\n".join([line.rstrip('. ') for line in reply_text.split('\n')])

        # 5. Salva a resposta da Capivara no histórico para ela lembrar do que ELA MESMA disse
        historico_conversas[number].append({"role": "assistant", "content": reply_text})

        # Enviar resposta via Evolution
        send_message_url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
        requests.post(
            send_message_url,
            json={"number": number, "text": reply_text},
            headers=HEADERS,
            timeout=10
        )
        
    except Exception as e:
        print(f"[-] Erro na API: {e}")

@app.post("/webhook")
async def webhook_evolution(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        background_tasks.add_task(process_webhook_event, payload)
        return {"status": "ok", "message": "Event processed in background"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}