FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app/LightRAG

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installer Rust
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copier uniquement les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier uniquement les fichiers nécessaires
COPY api/ ./api/

# Définir le répertoire de travail sur le dossier API
WORKDIR /app/LightRAG/api

# Variables d'environnement par défaut
ENV PYTHONUNBUFFERED=1
ENV RUNTIME_ENV=production
ENV PYTHONPATH=/app/LightRAG
ENV NEO4J_URI=bolt://vps-ovh:7687
ENV NEO4J_USERNAME=neo4j
ENV NEO4J_PASSWORD=password
ENV MILVUS_URI=http://vps-ovh:19530
ENV MILVUS_USERNAME=root
ENV MILVUS_PASSWORD=Milvus

# Commande par défaut
CMD ["python", "-u", "lightrag_insert.py"]
