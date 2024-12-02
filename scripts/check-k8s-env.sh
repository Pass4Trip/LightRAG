#!/bin/bash
#
# check-k8s-env.sh
# ---------------
# Description:
#   Vérifie les variables d'environnement dans les pods Kubernetes de LightRAG.
#   Affiche le statut de toutes les variables (ConfigMap et Secrets) avec des indicateurs visuels.
#
# Utilisation:
#   ./check-k8s-env.sh
#
# Prérequis:
#   - kubectl configuré avec accès au cluster
#   - Au moins un pod LightRAG en cours d'exécution
#
# Note:
#   Les valeurs des secrets sont masquées pour la sécurité
#

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Vérification des variables d'environnement Kubernetes ===${NC}\n"

# Récupérer le nom du pod
POD_NAME=$(microk8s kubectl get pods -l app=lightrag -o jsonpath="{.items[0].metadata.name}")

if [ -z "$POD_NAME" ]; then
    echo -e "${RED}❌ Aucun pod LightRAG trouvé${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Pod trouvé: $POD_NAME${NC}\n"

# Variables à vérifier
echo -e "${BLUE}=== Variables non-sensibles (ConfigMap) ===${NC}"
CONFIGMAP_VARS=(
    "RABBITMQ_USERNAME"
    "RABBITMQ_HOST"
    "RABBITMQ_PORT"
    "NEO4J_URI"
    "NEO4J_USERNAME"
    "PREFECT_ACCOUNT_ID"
    "PREFECT_WORKSPACE_ID"
    "VECTOR_DB_PATH"
)

for var in "${CONFIGMAP_VARS[@]}"; do
    value=$(microk8s kubectl exec $POD_NAME -- sh -c "echo \$$var")
    if [ -z "$value" ]; then
        echo -e "${RED}❌ $var: Non défini${NC}"
    else
        echo -e "${GREEN}✅ $var: $value${NC}"
    fi
done

echo -e "\n${BLUE}=== Variables sensibles (Secrets) ===${NC}"
SECRET_VARS=(
    "RABBITMQ_PASSWORD"
    "NEO4J_PASSWORD"
    "OVH_LLM_API_TOKEN"
)

for var in "${SECRET_VARS[@]}"; do
    value=$(microk8s kubectl exec $POD_NAME -- sh -c "echo \$$var")
    if [ -z "$value" ]; then
        echo -e "${RED}❌ $var: Non défini${NC}"
    else
        echo -e "${GREEN}✅ $var: ********${NC}"
    fi
done

echo -e "\n${BLUE}=== Vérification terminée ===${NC}"
