import json
import re
from prompts import SYSTEM_PROMPT

filepath = 'henrique_dataset.jsonl'
fixed_lines = []

with open(filepath, 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        
        # 1. Atualizar com o Prompt mais recente que está no prompts.py
        data['messages'][0]['content'] = SYSTEM_PROMPT
        
        user_msg = data['messages'][1]['content']
        ast_msg = data['messages'][2]['content']
        
        # Substitui [Amigo] por expressões neutras mineiras
        ast_msg = ast_msg.replace('[Amigo]', 'uai')
        user_msg = user_msg.replace('[Amigo]', 'uai')
        
        # Ajustes Geográficos para casar com o System Prompt (BH/UFMG)
        ast_msg = re.sub(r'(?i)interior do nordeste', 'interior de Minas', ast_msg)
        ast_msg = re.sub(r'(?i)\bnordeste\b', 'interior de Minas', ast_msg)
        ast_msg = re.sub(r'(?i)\bsão paulo\b', 'Belo Horizonte', ast_msg)
        ast_msg = re.sub(r'(?i)\bsp\b', 'bh', ast_msg)
        ast_msg = re.sub(r'(?i)\bpuc\b', 'outra universidade', ast_msg)
        
        # Ajustes de Grosseria
        ast_msg = ast_msg.replace('N INTERESSA 💁🏿‍♂️', 'kkkkk segredo nosso')
        ast_msg = ast_msg.replace('N INTERESSA 💁🏿‍♂️', 'kkkkk segredo nosso') # caso unicode diferencie
        ast_msg = ast_msg.replace('N INTERESSA', 'segredo po kkkk')
        ast_msg = ast_msg.replace('não interessa', 'segredo uai kkkk')
        
        data['messages'][1]['content'] = user_msg
        data['messages'][2]['content'] = ast_msg
        
        fixed_lines.append(json.dumps(data, ensure_ascii=False) + '\n')

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print(f"✅ {len(fixed_lines)} linhas verificadas e corrigidas no henrique_dataset.jsonl!")
