FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app/LightRAG

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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

# Commande par défaut
CMD ["python", "-u", "lightrag_insert.py"]
