import os
import requests
import asyncio # <-- NOVO IMPORT NECESSÁRIO AQUI
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
# 🧠 O CÉREBRO: Dicionário para guardar a memória
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

    # 1. Atualiza histórico da pessoa
    if number not in historico_conversas:
        historico_conversas[number] = [{"role": "system", "content": SYSTEM_PROMPT}]

    historico_conversas[number].append({"role": "user", "content": text_content})

    if len(historico_conversas[number]) > 11:
        historico_conversas[number] = [historico_conversas[number][0]] + historico_conversas[number][-10:]

    try:
        # 2. Pede a resposta para a OpenAI PRIMEIRO (para sabermos o tamanho do texto)
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_ID,
            messages=historico_conversas[number],
            temperature=0.7,
            frequency_penalty=1.0,
            presence_penalty=0.6
        )
        
        reply_text = response.choices[0].message.content
        reply_text = "\n".join([line.rstrip('. ') for line in reply_text.split('\n')])

        # ==========================================
        # ⏳ LÓGICA DE TEMPO DE DIGITAÇÃO REALISTA
        # ==========================================
        # Calcula o tempo: 1 segundo base de "pensar" + 60 milissegundos por cada letra
        tempo_digitando_ms = 1000 + (len(reply_text) * 60)

        # Trava de segurança: Se a mensagem for gigante, não digita por mais de 8 segundos 
        # (Para a pessoa do outro lado não achar que o WhatsApp travou)
        if tempo_digitando_ms > 8000:
            tempo_digitando_ms = 8000

        # 3. Avisa a Evolution API para mostrar o status "Digitando..." lá no app
        presence_url = f"{EVOLUTION_API_URL}/chat/sendPresence/{INSTANCE_NAME}"
        try:
            requests.post(
                presence_url, 
                json={"number": number, "presence": "composing", "delay": tempo_digitando_ms},
                headers=HEADERS,
                timeout=5
            )
        except Exception as e:
            pass

        # 4. Faz o seu servidor "dormir" de verdade por esse tempo (converte ms para segundos)
        await asyncio.sleep(tempo_digitando_ms / 1000.0)

        # 5. Salva a resposta no histórico e finalmente envia a mensagem
        historico_conversas[number].append({"role": "assistant", "content": reply_text})

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