import os
import requests
from fastapi import FastAPI, Request, BackgroundTasks
from openai import AsyncOpenAI
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI(title="Capivara Romantica Webhook")

# --- Configurações da OpenAI ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Aqui você vai usar o ID do modelo gerado pelo Fine-Tuning. Ex: ft:gpt-3.5-turbo-0125:sua-org:seu-modelo
OPENAI_MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-3.5-turbo") 

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- Configurações da Evolution API ---
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME", "MinhaInstancia")

# Headers padrão para requisições de envio na Evolution API
HEADERS = {
    "apikey": EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

async def process_webhook_event(payload: dict):
    """
    Processa a mensagem em background para não travar o retorno 200 pro Webhook
    """
    event_type = payload.get("event", "")
    if event_type != "messages.upsert":
        return

    data = payload.get("data", {})
    key = data.get("key", {})
    message = data.get("message", {})

    # 1. Filtro Crítico: Ignorar mensagens enviadas por nós mesmos
    if key.get("fromMe", False):
        return

    remote_jid = key.get("remoteJid", "")
    
    # 2. Filtro Crítico: Ignorar grupos
    # Em APIs do WhatsApp (Baileys/Evolution), grupos terminam com @g.us
    if "@g.us" in remote_jid:
        return

    # Pode ser verificado também através de pushName se é um contato conhecido (dependendo se a Evolution manda essa flag via contato salvo)
    # Por ora, a ausência de '@g.us' já confirma isGroup=False. E assumimos que a AI vai lidar com esses contatos 1 a 1.
    
    # 3. Tratando o número de telefone
    number = remote_jid.split("@")[0]

    # 4. Extraindo conteúdo de texto
    text_content = ""
    if "conversation" in message:
        text_content = message["conversation"]
    elif "extendedTextMessage" in message:
        text_content = message["extendedTextMessage"].get("text", "")
    
    if not text_content:
        return

    # 5. Simulate Typing Delay (Send Presence)
    presence_url = f"{EVOLUTION_API_URL}/chat/sendPresence/{INSTANCE_NAME}"
    try:
        # Mostra 'digitando' pro usuário enxergar do lado de lá
        requests.post(
            presence_url, 
            json={"number": number, "presence": "composing", "delay": 2000},
            headers=HEADERS,
            timeout=5
        )
    except Exception as e:
        print(f"[-] Erro ao enviar sendPresence: {e}")

    # 6. Realizar a chamada para o Fine-Tuning da OpenAI
    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_ID,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text_content}
            ],
            temperature=0.7
        )
        
        reply_text = response.choices[0].message.content

        # Para garantir que não existirá nenhum ponto final solto devido ao modelo as vezes insistir
        reply_text = "\n".join([line.rstrip('. ') for line in reply_text.split('\n')])

        # 7. Enviar resposta usando a Evolution
        send_message_url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
        requests.post(
            send_message_url,
            json={
                "number": number, 
                "text": reply_text
            },
            headers=HEADERS,
            timeout=10
        )
        print(f"[+] Resposta enviada com sucesso para {number}!")
        
    except Exception as e:
        print(f"[-] Erro ao se comunicar com a OpenAI ou Evolution: {e}")

@app.post("/webhook")
async def webhook_evolution(request: Request, background_tasks: BackgroundTasks):
    """
    Endpoint principal para receber os eventos do WhatsApp
    """
    try:
        payload = await request.json()
        background_tasks.add_task(process_webhook_event, payload)
        
        # O webhook exige o retorno rápido de {'status': 'ok'} (ou parecido) e código 200 pra n acumular retry
        return {"status": "ok", "message": "Event processed in background"}
    except Exception as e:
        return {"status": "error", "reason": str(e)}

# Para rodar de forma automática, depois crie um arquivo .env e então execute:
# uvicorn main:app --reload
