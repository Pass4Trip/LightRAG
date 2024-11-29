# Déploiement de LightRAG sur MicroK8s existant

Ce guide détaille les étapes pour déployer LightRAG sur une infrastructure MicroK8s existante avec PostgreSQL, Neo4j, RabbitMQ et Prefect Worker déjà configurés.

## 1. Prérequis

Les services suivants doivent être déjà en place et fonctionnels :
- PostgreSQL (pgsql-service:5432)
- Neo4j (p4t-neo4j:7687)
- RabbitMQ (rabbitmq:5672)
- Prefect Worker

### Configuration du VPS OVH
- Un VPS avec au moins 4GB de RAM et 2 vCPUs
- Ubuntu 20.04 LTS ou plus récent
- Un nom de domaine pointant vers votre VPS (optionnel mais recommandé)
- Ports ouverts dans le pare-feu OVH :
  - 16443 (API Kubernetes)
  - 80/443 (pour les services web)
  - 32000 (registry local)

### Installation de MicroK8s
```bash
# Installation de MicroK8s
sudo snap install microk8s --classic --channel=1.28/stable

# Configuration des permissions
sudo usermod -a -G microk8s $USER
sudo chown -R $USER ~/.kube
newgrp microk8s

# Activation des addons nécessaires
microk8s enable dns
microk8s enable storage
microk8s enable registry
microk8s enable ingress
```

## 2. Préparation de l'Image Docker

### Dockerfile pour LightRAG
```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["python", "examples/lightrag_openai_compatible_demo.py"]
```

### Construction et Push de l'Image
```bash
# Construire l'image
docker build -t localhost:32000/lightrag:latest .

# S'assurer que le registry est accessible
microk8s kubectl port-forward -n container-registry service/registry 32000:5000 --address 0.0.0.0 &

# Pousser vers le registry local MicroK8s
docker push localhost:32000/lightrag:latest
```

## 3. Configuration Kubernetes pour LightRAG

### LightRAG Deployment (lightrag.yaml)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lightrag
spec:
  replicas: 1
  selector:
    matchLabels:
      app: lightrag
  template:
    metadata:
      labels:
        app: lightrag
    spec:
      containers:
      - name: lightrag
        image: localhost:32000/lightrag:latest
        imagePullPolicy: Always
        env:
        - name: POSTGRES_HOST
          value: pgsql-service
        - name: POSTGRES_PORT
          value: "5432"
        - name: NEO4J_HOST
          value: p4t-neo4j
        - name: NEO4J_PORT
          value: "7687"
        - name: RABBITMQ_HOST
          value: rabbitmq
        - name: RABBITMQ_PORT
          value: "5672"
        - name: OVH_AI_ENDPOINTS_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: ovh-secrets
              key: api-token
        volumeMounts:
        - name: lightrag-data
          mountPath: /app/data
        resources:
          requests:
            memory: "512Mi"
            cpu: "200m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: lightrag-data
        persistentVolumeClaim:
          claimName: lightrag-pvc
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lightrag-pvc
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: microk8s-hostpath
  resources:
    requests:
      storage: 10Gi
```

## 4. Déploiement

### Configuration du Token OVH
```bash
# Créer le secret pour le token OVH
microk8s kubectl create secret generic ovh-secrets \
  --from-literal=api-token='votre-token-ovh'
```

### Déploiement de LightRAG
```bash
# Appliquer la configuration
microk8s kubectl apply -f lightrag.yaml
```

## 5. Vérification

### Vérifier le Déploiement
```bash
# Vérifier le statut du pod
microk8s kubectl get pods -l app=lightrag

# Consulter les logs
microk8s kubectl logs -f deployment/lightrag
```

## 6. Maintenance

### Mise à Jour de LightRAG
```bash
# Reconstruire et pousser la nouvelle image
docker build -t localhost:32000/lightrag:latest .
microk8s kubectl port-forward -n container-registry service/registry 32000:5000 --address 0.0.0.0 &
docker push localhost:32000/lightrag:latest

# Redémarrer le déploiement
microk8s kubectl rollout restart deployment lightrag
```

### Sauvegarder les Données
```bash
# Sauvegarder le PVC
microk8s kubectl get pvc lightrag-pvc -o yaml > lightrag-pvc-backup.yaml
```

## 7. Troubleshooting

### Logs et Diagnostics
```bash
# Voir les logs détaillés
microk8s kubectl logs -f deployment/lightrag

# Décrire le pod pour les événements
microk8s kubectl describe pod -l app=lightrag

# Vérifier la connectivité avec les services
microk8s kubectl exec -it deployment/lightrag -- curl -v pgsql-service:5432
microk8s kubectl exec -it deployment/lightrag -- curl -v p4t-neo4j:7687
microk8s kubectl exec -it deployment/lightrag -- curl -v rabbitmq:5672
```

## 8. Optimisation pour VPS OVH

### Monitoring des Ressources
```bash
# Installation de metrics-server
microk8s enable metrics-server

# Vérification de l'utilisation des ressources
microk8s kubectl top nodes
microk8s kubectl top pods
```

### Sécurité
```bash
# Configuration du pare-feu UFW
sudo ufw allow 16443/tcp  # API Kubernetes
sudo ufw allow 80/tcp     # HTTP
sudo ufw allow 443/tcp    # HTTPS
sudo ufw allow 32000/tcp  # Registry local

# Activation du pare-feu
sudo ufw enable
```

### Sauvegarde Automatique
```bash
# Installation de k8s-snapshots pour les sauvegardes automatiques des PVCs
microk8s kubectl apply -f https://raw.githubusercontent.com/k8s-snapshots/k8s-snapshots/master/deploy/k8s-snapshots.yaml
