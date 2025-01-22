#!/bin/zsh

# Configuration
APP_NAME="lightrag-api"
APP_TAG="v1"
REGISTRY="51.77.200.196:32000"
LOCAL_PATH="/Users/vinh/Documents/LightRAG"
VPS_HOST="ubuntu@51.77.200.196"

# Couleurs
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Nettoyer les ressources existantes
clean_resources() {
    echo -e "${YELLOW}🧹 Nettoyage des ressources existantes...${NC}"
    docker stop "$APP_NAME" 2>/dev/null
    docker rm "$APP_NAME" 2>/dev/null
    docker rmi "$REGISTRY/$APP_NAME:$APP_TAG" 2>/dev/null
}

# Construire l'image
build_image() {
    echo "${GREEN}🚢 Construction de l'image...${NC}"
    docker build \
        -t "$REGISTRY/lightrag-api:v1" \
        -f "$LOCAL_PATH/api/Dockerfile" \
        "$LOCAL_PATH"
}

# Pousser l'image
push_image() {
    echo "${YELLOW}📤 Envoi de l'image vers le registry...${NC}"
    docker push "$REGISTRY/$APP_NAME:$APP_TAG"
}

# Déployer sur Kubernetes
deploy_kubernetes() {
    echo "${GREEN}🌐 Déploiement sur Kubernetes...${NC}"
    scp "$LOCAL_PATH/api/lightrag_deployment.yaml" "$VPS_HOST":~/lightrag_deployment.yaml
    scp "$LOCAL_PATH/api/lightrag-api-ingress.yaml" "$VPS_HOST":~/lightrag-api-ingress.yaml
    ssh vps-ovh "
        microk8s kubectl apply -f api/lightrag_deployment.yaml
        microk8s kubectl apply -f api/lightrag-api-ingress.yaml
        microk8s kubectl rollout restart deployment $APP_NAME
    "
}

# Exécution principale
main() {
    clean_resources
    build_image
    push_image
    deploy_kubernetes
    echo "${GREEN}✅ Déploiement terminé avec succès !${NC}"
}

# Lancer le déploiement
main