#!/bin/bash
#
# update-env.sh
# ------------
# Description:
#   Met à jour les ConfigMaps et Secrets dans Kubernetes avec les variables
#   d'environnement actuelles. Redémarre ensuite le déploiement pour appliquer
#   les changements.
#
# Utilisation:
#   1. D'abord charger les variables : source ./export-env.sh
#   2. Puis exécuter : ./update-env.sh
#
# Prérequis:
#   - kubectl configuré avec accès au cluster
#   - Variables d'environnement chargées (via export-env.sh)
#   - Droits suffisants pour modifier ConfigMaps et Secrets
#
# Actions:
#   1. Supprime et recrée la ConfigMap lightrag-config
#   2. Supprime et recrée le Secret lightrag-secrets
#   3. Redémarre le déploiement lightrag-deployment
#

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Mise à jour des variables d'environnement Kubernetes ===${NC}\n"

# 1. Mise à jour des ConfigMaps (variables non-sensibles)
echo -e "${GREEN}1. Mise à jour des ConfigMaps...${NC}"
microk8s kubectl delete configmap lightrag-config || true
microk8s kubectl create configmap lightrag-config \
    --from-literal=RABBITMQ_USERNAME=rabbitmq \
    --from-literal=RABBITMQ_HOST=51.77.200.196 \
    --from-literal=RABBITMQ_PORT=30645 \
    --from-literal=NEO4J_URI=bolt://51.77.200.196:30687 \
    --from-literal=NEO4J_USERNAME=neo4j \
    --from-literal=VECTOR_DB_PATH=/home/ubuntu/lightrag_data \
    --from-literal=PREFECT_ACCOUNT_ID=1de47cd9-a32e-4a43-8545-fd3bab9eaabe \
    --from-literal=PREFECT_WORKSPACE_ID=59349ca6-8f64-4b16-b768-5c70d28a342e

# 2. Mise à jour des Secrets (variables sensibles)
echo -e "\n${GREEN}2. Mise à jour des Secrets...${NC}"
microk8s kubectl delete secret lightrag-secrets || true
microk8s kubectl create secret generic lightrag-secrets \
    --from-literal=RABBITMQ_PASSWORD="$RABBITMQ_PASSWORD" \
    --from-literal=NEO4J_PASSWORD="$NEO4J_PASSWORD" \
    --from-literal=OVH_LLM_API_TOKEN="$OVH_LLM_API_TOKEN"

# 3. Redémarrage du déploiement pour prendre en compte les changements
echo -e "\n${GREEN}3. Redémarrage du déploiement...${NC}"
microk8s kubectl rollout restart deployment lightrag-deployment

echo -e "\n${BLUE}=== Mise à jour terminée ===${NC}"
echo "Pour vérifier le statut du déploiement:"
echo "kubectl get pods"
echo "kubectl logs -f <nom-du-pod>"
