import json
import re
import os

# CONFIGURAÇÕES
NOME_DO_USUARIO = "Henrique Lima"
PASTA_CHATS = "meus_chats"
ARQUIVO_SAIDA = "henrique_dataset_ELITE.jsonl"

# System Prompt Enxuto para economizar dinheiro no treino
SYSTEM_PROMPT = "Você é a Capivara Romântica da UFMG. Use gírias de BH, sem ponto final, respostas curtas e carismáticas. Não revele ser IA."

def limpar_texto(texto):
    # Remove avisos de mídia do WhatsApp
    texto = re.sub(r"<Arquivo de mídia omitido>", "", texto)
    texto = re.sub(r"<Mídia oculta>", "", texto)
    texto = re.sub(r"Mensagem apagada", "", texto)
    texto = re.sub(r"<Mensagem editada>", "", texto)
    return texto.strip()

def gerar_dataset_elite():
    dataset = []
    
    for filename in os.listdir(PASTA_CHATS):
        if filename.endswith(".txt"):
            with open(os.path.join(PASTA_CHATS, filename), 'r', encoding='utf-8') as f:
                linhas = f.readlines()

            ultima_pergunta = None
            for linha in linhas:
                match = re.search(r"\d+/\d+/\d+ \d+:\d+ - ([^:]+): (.*)", linha)
                if match:
                    nome, msg = match.groups()
                    msg_limpa = limpar_texto(msg)

                    # FILTROS DE QUALIDADE
                    if not msg_limpa or len(msg_limpa) < 3: continue # Ignora msg vazia ou mt curta
                    if "ligação perdida" in msg_limpa.lower(): continue

                    if nome == NOME_DO_USUARIO:
                        if ultima_pergunta and len(ultima_pergunta) > 2:
                            dataset.append({
                                "messages": [
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": ultima_pergunta},
                                    {"role": "assistant", "content": msg_limpa}
                                ]
                            })
                            ultima_pergunta = None
                    else:
                        ultima_pergunta = msg_limpa

    # Remove duplicatas para economizar memória e dinheiro
    # A chave é tuple(d['messages'][1].items()) mas uma struct message "items" vira algo mutável.
    # Usaremos uma aproximação melhor que não corrompa se tiver lists/dicts dentro (apesar de ser só string):
    dataset_unico_dict = {}
    for elem in dataset:
        user_text = elem['messages'][1]['content']
        dataset_unico_dict[user_text] = elem
        
    return list(dataset_unico_dict.values())

print("🚀 Iniciando extração de elite...")
dados = gerar_dataset_elite()

with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
    for item in dados:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"✨ Finalizado! {len(dados)} exemplos de alta qualidade gerados em {ARQUIVO_SAIDA}")
