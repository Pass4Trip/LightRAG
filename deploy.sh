#!/bin/bash

# Arrêt du script en cas d'erreur
set -e

echo "🔄 Mise à jour du déploiement LightRAG..."

# Suppression du dossier existant et clone du repo sur le VPS
echo "📦 Récupération du code source..."
ssh ubuntu@vps-ovh "rm -rf ~/lightrag && git clone https://github.com/Pass4Trip/LightRAG.git ~/lightrag"

# Construction de l'image avec buildah sur le VPS
echo "🏗️  Construction de l'image Docker..."
ssh ubuntu@vps-ovh "cd ~/lightrag && buildah build --layers --force-rm -t localhost:32000/lightrag:v5-prefect ."

# Push de l'image dans le registry local sur le VPS
echo "⬆️  Push de l'image vers le registry..."
ssh ubuntu@vps-ovh "buildah push localhost:32000/lightrag:v5-prefect"

# Application des configurations Kubernetes sur le VPS
echo "🔧 Application des configurations Kubernetes..."
ssh ubuntu@vps-ovh "microk8s kubectl apply -f ~/lightrag/yaml/kubernetes-config.yaml"

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
