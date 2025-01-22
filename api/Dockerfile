# Étape 1 : Dépendances de base
FROM --platform=linux/amd64 python:3.10-slim

# Répertoire de travail
WORKDIR /app/LightRAG

# Variables d'environnement par défaut
ENV PYTHONPATH=/app/LightRAG:/app/LightRAG/api
ENV PYTHONUNBUFFERED=1
ENV RUNTIME_ENV=production

ENV NEO4J_URI=bolt://vps-af24e24d.vps.ovh.net:32045
ENV NEO4J_USERNAME=neo4j
ENV NEO4J_PASSWORD=my-initial-password

ENV MILVUS_URI=http://51.77.200.196:19530
ENV MILVUS_USERNAME=root
ENV MILVUS_PASSWORD=Milvus
ENV MILVUS_DB_NAME=lightrag

ENV MONGO_URI=mongodb://root:root@vps-af24e24d.vps.ovh.net:30940/
ENV MONGO_DATABASE=LightRAG

ENV RABBITMQ_HOST=51.77.200.196
ENV RABBITMQ_PORT=30645
ENV RABBITMQ_USER=rabbitmq
ENV RABBITMQ_PASSWORD=mypassword
ENV RABBITMQ_QUEUE=queue_vinh_test

# Variables d'environnement supplémentaires
ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    CARGO_HOME=/root/.cargo \
    RUSTUP_HOME=/root/.rustup \
    PATH="/root/.cargo/bin:${PATH}"

# Installation de Rust et des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    git \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && . "$HOME/.cargo/env" \
    && rustup default stable \
    && rustc --version \
    && cargo --version

# Copier tous les fichiers sauf ./api
COPY . .

# Installer les dépendances Python, en ignorant les erreurs de compilation
RUN pip install --no-cache-dir -r requirements.txt 


# Exposition du port
EXPOSE 8000

# Commande pour démarrer l'application
CMD ["python", "-m", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]