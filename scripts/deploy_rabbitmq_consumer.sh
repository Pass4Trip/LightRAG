#!/bin/bash
set -e

# Se connecter au VPS-OVH via SSH
ssh root@vps-ovh << 'ENDSSH'
    # Aller dans le répertoire du projet
    cd /path/to/LightRAG

    # Construire l'image Docker
    microk8s ctr images build \
        -t lightrag-rabbitmq-consumer:latest \
        -f rabbitMQ/docker/Dockerfile.rabbitmq_consumer .

    # Créer les secrets (à adapter selon votre configuration)
    microk8s kubectl create secret generic rabbitmq-credentials \
        --from-literal=host=rabbitmq.example.com \
        --from-literal=port=5672 \
        --from-literal=username=your_username \
        --from-literal=password=your_password

    microk8s kubectl create secret generic openai-credentials \
        --from-literal=api_key=your_openai_api_key

    # Déployer le pod
    microk8s kubectl apply -f yaml/k8s_rabbitmq_consumer.yaml

    # Vérifier le déploiement
    microk8s kubectl get pods
ENDSSH

echo "Déploiement terminé sur le VPS-OVH"
