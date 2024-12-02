#!/bin/bash
#
# activate-env.sh
# -------------
# Description:
#   Active l'environnement virtuel et configure les variables d'environnement
#   pour LightRAG.
#
# Utilisation:
#   source ./activate-env.sh
#

# Activer l'environnement virtuel
source ../venv/bin/activate

# Charger les variables d'environnement
source ./update-local-env.sh

echo -e "\n✅ Environnement LightRAG activé et configuré!"
