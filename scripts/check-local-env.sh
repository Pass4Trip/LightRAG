#!/bin/bash
#
# check-local-env.sh
# ----------------
# Description:
#   Vérifie les variables d'environnement locales pour LightRAG sur macOS.
#   Charge les variables depuis .env et vérifie leur disponibilité.
#
# Utilisation:
#   source ./check-local-env.sh
#
# Prérequis:
#   - Fichier .env dans le dossier parent
#   - Python et pip installés pour le développement local
#

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Vérification de l'environnement local LightRAG ===${NC}\n"

# Charger les variables depuis .env
ENV_FILE="../.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✅ Fichier .env trouvé${NC}"
    source "$ENV_FILE"
else
    echo -e "${RED}❌ Fichier .env non trouvé${NC}"
    exit 1
fi

echo -e "\n${BLUE}=== Variables non-sensibles ===${NC}"
check_var() {
    local var=$1
    local val=$(eval echo \$$var)
    if [ -n "$val" ]; then
        if [[ "$var" == *"PASSWORD"* || "$var" == *"TOKEN"* || "$var" == *"SECRET"* ]]; then
            echo -e "${GREEN}✅ $var: ********${NC}"
        else
            echo -e "${GREEN}✅ $var: $val${NC}"
        fi
    else
        echo -e "${RED}❌ $var: Non défini${NC}"
    fi
}

# Vérifier les variables non-sensibles
check_var "RABBITMQ_USERNAME"
check_var "RABBITMQ_HOST"
check_var "RABBITMQ_PORT"
check_var "NEO4J_URI"
check_var "NEO4J_USERNAME"
check_var "PREFECT_ACCOUNT_ID"
check_var "PREFECT_WORKSPACE_ID"
check_var "VECTOR_DB_PATH"

echo -e "\n${BLUE}=== Variables sensibles ===${NC}"
# Vérifier les variables sensibles
check_var "RABBITMQ_PASSWORD"
check_var "NEO4J_PASSWORD"
check_var "OVH_LLM_API_TOKEN"

# Vérifier les dépendances locales
echo -e "\n${BLUE}=== Dépendances Python ===${NC}"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✅ Python3 installé: $(python3 --version)${NC}"
else
    echo -e "${RED}❌ Python3 non trouvé${NC}"
fi

if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ Pip3 installé: $(pip3 --version)${NC}"
else
    echo -e "${RED}❌ Pip3 non trouvé${NC}"
fi


echo -e "\n${BLUE}=== Vérification terminée ===${NC}"
