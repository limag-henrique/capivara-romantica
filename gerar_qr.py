import requests
import base64

# 1. Configurações (Mantenha sua URL e Chave da Railway)
base_url = "https://evolution-api-production-06d2.up.railway.app"
instance_name = "capivara"
chave_api = "d130312bf254cdbbea92b783844c5d9d473f7dd87d358163299b4f4e1da0725b"

# 2. Rota de Conexão (Diferente da rota de criação)
url_connect = f"{base_url}/instance/connect/{instance_name}"

headers = {
    "apikey": chave_api,
    "Content-Type": "application/json"
}

print(f"Solicitando reconexão para a instância: {instance_name}...")

try:
    # Para conectar, usamos o método GET na Evolution API
    response = requests.get(url_connect, headers=headers)
    data = response.json()

    # 3. Lógica de salvamento da imagem
    if isinstance(data, dict) and "base64" in data:
        print("\n✅ QR Code gerado com sucesso!")
        
        # Extrai e decodifica a imagem
        b64_string = data["base64"].split(",")[1]
        with open("meu_qr_code.png", "wb") as f:
            f.write(base64.b64decode(b64_string))
            
        print("🚀 Pronto! Abra 'meu_qr_code.png' e escaneie com o WhatsApp Business.")
    
    elif isinstance(data, dict) and data.get("status") == "CONNECTED":
        print("\n✨ Você já está conectado! Não é necessário escanear novamente.")
    
    else:
        print("\n❌ Não foi possível obter o QR Code. Resposta:")
        print(data)

except Exception as e:
    print(f"\nErro na requisição: {e}")