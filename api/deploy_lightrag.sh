#!/bin/bash

# Couleurs pour les messages
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Définir les variables
PROJECT_NAME="LightRAG"
APP_NAME="lightrag-api"
APP_TAG="v1"
LOCAL_PATH="/Users/vinh/Documents/LightRAG"
HOST_PORT=8000

# Vérifier les dépendances
command -v docker >/dev/null 2>&1 || { 
    echo -e "${RED}❌ Docker n'est pas installé. Installez Docker Desktop.${NC}"
    exit 1
}

# Nettoyer les conteneurs et images existants
echo -e "${YELLOW}🧹 Nettoyage des conteneurs et images existants...${NC}"
docker stop ${APP_NAME} 2>/dev/null
docker rm ${APP_NAME} 2>/dev/null
docker rmi ${APP_NAME}:${APP_TAG} 2>/dev/null
docker rmi lightrag-base:latest 2>/dev/null

# Construire l'image de base
echo -e "${YELLOW}🔨 Construction de l'image de base...${NC}"
docker build \
    -t lightrag-base:latest \
    -f ${LOCAL_PATH}/Dockerfile.base \
    ${LOCAL_PATH}

# Construire l'image de l'API
echo -e "${YELLOW}🔨 Construction de l'image de l'API...${NC}"
docker build \
    -t ${APP_NAME}:${APP_TAG} \
    -f ${LOCAL_PATH}/api/Dockerfile \
    ${LOCAL_PATH}

# Vérifier la construction des images
if [[ "$(docker images -q ${APP_NAME}:${APP_TAG} 2> /dev/null)" == "" ]]; then
    echo -e "${RED}❌ Échec de la construction de l'image Docker${NC}"
    exit 1
fi

# Lancer le conteneur
echo -e "${YELLOW}🚢 Démarrage du conteneur...${NC}"
docker run -d \
    --name ${APP_NAME} \
    -p ${HOST_PORT}:8000 \
    -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
    ${APP_NAME}:${APP_TAG}

# Vérifier le statut du conteneur
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conteneur démarré avec succès${NC}"
    
    # Afficher les logs du conteneur
    echo -e "${YELLOW}📋 Logs du conteneur :${NC}"
    docker logs ${APP_NAME}
else
    echo -e "${RED}❌ Échec du démarrage du conteneur${NC}"
    exit 1
fi

# Nettoyer les images intermédiaires
docker image prune -f
