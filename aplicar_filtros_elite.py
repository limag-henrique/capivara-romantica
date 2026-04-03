import json
import re
import random

filepath = 'henrique_dataset_ELITE.jsonl'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []

grosserias = [ r'\bvsf\b', r'\btnc\b', r'\bfoda-se', r'\bfodase\b', 
               r'\bcala a boca\b', r'\bvai a merda\b', r'\bvai tomar no', 
               r'\bsai fora\b', r'\bme erra\b', r'\bse foder\b', r'\boteário\b', r'\bbabaca\b',
               r'\bvai se foder\b', r'\bme esquece\b', r'^não$', r'^não\s+interessa' ]

puxar_assunto = [
    " mas iai, oq ta mandando hj?", " e vc, novidades?", " me conta ai, de q curso vc é mesmo?", 
    " e a vida acadêmica, sofrendo mto?", " mas mudando de assunto, curte um cineminha?", 
    " foda kkkk e qual a boa pra hj?", " ah sim kkkkkk vc é d bh?", " boto fé kkk q q c ta arrumando?"
]

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

creep_words = [r'calcinha', r'tecido\s+esticar', r'let[íi]cia', r'j[uú]lia', r'ver\s+detalhes']

for line in lines:
    data = json.loads(line)
    user_msg = data['messages'][1]['content']
    ast_msg = data['messages'][2]['content']
    
    # 1. Creep check
    is_creepy = False
    for cw in creep_words:
        if re.search(cw, user_msg, re.IGNORECASE) or re.search(cw, ast_msg, re.IGNORECASE):
            is_creepy = True; break
    if is_creepy: continue
    
    # 2. Supérfluo
    user_msg = re.sub(r'(?i)sup[eé]rfulo', 'supérfluo', user_msg)
    ast_msg = re.sub(r'(?i)sup[eé]rfulo', 'supérfluo', ast_msg)
    
    # 3. [Amigo] / Brackets -> uai / mano
    user_msg = re.sub(r'\[.*?\]', 'mano', user_msg)
    ast_msg = re.sub(r'\[Amigo\]', 'uai', ast_msg)
    ast_msg = re.sub(r'\[.*?\]', 'mano', ast_msg)
    
    # 4. Geographics
    ast_msg = re.sub(r'(?i)interior do nordeste', 'interior de Minas', ast_msg)
    ast_msg = re.sub(r'(?i)\bnordeste\b', 'interior de Minas', ast_msg)
    ast_msg = re.sub(r'(?i)\bsão paulo\b', 'Belo Horizonte', ast_msg)
    ast_msg = re.sub(r'(?i)\bsp\b', 'bh', ast_msg)
    ast_msg = re.sub(r'(?i)\bpuc\b', 'outra universidade', ast_msg)
    
    # 5. Fix Aggression
    ast_msg = ast_msg.replace('N INTERESSA 💁🏿‍♂️', 'kkkkk segredo nosso')
    ast_msg = ast_msg.replace('N INTERESSA', 'segredo po kkkk')
    ast_msg = ast_msg.replace('não interessa', 'segredo uai kkkk')
    for g in grosserias:
        if re.search(g, ast_msg, re.IGNORECASE):
            ast_msg = re.sub(g, 'kkkk q bobagem', ast_msg, flags=re.IGNORECASE)
            
    # 6. Specific Cartaz Hook
    if 'privilégios ganhou so far' in user_msg.lower():
        ast_msg = "além da minha companhia incrível? kkkk tem a bolsa de 700 reais que prometi no cartaz e o cartão da fump que é ouro puro"

    data['messages'][1]['content'] = user_msg
    data['messages'][2]['content'] = ast_msg
    new_lines.append(data)

# Inject hooks
random.seed(123)
hooks_added = 0
for i in range(len(new_lines)):
    if hooks_added < 40 and len(new_lines[i]['messages'][2]['content']) > 15 and random.random() < 0.05:
        new_lines[i]['messages'][2]['content'] += random.choice(cartaz_hooks)
        hooks_added += 1

# Puxar assunto
for i in range(len(new_lines)):
    if len(new_lines[i]['messages'][2]['content'].split()) <= 4 and random.random() < 0.15:
        new_lines[i]['messages'][2]['content'] += random.choice(puxar_assunto)

# Sweet Spot Downsampling
tamanho_original = len(new_lines)
if len(new_lines) > 1050:
    new_lines = random.sample(new_lines, 1050)

with open(filepath, 'w', encoding='utf-8') as f:
    for item in new_lines:
        f.write(json.dumps(item, ensure_ascii=False) + '\n')

print(f"Dataset final ELITE purificado! Foi de {tamanho_original} para {len(new_lines)} exemplos na medida exata!")
