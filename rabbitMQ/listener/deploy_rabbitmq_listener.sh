#!/bin/bash

# Configuration
VPS_HOST="vps-af24e24d.vps.ovh.net"
VPS_IP="51.77.200.196"
VPS_USER="ubuntu"
REGISTRY_PORT="32000"
LOCAL_PATH="/Users/vinh/Documents/LightRAG/rabbitMQ/listener"
APP_NAME="rabbitmq-listener"
APP_TAG="v1"

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🚀 Déploiement de ${APP_NAME}...${NC}"

# Nettoyer les images locales
echo -e "${YELLOW}🧹 Nettoyage des images locales...${NC}"
docker rmi -f ${APP_NAME} ${VPS_IP}:${REGISTRY_PORT}/${APP_NAME} 2>/dev/null || true

# Build de l'image pour linux/amd64
echo -e "${YELLOW}🔨 Build de l'image Docker...${NC}"
docker build --no-cache --platform linux/amd64 -t ${APP_NAME}:${APP_TAG} ${LOCAL_PATH}

# Tag de l'image pour le registry local
echo -e "${YELLOW}🏷️  Tag de l'image...${NC}"
docker tag ${APP_NAME}:${APP_TAG} ${VPS_IP}:${REGISTRY_PORT}/${APP_NAME}:${APP_TAG}

# Push de l'image vers le registry
echo -e "${YELLOW}📤 Push de l'image vers le registry...${NC}"
docker push ${VPS_IP}:${REGISTRY_PORT}/${APP_NAME}:${APP_TAG}

# Nettoyer et préparer le VPS
echo -e "${YELLOW}🧹 Préparation du VPS...${NC}"
ssh ${VPS_USER}@${VPS_HOST} "
    set -x  # Mode debug pour afficher chaque commande
    
    # Créer le répertoire s'il n'existe pas
    mkdir -p /home/ubuntu/LightRAG/rabbitMQ/listener
"

# Copier le fichier de déploiement
scp ${LOCAL_PATH}/deployment.yaml ${VPS_USER}@${VPS_HOST}:/home/ubuntu/LightRAG/rabbitMQ/listener/deployment.yaml

# Commandes finales sur le VPS
ssh ${VPS_USER}@${VPS_HOST} "
    set -x  # Mode debug pour afficher chaque commande
    
    # Supprimer le secret existant avant de le recréer
    microk8s kubectl delete secret rabbitmq-credentials || true
    
    # Créer le secret
    microk8s kubectl create secret generic rabbitmq-credentials \
        --from-literal=host=51.77.200.196 \
        --from-literal=port=30645 \
        --from-literal=username=rabbitmq \
        --from-literal=password=mypassword \
        -n default
    
    # Vérifier les images existantes
    microk8s ctr image ls | grep localhost:32000/${APP_NAME}:${APP_TAG} || echo \"Aucune image trouvée\"
    
    # Supprimer les anciennes images
    microk8s ctr image rm localhost:32000/${APP_NAME}:${APP_TAG} 2>&1 || echo \"Aucune image à supprimer\"
"

# Redéploiement du pod
echo -e "${YELLOW}🔄 Redéploiement du pod...${NC}"
if ssh ${VPS_USER}@${VPS_HOST} "
    # Debug: Vérifier l'image actuelle
    echo '🔍 Image actuelle :'
    microk8s kubectl get deployment ${APP_NAME} -o=jsonpath='{.spec.template.spec.containers[0].image}'
    echo
    
    # Appliquer le déploiement
    microk8s kubectl apply -f /home/ubuntu/LightRAG/rabbitMQ/listener/deployment.yaml
  
    # Redémarrer le déploiement
    microk8s kubectl rollout restart deployment ${APP_NAME}
"
then
    
    # Vérification détaillée du pod
    echo -e "${YELLOW}🔍 Vérification du pod déployé...${NC}"
    
    # Récupérer les détails du pod
    POD_INFO=$(ssh ${VPS_USER}@${VPS_HOST} "microk8s kubectl get pods -l app=${APP_NAME} -o=jsonpath='{.items[0].metadata.name} {.items[0].status.containerStatuses[0].imageID} {.items[0].status.containerStatuses[0].image} {.items[0].metadata.creationTimestamp}'")
    
    echo -e "${YELLOW}Détails du pod :${NC}"
    echo "$POD_INFO" | awk '{print "Nom du pod: " $1 "\nImage ID: " $2 "\nImage: " $3 "\nDate de création: " $4}'
    
    echo -e "${GREEN}✅ Déploiement terminé avec succès${NC}"
else
    echo -e "${RED}❌ Échec du déploiement${NC}"
    exit 1
fi
