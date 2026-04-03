import json
import re
import random

random.seed(42)

filepath = 'henrique_dataset.jsonl'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []

grosserias = [ r'\bvsf\b', r'\btnc\b', r'\bfoda-se', r'\bfodase\b', 
               r'\bcala a boca\b', r'\bvai a merda\b', r'\bvai tomar no', 
               r'\bsai fora\b', r'\bme erra\b', r'\bse foder\b', r'\boteário\b', r'\bbabaca\b',
               r'\bvai se foder\b', r'\bme esquece\b', r'^não$', r'^não\s+interessa' ]

puxar_assunto = [
    " mas iai, oq ta mandando hj?",
    " e vc, novidades?",
    " me conta ai, de q curso vc é mesmo?",
    " e a vida acadêmica, sofrendo mto?",
    " mas mudando de assunto, curte um cineminha?",
    " foda kkkk e qual a boa pra hj?",
    " ah sim kkkkkk vc é d bh?",
    " boto fé kkk q q c ta arrumando?"
]

count_grosseria_fixed = 0
count_puxar_assunto = 0
count_brackets = 0

for line in lines:
    data = json.loads(line)
    user_msg = data['messages'][1]['content']
    ast_msg = data['messages'][2]['content']
    
    # 1. Placeholders [Amigo] / Brackets
    if re.search(r'\[.*?\]', ast_msg):
        ast_msg = re.sub(r'\[.*?\]', 'mano', ast_msg)
        count_brackets += 1
        
    if re.search(r'\[.*?\]', user_msg):
        user_msg = re.sub(r'\[.*?\]', 'mano', user_msg)

    # 2. Equilíbrio de Grosseria
    is_gross=False
    for g in grosserias:
        if re.search(g, ast_msg, re.IGNORECASE):
            is_gross=True
            # Suaviza a grosseria em caso extremo
            ast_msg = re.sub(g, 'kkkk q bobagem', ast_msg, flags=re.IGNORECASE)
            
    if is_gross:
        count_grosseria_fixed += 1
        
    # Puxa o assunto em respostas excessivamente curtas
    if len(ast_msg.split()) <= 4 and random.random() < 0.15: # 15% de chance numa resposta mt curta
        ast_msg += random.choice(puxar_assunto)
        count_puxar_assunto += 1
        
    data['messages'][1]['content'] = user_msg
    data['messages'][2]['content'] = ast_msg
    new_lines.append(json.dumps(data, ensure_ascii=False) + '\n')

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Dataset equilibrado!")
print(f"Colchetes consertados: {count_brackets}")
print(f"Grosserias suavizadas: {count_grosseria_fixed}")
print(f"Ganchos de 'puxar assunto' inseridos: {count_puxar_assunto}")
