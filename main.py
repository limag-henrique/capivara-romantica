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

    # 4. Extraindo conteúdo de texto e lidando com Mídias
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

    # Trava extra: Se for mídia, a Capivara dá uma desculpa e nem gasta token com a OpenAI
    if "audioMessage" in message or "imageMessage" in message:
        reply_media = "Pô véi, tô no meio da aula de Cálculo (ou no bandejão) e a internet tá um lixo, não consigo abrir mídia/áudio agora kkkk escreve aí o que foi"
        requests.post(
            f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}",
            json={"number": number, "text": reply_media},
            headers=HEADERS
        )
        return

    # 1. Atualiza histórico da pessoa
    if number not in historico_conversas:
        historico_conversas[number] = [{"role": "system", "content": SYSTEM_PROMPT}]

    historico_conversas[number].append({"role": "user", "content": text_content})

    if len(historico_conversas[number]) > 11:
        historico_conversas[number] = [historico_conversas[number][0]] + historico_conversas[number][-10:]

    try:
        # 1. RASCUNHO: Pede a resposta para a Capivara
        response = await client.chat.completions.create(
            model=OPENAI_MODEL_ID,
            messages=historico_conversas[number],
            temperature=0.7,
            frequency_penalty=0.1,
            presence_penalty=0.6
        )
        
        draft_reply = response.choices[0].message.content

        # ==========================================
        # 🛡️ O AUDITOR (GUARDRAIL DE AUTO-CORREÇÃO)
        # ==========================================
        prompt_auditor = f"""Você é o Revisor de Segurança da Capivara Romântica. 
        Leia este rascunho de mensagem: "{draft_reply}"
        
        Sua tarefa é REESCREVER a mensagem se ela quebrar QUALQUER uma destas regras:
        1. VAZAMENTO: Se a mensagem contiver o nome 'Henrique', apague e substitua por 'Capivara'.
        2. ALUCINAÇÃO ACADÊMICA: Se a mensagem falar sobre "processo seletivo literal", "grupo de pesquisa", "taxas", ou agir como se o cartaz fosse algo científico, REESCREVA transformando num flerte debochado de um universitário liso.
        3. PONTO FINAL: Remova QUALQUER ponto final (.) que esteja no final da mensagem.
        4. MONOSSÍLABOS: Se a resposta for só "Sim", "Kkkk" ou "Entendi", adicione uma pergunta provocativa no final.
        
        Se o rascunho estiver perfeito e seguir o flerte, devolva-o EXATAMENTE igual, sem ponto final. 
        Retorne APENAS a mensagem final, sem explicações."""

        # 2. VALIDAÇÃO: Passa o rascunho pelo Auditor
        eval_response = await client.chat.completions.create(
            model="gpt-4o-mini", # O auditor pode usar o modelo base barato
            messages=[{"role": "system", "content": prompt_auditor}],
            temperature=0.0 # Temperatura zero para ele ser estrito e focado
        )
        
        final_reply = eval_response.choices[0].message.content
        final_reply = "\n".join([line.rstrip('. ') for line in final_reply.split('\n')])

        # ==========================================
        # ⏳ LÓGICA DE TEMPO DE DIGITAÇÃO
        # ==========================================
        tempo_digitando_ms = 1000 + (len(final_reply) * 50)
        if tempo_digitando_ms > 8000:
            tempo_digitando_ms = 8000

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

        await asyncio.sleep(tempo_digitando_ms / 1000.0)

        # 3. Salva a resposta final e envia
        historico_conversas[number].append({"role": "assistant", "content": final_reply})

        send_message_url = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
        requests.post(
            send_message_url,
            json={"number": number, "text": final_reply},
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
        print(f"[-] Erro na API (OpenAI ou Evolution): {e}")
        # Se a IA falhar ou o servidor travar, a Capivara dá uma desculpa técnica
        msg_erro = "A internet aqui no ICEx caiu bem na hora que eu ia responder, a rede da UFMG tá intankável hoje kkkk manda de novo?"
        requests.post(
            f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}",
            json={"number": number, "text": msg_erro},
            headers=HEADERS,
            timeout=5
        )