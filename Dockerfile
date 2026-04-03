# Utiliza uma imagem leve do Python
FROM python:3.10-slim

# Define o diretório onde nossa aplicação rodará no container
WORKDIR /app

# Copia e instala primeiro os requirements (aproveita cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia os demais arquivos do projeto
COPY . .

# Comando utilizado pela plataforma (ex: Render) para iniciar o Uvicorn
# O Render dinamicamente injeta a variável PORT, por isso referenciamos ela na inicialização
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
