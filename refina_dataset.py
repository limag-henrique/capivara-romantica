import json
import re
import random

random.seed(42) # reprodutível

filepath = 'henrique_dataset.jsonl'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []

cartaz_hooks = [
    " mas me fala, vc viu a bolsa de 700 q prometi no cartaz né? kkkk",
    " só lembrando da regra de ouro do cartaz: aluno da face é barrado viu",
    " kkkk e pelo visto vc quer meu cartão da fump, confessa",
    " uai, mas pra fechar comigo tem q topar andar nas viagens da buser q tão no cartaz kkk",
    " não esquece q a modalidade é financiamento ein... só libero os 700 reais dps da formatura kkkk",
    " me diz q vc não é da face, senão o cartaz já te barra",
    " lembrando q eu sofro no ICEx e tô liso, por isso lancei aquele cartaz kkk",
    " a vaga pro meu cartaz de financiamento ainda tá de pé viu kkkk"
]

count_hooks = 0
count_removed = 0
fixed_superfluo = 0
specific_hook_fixed = False

for line in lines:
    data = json.loads(line)
    user_msg = data['messages'][1]['content']
    ast_msg = data['messages'][2]['content']
    
    # 2. Remoção do Alerta Amarelo de Assédio/Creepy
    creep_words = [r'calcinha', r'tecido\s+esticar', r'let[íi]cia', r'j[uú]lia', r'ver\s+detalhes']
    is_creepy = False
    for cw in creep_words:
        if re.search(cw, user_msg, re.IGNORECASE) or re.search(cw, ast_msg, re.IGNORECASE):
            is_creepy = True
            break
            
    if is_creepy:
        count_removed += 1
        continue
        
    # 1. Correção Ortográfica: Supérfulo -> Supérfluo
    if re.search(r'(?i)sup[eé]rfulo', user_msg):
        user_msg = re.sub(r'(?i)sup[eé]rfulo', 'supérfluo', user_msg)
    if re.search(r'(?i)sup[eé]rfulo', ast_msg):
        ast_msg = re.sub(r'(?i)sup[eé]rfulo', 'supérfluo', ast_msg)
        fixed_superfluo += 1
        
    # 3. Consertar o Hook específico
    if 'privilégios ganhou so far' in user_msg.lower():
        ast_msg = "além da minha companhia incrível? kkkk tem a bolsa de 700 reais que prometi no cartaz e o cartão da fump que é ouro puro"
        specific_hook_fixed = True
        
    else:
        # Adicionar ganchos do cartaz aleatoriamente para ancorar o comportamento do modelo
        # Seleciona de forma randômica cerca de 40 conversas longas
        if count_hooks < 40 and len(ast_msg) > 15:
            # Em torno de 5% de chance p pegar 40 nas 1800+ restantes
            if random.random() < 0.05:
                # Usa \n ou só joga lá
                ast_msg += random.choice(cartaz_hooks)
                count_hooks += 1

    data['messages'][1]['content'] = user_msg
    data['messages'][2]['content'] = ast_msg
    new_lines.append(json.dumps(data, ensure_ascii=False) + '\n')

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Dataset refinado!")
print(f"Linhas comprometidas removidas: {count_removed}")
print(f"Gafes de 'supérfulo' corrigidas no assistente: {fixed_superfluo}")
print(f"Gancho específico foi corrigido? {specific_hook_fixed}")
print(f"Menções do cartaz injetadas nos exemplos: {count_hooks}")
