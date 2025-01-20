# Utiliser une image Python officielle
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY rabbitmq_listener.py .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Variables d'environnement par défaut (peuvent être surchargées)
ENV RABBITMQ_HOST=51.77.200.196
ENV RABBITMQ_PORT=30645
ENV RABBITMQ_USER=rabbitmq
ENV RABBITMQ_PASSWORD=mypassword
ENV RABBITMQ_QUEUE=queue_vinh_test

# Commande par défaut
CMD ["python", "rabbitmq_listener.py"]
