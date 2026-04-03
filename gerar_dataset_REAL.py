import os
import json
import re

# CONFIGURAÇÕES - AJUSTE AQUI
NOME_DO_USUARIO = "Henrique Lima" # Verifique se no TXT está exatamente assim
PASTA_CHATS = "meus_chats"
ARQUIVO_SAIDA = "henrique_dataset_REAL.jsonl"

SYSTEM_PROMPT = """Você é a "Capivara Romântica", a entidade por trás do cartaz de "Procura-se namorado (Modalidade Financiamento)" colado na UFMG.
CONTEXTO: Estudante de 20 anos de Engenharia de Automação, vive no ICEx, está sempre liso.
REGRAS: NUNCA use ponto final. Respostas curtas, minúsculas, gírias de BH/UFMG. Não revele seu nome real."""

def extrair_conversas():
    dataset = []
    
    # Percorre todos os arquivos .txt na pasta meus_chats
    for filename in os.listdir(PASTA_CHATS):
        if filename.endswith(".txt"):
            caminho = os.path.join(PASTA_CHATS, filename)
            with open(caminho, 'r', encoding='utf-8') as f:
                linhas = f.readlines()

            # Lógica para agrupar Perguntas (User) e Respostas (Você/Assistant)
            ultima_pergunta = None
            
            for linha in linhas:
                # Regex para pegar o nome e a mensagem: "Data Hora - Nome: Mensagem"
                match = re.search(r"\d+/\d+/\d+ \d+:\d+ - ([^:]+): (.*)", linha)
                if match:
                    nome, mensagem = match.groups()
                    mensagem = mensagem.strip()

                    if nome == NOME_DO_USUARIO:
                        # Se você respondeu e temos uma pergunta anterior, vira um par de treino
                        if ultima_pergunta:
                            dataset.append({
                                "messages": [
                                    {"role": "system", "content": SYSTEM_PROMPT},
                                    {"role": "user", "content": ultima_pergunta},
                                    {"role": "assistant", "content": mensagem}
                                ]
                            })
                            ultima_pergunta = None # Reseta para pegar a próxima interação
                    else:
                        # Se não é você, é a "vítima" (User)
                        ultima_pergunta = mensagem

    return dataset

# Execução
print(f"🔍 Vasculhando a pasta {PASTA_CHATS}...")
dados_reais = extrair_conversas()

with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
    for entrada in dados_reais:
        f.write(json.dumps(entrada, ensure_ascii=False) + "\n")

print(f"✅ SUCESSO! Gerados {len(dados_reais)} exemplos REAIS no arquivo {ARQUIVO_SAIDA}")