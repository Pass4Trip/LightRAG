#!/bin/zsh

# Configuration
APP_NAME="rabbitmq-listener"
APP_TAG="v1"
REGISTRY="51.77.200.196:32000"
LOCAL_PATH="/Users/vinh/Documents/LightRAG/rabbitMQ/listener"
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
        --platform linux/amd64 \
        -t "$REGISTRY/$APP_NAME:$APP_TAG" \
        -f "$LOCAL_PATH/Dockerfile" \
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
    
    # Supprimer le secret existant avant de le recréer
    ssh $VPS_HOST "
        microk8s kubectl delete secret rabbitmq-credentials || true
        
        # Créer le secret
        microk8s kubectl create secret generic rabbitmq-credentials \
            --from-literal=host=51.77.200.196 \
            --from-literal=port=30645 \
            --from-literal=username=rabbitmq \
            --from-literal=password=mypassword \
            -n default
    "
    
    # Copier le fichier de déploiement
    scp "$LOCAL_PATH/deployment.yaml" "$VPS_HOST":~/LightRAG/rabbitMQ/listener/deployment.yaml
    
    # Déployer sur Kubernetes
    ssh vps-ovh "
        microk8s kubectl apply -f /home/ubuntu/LightRAG/rabbitMQ/listener/deployment.yaml
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
