#!/bin/bash

# Configuration
LOCAL_PATH="/Users/vinh/Documents/LightRAG"
PROJECT_NAME="LightRAG"
APP_NAME="lightrag-api"
APP_TAG="v1"
HOST_PORT=8000

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Vérifier les dépendances
command -v docker >/dev/null 2>&1 || { 
    echo -e "${RED}❌ Docker n'est pas installé. Installez Docker Desktop.${NC}"
    exit 1
}

echo -e "${YELLOW}🚀 Déploiement local de ${APP_NAME}...${NC}"

# Arrêter et supprimer le conteneur existant si présent
echo -e "${YELLOW}🧹 Nettoyage des conteneurs existants...${NC}"
docker stop ${APP_NAME} 2>/dev/null
docker rm ${APP_NAME} 2>/dev/null

# Créer un Dockerfile temporaire qui copie tout le projet
echo -e "${YELLOW}🔨 Préparation du Dockerfile...${NC}"
cat > ${LOCAL_PATH}/Dockerfile.temp << EOL
FROM python:3.10-slim

# Définir le répertoire de travail
WORKDIR /app/${PROJECT_NAME}

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Installer Rust et Cargo
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copier uniquement les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le projet
COPY . .

# Définir le répertoire de travail sur le dossier API
WORKDIR /app/${PROJECT_NAME}/api

# Commande par défaut
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

# Build de l'image Docker
echo -e "${YELLOW}🔨 Build de l'image Docker...${NC}"
docker build \
    -t ${APP_NAME}:${APP_TAG} \
    -f ${LOCAL_PATH}/Dockerfile.temp \
    ${LOCAL_PATH}

# Supprimer le Dockerfile temporaire
rm ${LOCAL_PATH}/Dockerfile.temp

# Lancer le conteneur
echo -e "${YELLOW}🚢 Démarrage du conteneur...${NC}"
docker run -d \
    --name ${APP_NAME} \
    -p ${HOST_PORT}:8000 \
    -e RUNTIME_ENV=development \
    ${APP_NAME}:${APP_TAG}

# Vérifier le statut du conteneur
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conteneur démarré avec succès${NC}"
    echo -e "${YELLOW}🌐 Endpoints disponibles :${NC}"
    echo -e "  - Racine : http://localhost:${HOST_PORT}/"
    echo -e "  - Insertion : http://localhost:${HOST_PORT}/insert/"
    echo -e "  - Recherche : http://localhost:${HOST_PORT}/query/"
    
    # Attendre quelques secondes pour s'assurer que le conteneur est prêt
    sleep 5
    
    # Tester les endpoints
    echo -e "${YELLOW}🔍 Test des endpoints...${NC}"
    
    # Test de l'endpoint racine
    ROOT_RESPONSE=$(curl -s http://localhost:${HOST_PORT}/)
    echo -e "  - Endpoint racine : ${ROOT_RESPONSE}"
    
    # Test de l'endpoint d'insertion (avec un payload minimal)
    INSERT_RESPONSE=$(curl -s -X POST http://localhost:${HOST_PORT}/insert/ \
        -H "Content-Type: application/json" \
        -d '{"type": "test", "content": "Message de test"}')
    echo -e "  - Endpoint insertion : ${INSERT_RESPONSE}"
    
    # Test de l'endpoint de recherche (avec un payload minimal)
    QUERY_RESPONSE=$(curl -s -X POST http://localhost:${HOST_PORT}/query/ \
        -H "Content-Type: application/json" \
        -d '{"question": "Test de requête"}')
    echo -e "  - Endpoint recherche : ${QUERY_RESPONSE}"
    
    # Afficher les logs du conteneur
    echo -e "${YELLOW}📋 Logs du conteneur :${NC}"
    docker logs ${APP_NAME}
else
    echo -e "${RED}❌ Échec du démarrage du conteneur${NC}"
    exit 1
fi
