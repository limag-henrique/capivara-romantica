import os
import time
import re
import requests
import asyncio
from fastapi import FastAPI, Request, BackgroundTasks
from openai import AsyncOpenAI
from dotenv import load_dotenv

from prompts import SYSTEM_PROMPT

load_dotenv()

app = FastAPI(title="Capivara Romantica Webhook")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL_ID = os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini")

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://localhost:8080")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME", "MinhaInstancia")

HEADERS = {
    "apikey": EVOLUTION_API_KEY,
    "Content-Type": "application/json"
}

historico_conversas = {}
last_activity = {}  # Rastreia o tempo do último contato de cada número
numeros_em_processamento = set()

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

    # Atualiza o timestamp de atividade do usuário
    current_time = time.time()
    last_activity[number] = current_time

    # Rotina Ninja de Limpeza (evita Memory Leak no Render)
    # Remove qualquer pessoa inativa há mais de 2 horas (7200 segundos)
    numeros_inativos = [num for num, timestamp in last_activity.items() if current_time - timestamp > 7200]
    for num in numeros_inativos:
        historico_conversas.pop(num, None)
        last_activity.pop(num, None)
        numeros_em_processamento.discard(num)

    text_content = ""
    if "conversation" in message:
        text_content = message["conversation"]
    elif "extendedTextMessage" in message:
        text_content = message["extendedTextMessage"].get("text", "")
    elif "audioMessage" in message:
        text_content = "*[Usuário enviou um áudio]*"
    elif "imageMessage" in message:
        text_content = "*[Usuário enviou uma imagem]*"
    
    if not text_content:
        return

    # Garante que o histórico existe
    if number not in historico_conversas:
        historico_conversas[number] = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Se já existe uma resposta a ser gerada, apenas adiciona a nova mensagem ao histórico e encerra.
    # A task que está a dormir vai ler esta mensagem nova quando acordar!
    if number in numeros_em_processamento:
        historico_conversas[number].append({"role": "user", "content": text_content})
        return

    # Se não está em processamento, bloqueia o número e assume a liderança
    numeros_em_processamento.add(number)

    try:
        if "audioMessage" in message or "imageMessage" in message:
            reply_media = "pô véi, tô no meio da aula (ou no bandejão) e a internet tá um lixo, não consigo abrir mídia agora kkkk escreve aí o que foi"
            requests.post(
                f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}",
                json={"number": number, "text": reply_media},
                headers=HEADERS
            )
            return

        # Adiciona a primeira mensagem
        historico_conversas[number].append({"role": "user", "content": text_content})

        # Dorme 3 segundos para acumular mensagens rápidas que o utilizador envie de rajada
        await asyncio.sleep(3)

        if len(historico_conversas[number]) > 41:
            historico_conversas[number] = [historico_conversas[number][0]] + historico_conversas[number][-40:]

        # RASCUNHO (Sua chamada da API original se mantém)
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_ID,
            messages=historico_conversas[number],
            temperature=0.4,       # Reduzido de 0.8 (deixa as respostas mais realistas e pé no chão)
            frequency_penalty=0.0, # Zerado (evita que ele fique buscando palavras raras)
            presence_penalty=0.1   # Reduzido de 0.6 (evita que ele force novos tópicos aleatórios)
        )
        
        draft_reply = response.choices[0].message.content

        # AUDITOR NATIVO (Substituindo o gpt-4o-mini por código puro, agora com Regex)
        # 1. Remove aspas normais e curvas
        final_reply = re.sub(r'["“”]', '', draft_reply)
        
        # 2. Limpeza de markdown, bullets e formatação
        linhas = final_reply.split('\n')
        linhas_limpas = []
        for linha in linhas:
            # Remove marcadores de lista (*, -, +) e espaços vazios no ínicio/fim da linha
            linha_limpa = re.sub(r'^[\-\+\*\s]+', '', linha.strip())
            
            # Remove qualquer ponto final que fique grudado no fim da frase.
            linha_limpa = re.sub(r'\.+$', '', linha_limpa)
                
            if linha_limpa:
                linhas_limpas.append(linha_limpa)
                
        # Salva a mensagem completa (unida por \n) no histórico de conversas para a IA lembrar do contexto
        final_reply = "\n".join(linhas_limpas)
        historico_conversas[number].append({"role": "assistant", "content": final_reply})

        # Agora, envia CADA LINHA como uma mensagem SEPARADA no WhatsApp (simulando rajada de mensagens)
        for balao in linhas_limpas:
            # TEMPO DE DIGITAÇÃO POR BALÃO (mais rápido por serem mensagens curtas)
            tempo_digitando_ms = 1500 + (len(balao) * 50) 
            if tempo_digitando_ms > 12000:
                tempo_digitando_ms = 12000

            presence_url = f"{EVOLUTION_API_URL}/chat/sendPresence/{INSTANCE_NAME}"
            try:
                requests.post(
                    presence_url, 
                    json={"number": number, "presence": "composing", "delay": tempo_digitando_ms},
                    headers=HEADERS,
                    timeout=5
                )
            except Exception:
                pass

            await asyncio.sleep(tempo_digitando_ms / 1000.0)

            send_message_url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
            try:
                requests.post(
                    send_message_url,
                    json={"number": number, "text": balao},
                    headers=HEADERS,
                    timeout=10
                )
            except Exception:
                pass
        
    except Exception as e:
        print(f"[-] Erro na API interna: {e}")
    finally:
        # Liberta o bloqueio para a próxima interação
        numeros_em_processamento.discard(number)

@app.post("/webhook")
async def webhook_evolution(request: Request, background_tasks: BackgroundTasks):
    try:
        payload = await request.json()
        background_tasks.add_task(process_webhook_event, payload)
        return {"status": "ok", "message": "Processado"}
    except Exception as e:
        print(f"[-] Erro fatal no Webhook: {e}")