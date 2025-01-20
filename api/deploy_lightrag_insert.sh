#!/bin/bash

# Configuration
LOCAL_PATH="/Users/vinh/Documents/LightRAG"
APP_NAME="lightrag-insert"
APP_TAG="v1"
CONTAINER_NAME="lightrag-insert-local"
HOST_PORT=8000

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Déploiement local de ${APP_NAME}...${NC}"

# Arrêter et supprimer le conteneur existant si présent
docker stop ${CONTAINER_NAME} 2>/dev/null
docker rm ${CONTAINER_NAME} 2>/dev/null

# Build de l'image Docker
docker build \
    -t ${APP_NAME}:${APP_TAG} \
    -f ${LOCAL_PATH}/api/Dockerfile \
    ${LOCAL_PATH}

# Lancer le conteneur
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${HOST_PORT}:8000 \
    -e RUNTIME_ENV=development \
    ${APP_NAME}:${APP_TAG}

# Vérifier le statut du conteneur
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Conteneur démarré avec succès${NC}"
    echo -e "${YELLOW}🌐 Accessible sur http://localhost:${HOST_PORT}${NC}"
    
    # Afficher les logs
    echo -e "${YELLOW}📋 Logs du conteneur :${NC}"
    docker logs ${CONTAINER_NAME}
else
    echo -e "${RED}❌ Échec du démarrage du conteneur${NC}"
    exit 1
fi

# Liste des conteneurs en cours
echo -e "${YELLOW}🔍 Conteneurs en cours :${NC}"
docker ps | grep ${APP_NAME}
