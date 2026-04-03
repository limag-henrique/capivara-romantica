import requests

# 1. Configurações da Evolution API
base_url = "https://evolution-api-production-06d2.up.railway.app"
chave_api = "d130312bf254cdbbea92b783844c5d9d473f7dd87d358163299b4f4e1da0725b"
instance_name = "capivara"

# 2. O link do seu bot no Render (com o /webhook no final)
url_do_seu_bot = "https://capivara-romantica.onrender.com/webhook"

url_webhook = f"{base_url}/webhook/set/{instance_name}"

headers = {
    "apikey": chave_api,
    "Content-Type": "application/json"
}

# 3. Avisando a Evolution para mandar as mensagens para o Render
payload = {
    "webhook": {
        "enabled": True,
        "url": url_do_seu_bot,
        "byEvents": False,
        "base64": False,
        "events": [
            "MESSAGES_UPSERT" # Gatilho: só avisa quando chegar mensagem nova
        ]
    }
}

print("Conectando o WhatsApp ao Render...")
response = requests.post(url_webhook, json=payload, headers=headers)

# 4. Resultado
if response.status_code == 200:
    print("✅ SUCESSO! A ponte foi estabelecida.")
    print("A Evolution API agora enviará todas as mensagens para:", url_do_seu_bot)
else:
    print("❌ Erro ao ligar o webhook:")
    print(response.text)