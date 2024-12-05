#!/bin/bash

# Arrêt du script en cas d'erreur
set -e

echo "🔄 Mise à jour du déploiement LightRAG..."

# Suppression du dossier existant et clone du repo sur le VPS
echo "📦 Récupération du code source..."
ssh ubuntu@vps-ovh "rm -rf ~/lightrag"
ssh ubuntu@vps-ovh "git clone https://github.com/Pass4Trip/LightRAG.git ~/lightrag"

# Créer et activer l'environnement virtuel
ssh ubuntu@vps-ovh "cd ~/lightrag && python3 -m venv venv && source venv/bin/activate"

# Installer les dépendances système pour les outils de build et les en-têtes de développement Python
ssh ubuntu@vps-ovh "sudo apt-get update && sudo apt-get install -y build-essential libssl-dev libffi-dev python3-dev"

# Installer les dépendances
ssh ubuntu@vps-ovh "cd ~/lightrag && source venv/bin/activate && pip install -r requirements.txt"

# Build l'image avec buildah
echo "🏗️  Construction de l'image Docker..."
ssh ubuntu@vps-ovh "cd ~/lightrag && chmod +x scripts/build.sh && ./scripts/build.sh"

# Push de l'image dans le registry local sur le VPS
echo "⬆️  Push de l'image vers le registry..."
ssh ubuntu@vps-ovh "buildah push localhost:32000/lightrag:v5-prefect"

# Redémarrage du pod pour prendre en compte les changements sur le VPS
echo "🔄 Redémarrage du pod LightRAG..."
ssh ubuntu@vps-ovh "microk8s kubectl rollout restart deployment lightrag"

# Attente que le pod soit prêt sur le VPS
echo "⏳ Attente que le pod soit prêt..."
ssh ubuntu@vps-ovh "microk8s kubectl rollout status deployment/lightrag"

echo "✨ Déploiement terminé avec succès!"

# Affichage des pods pour vérification sur le VPS
echo "📊 État des pods:"
ssh ubuntu@vps-ovh "microk8s kubectl get pods | grep lightrag"