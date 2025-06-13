# Imagem base com Python e dependências de build
FROM python:3.11-slim

# Instala dependências do sistema necessárias pro dlib
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria diretório de trabalho
WORKDIR /app

# Copia o projeto
COPY . .

# Instala as dependências Python
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expõe a porta do Flask
EXPOSE 5000

# Comando para iniciar o app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]

