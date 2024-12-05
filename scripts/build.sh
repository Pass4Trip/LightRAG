#!/bin/bash

# Cette fonction contient la logique de build
build_image() {
    # Créer un nouveau conteneur
    echo "📦 Création du conteneur de base..."
    container=$(buildah from python:3.12-slim)

    # Monter le conteneur
    mount=$(buildah mount $container)

    # Installer les dépendances système
    echo "📥 Installation des dépendances système..."
    buildah run $container apt-get update
    buildah run $container apt-get install -y --no-install-recommends build-essential git curl
    buildah run $container rm -rf /var/lib/apt/lists/*

    # Créer l'environnement virtuel
    echo "🐍 Configuration de l'environnement Python..."
    buildah run $container python3 -m venv /opt/venv
    buildah config --env PATH="/opt/venv/bin:$PATH" $container

    # Copier et installer les dépendances
    echo "📥 Installation des dépendances Python..."
    buildah copy $container requirements.txt /app/
    buildah config --workingdir /app $container
    buildah run $container pip install --no-cache-dir --upgrade pip
    buildah run $container pip install --no-cache-dir -r requirements.txt

    # Copier les fichiers nécessaires
    echo "📁 Copie des fichiers de l'application..."
    buildah copy $container examples/lightrag_openai_compatible_demo_rabbitmq.py /app/
    buildah copy $container lightrag /app/lightrag/

    # Trouver le chemin du package lightrag et copier notre version légère de llm.py
    echo "🔄 Configuration du module LightRAG..."
    buildah copy $container local/llm.py /app/local/
    buildah run $container bash -c 'PACKAGE_PATH=$(python3 -c "import lightrag; print(lightrag.__path__[0])") && cp /app/local/llm.py $PACKAGE_PATH/llm.py'

    # Créer le répertoire data
    buildah run $container mkdir -p /app/data
    buildah run $container chmod -R 777 /app/data

    # Configurer les variables d'environnement
    echo "⚙️  Configuration des variables d'environnement..."
    buildah config --env PYTHONUNBUFFERED=1 $container
    buildah config --env PYTHONDONTWRITEBYTECODE=1 $container
    buildah config --env PYTHONPATH=/app $container
    buildah config --env VECTOR_DB_PATH=/app/data $container

    # Configurer la commande par défaut
    buildah config --cmd "python /app/lightrag_openai_compatible_demo_rabbitmq.py" $container

    # Créer l'image
    echo "💾 Création de l'image finale..."
    buildah commit $container localhost:32000/lightrag:v5-prefect
}

# Arrêt du script en cas d'erreur
set -e

echo "🏗️  Construction de l'image Docker..."

# Exécuter le build dans buildah unshare
buildah unshare bash -c "$(declare -f build_image); build_image"

echo "✨ Construction de l'image terminée avec succès!"
