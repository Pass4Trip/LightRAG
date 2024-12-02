#!/bin/bash
#
# update-local-env.sh
# -----------------
# Description:
#   Met à jour les variables d'environnement locales pour LightRAG sur macOS.
#   Charge les variables depuis .env et les configure pour la session courante.
#
# Utilisation:
#   source ./update-local-env.sh
#
# Note importante:
#   Ce script doit être exécuté avec 'source' pour que les variables
#   persistent dans votre session shell actuelle.
#

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Mise à jour des variables d'environnement locales ===${NC}\n"

# Chemin vers le fichier .env
ENV_FILE="/Users/vinh/Documents/LightRAG/.env"

# Vérifier si le fichier .env existe
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Fichier .env non trouvé dans $ENV_FILE${NC}"
    return 1
fi

echo -e "${GREEN}✅ Fichier .env trouvé${NC}"

# Variables à configurer
declare -A variables=(
    # Variables non-sensibles
    ["RABBITMQ_USERNAME"]="rabbitmq"
    ["RABBITMQ_HOST"]="51.77.200.196"
    ["RABBITMQ_PORT"]="30645"
    ["NEO4J_URI"]="bolt://51.77.200.196:30687"
    ["NEO4J_USERNAME"]="neo4j"
    ["PREFECT_ACCOUNT_ID"]="1de47cd9-a32e-4a43-8545-fd3bab9eaabe"
    ["PREFECT_WORKSPACE_ID"]="59349ca6-8f64-4b16-b768-5c70d28a342e"
    ["VECTOR_DB_PATH"]="/app/data/nano-vectorDB"
    # Variables sensibles
    ["RABBITMQ_PASSWORD"]="mypassword"
    ["NEO4J_PASSWORD"]="mypassword"
    ["OVH_LLM_API_TOKEN"]="eyJhbGciOiJFZERTQSJ9.eyJwcm9qZWN0IjoiMzE1M2Q2ZTZjMjZmNDM0YzhiNDVjNjFlNDA2NzIwMjIiLCJhdWQiOiIzNzM4NjExNjY0MDQzMDM0IiwiZXhwIjoxNzM1NDE3NjYzLCJqdGkiOiI0NzkzOGZkNS05NDQ3LTQ4ODctOTc0Ny1mNGI4NzRjODAxYzciLCJpc3MiOiJ0cmFpbmluZy5haS5jbG91ZC5vdmgubmV0Iiwic3ViIjoidGE2NTkyMDYtb3ZoIiwib3ZoVG9rZW4iOiI3elR5YmxlQ1JRNkx4WnZzdFF3dDRtUnVtcW1jRDF1aV9LdS1SS3c0VC0zTHE1a08zZjlraUtQSF9OY3NpVGp6Z2dHbXB2aHZnMnJncTM4cnBWUnpvanVEQnZqdld3ejRaRzFtOWtXOGpkNmVhNHpCSWJXVVd2TXlHVWV3amVLWWM5bkFuY0psQmg5b1hrVnFCWlp2eGhaMDY1R21tSUprOWVwWk5Gam8ta1MzSTd3VzlYbGNNYTNfcFdLOHRsUjBHSGJjRkszdE9pZXQzNmxYQTh6MUxKN2x3Wm51NmRDLVh6MlRDWGN4bVFlcGhsVEpWb0t3MEQtOXZGblMxckV5Y0dGcldWQk1UTDhwbHhxdkNSMm1QazMyOUVrOUhpUXUxekViWmNvT3FGR016b3dMOEd5Z1VZLWVSUERzbEtGTnB5bmlnU3hVRVF0QnNndm94cGE4M0tpS1FILU5BS19oSUwtR0t3VFdsaVY4cF9CdFpXNHJMNHpULUxqOHoyOExFS01uX1hpZ1FHY3RLckRkT1R6dnl1cEdXeDNvMVVWVmxkS0swaXQ5U3g5aUc4a18yWFVaalRTNGZrRWZjVDVvNm9GQVNkcVZKWE9vRTJjMWtCQ0NRTEhNRXJRbC1jdm5lWi1jYmE3enRJZ0VXdUdnZ2pIS0lHemZlNmNKTnAxXzE0d2x1cXFTcEROYVZrc2FJSklzc01WV0NOVlBaUy1IM0UxUXRyWnlTWUVrZTB1UE9sOVFUSndyR3BmTXBNNHZSR2czNkVDXzlnSnp6YXBXZENibnYwT1ZPemVwUXhBTG95VUl3M0drUEptc1N5eUQtWENnSndabjNJcEZ3QjhOODZNNFFlVFRITFcxby1oUGhrYmc3b05wSXZwU1JGUFNBUXItcFpIYlg0eHVKNW1Gd1I4bjd2aDJ3cVppY3JoZGpkTkxFZlJQTW1ZdzhhUmxJMnUwQnJybThlYmM1U1RFaXlKVlpuVy1FNTE5dXN4ckdjU0dXVVR4TEIyclFEbkswX08xMlRlVG81elRnaXJFRGVDcnNqRGJtbEItQ01PV3Y2WU5jQWRoaWJ2WmR4WmtRRklqZXpaRmtBdl9vTkFXRUZnQVdEN2lsM19FaVM3NDNzbkZqNUpHYXB2UC1IZDJZVFA1UFVwYmJNT0wtSGc5M2pqeWpTVnkzLXRGYjktbmMySFRsTFdHNG5wR2N1M2Q3N0tpSm80eXdpSnVwSWdiYlhtOTgtbHhnanota0pxZmh4UkZYa1lTSldzQUFwUUVaZUxmV1ZReFFFVHdIZi1sc0c4a2lsZnd4Qms0WktZb0xQLWZ5NDJvdkMycSJ9.fw8fL7oSy00Lo3dhpUwWNdms0t405r-Mbf3vVh2nCaElJwZTMLKsv0KWSQMdSzIh-kTpwWD7CtKs0ZUXYQd1Dw"
)

# Charger et exporter les variables
echo -e "\n${BLUE}=== Configuration des variables ===${NC}"
while IFS='=' read -r key value || [ -n "$key" ]; do
    # Ignorer les lignes vides ou commentées
    if [[ -z "$key" || "$key" =~ ^# ]]; then
        continue
    fi
    
    # Nettoyer la clé et la valeur
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs | sed 's/^["'"'"']//;s/["'"'"']$//')
    
    # Exporter la variable
    export "$key=$value"
    
    # Afficher le statut
    if [ -n "${variables[$key]}" ]; then
        if [[ "$key" == *"PASSWORD"* || "$key" == *"TOKEN"* || "$key" == *"SECRET"* ]]; then
            echo -e "${GREEN}✅ ${variables[$key]} ($key): ********${NC}"
        else
            echo -e "${GREEN}✅ ${variables[$key]} ($key): $value${NC}"
        fi
    fi
done < "$ENV_FILE"

echo -e "\n${BLUE}=== Configuration du PATH ===${NC}"
# Ajouter le dossier du projet au PYTHONPATH si nécessaire
PROJECT_ROOT=$(dirname $(dirname $(readlink -f "$0")))
if [[ ":$PYTHONPATH:" != *":$PROJECT_ROOT:"* ]]; then
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    echo -e "${GREEN}✅ PYTHONPATH mis à jour avec: $PROJECT_ROOT${NC}"
else
    echo -e "${BLUE}ℹ️  PYTHONPATH contient déjà: $PROJECT_ROOT${NC}"
fi

echo -e "\n${GREEN}✅ Variables d'environnement mises à jour avec succès!${NC}"
echo -e "${BLUE}ℹ️  Les variables sont disponibles uniquement dans la session shell courante.${NC}"
echo -e "${BLUE}ℹ️  Pour les rendre permanentes, ajoutez-les à votre ~/.zshrc ou ~/.bash_profile${NC}"
