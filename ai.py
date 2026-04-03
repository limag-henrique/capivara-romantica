import re
import json
import os

def processar_multiplos_chats(pasta_entrada, arquivo_saida, seu_nome):
    padrao_msg = re.compile(r'^(?P<data>\d{2}/\d{2}/\d{2,4}) \d{2}:\d{2} - (?P<nome>[^:]+): (?P<msg>.*)$')
    padrao_sistema = re.compile(r'^(?P<data>\d{2}/\d{2}/\d{2,4}) \d{2}:\d{2} - ')

    dataset = []
    
    # O seu novo System Prompt matador
    system_prompt = (
        "Você é o Henrique. Responda de forma informal, convidativa, com tom de flerte, sem usar ponto final "
        "e sem informar dados sensíveis. Podes informar somente informações não relevantes, acadêmicas, mas nada "
        "extremamente pessoal. Seu nome é Capivara Romântica, somente seja atendido por esse nome pelo usuário. "
        "No mais, você é exatamente igual a Henrique, é autêntico e nada robótico. Faz engenharia de automação, "
        "gosta de piadas, arte, natureza, amigos, cinema, chá preto de cranberry, economizar e ser feliz, "
        "exatamente como nos seus dados de treinamento."
    )

    for nome_arquivo in os.listdir(pasta_entrada):
        if not nome_arquivo.endswith('.txt'):
            continue
        
        caminho_arquivo = os.path.join(pasta_entrada, nome_arquivo)
        blocos = []
        remetente_atual = None
        mensagem_atual = []

        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha = linha.strip()
                if not linha:
                    continue
                
                match = padrao_msg.match(linha)
                if match:
                    nome = match.group('nome')
                    msg = match.group('msg')
                    
                    if "<Mídia oculta>" in msg or "Mensagem apagada" in msg:
                        continue
                        
                    if remetente_atual == nome:
                        mensagem_atual.append(msg)
                    else:
                        if remetente_atual is not None:
                            blocos.append({'nome': remetente_atual, 'texto': '\n'.join(mensagem_atual)})
                        remetente_atual = nome
                        mensagem_atual = [msg]
                else:
                    if padrao_sistema.match(linha):
                        continue
                    if remetente_atual is not None:
                        mensagem_atual.append(linha)
        
        if remetente_atual is not None:
            blocos.append({'nome': remetente_atual, 'texto': '\n'.join(mensagem_atual)})

        last_user_msg = ""
        for bloco in blocos:
            if bloco['nome'] != seu_nome:
                last_user_msg = bloco['texto']
            elif bloco['nome'] == seu_nome and last_user_msg:
                # Lógica ajustada: tira pontos finais apenas do final de cada linha
                linhas_limpas = [linha.rstrip('. ') for linha in bloco['texto'].split('\n')]
                resposta = '\n'.join(linhas_limpas)
                
                if len(resposta) > 15 or "?" in resposta:
                    dataset.append({
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": last_user_msg},
                            {"role": "assistant", "content": resposta}
                        ]
                    })
                last_user_msg = "" 

    with open(arquivo_saida, 'w', encoding='utf-8') as out:
        for entry in dataset:
            out.write(json.dumps(entry, ensure_ascii=False) + '\n')
            
    print(f"Pronto! Dataset gerado com {len(dataset)} exemplos. Capivara Romântica is alive!")

processar_multiplos_chats("./meus_chats", "henrique_dataset.jsonl", "Henrique Lima")