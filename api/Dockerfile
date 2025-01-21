FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app/LightRAG

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Installer Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"
ENV RUSTUP_HOME=/root/.rustup
ENV CARGO_HOME=/root/.cargo
RUN . "$HOME/.cargo/env" && \
    rustup default stable && \
    rustc --version && \
    cargo --version

# Copier tout le projet
COPY . ./

# Installer les dépendances Python
RUN pip install -r requirements.txt

# Définir le répertoire de travail sur le dossier API
WORKDIR /app/LightRAG/api

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


# Exposer le port sur lequel l'application va tourner
EXPOSE 8000

# Commande pour lancer l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
