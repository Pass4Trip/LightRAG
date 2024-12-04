# LightRAG

LightRAG est une implémentation légère de RAG (Retrieval-Augmented Generation) avec intégration Neo4j et RabbitMQ.

## Table des Matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Architecture](#architecture)
5. [Déploiement](#déploiement)
6. [Stockage des Données](#stockage-des-données)

## Prérequis

- Python >= 3.9
- UV (gestionnaire de paquets Python)
- Neo4j (base de données graphe)
- RabbitMQ (message broker)
- Kubernetes (microk8s)

## Installation

### Installation Rapide

```bash
# Exécuter le script d'installation
./setup_uv_env.sh
```

Ce script :
- Installe UV si nécessaire
- Crée un environnement virtuel
- Installe toutes les dépendances

### Installation avec UV (Recommandé)

UV est un gestionnaire de paquets Python ultra-rapide écrit en Rust :

```bash
# Installation de UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# Création de l'environnement virtuel
uv venv

# Activation de l'environnement
source .venv/bin/activate

# Installation des dépendances
uv pip install -r requirements.txt
```

## Configuration

### Services Requis

#### Neo4j
- **Port** : 7687 (Bolt), exposé sur le port 32719
- **Credentials** : Configurés via Neo4j Credentials Block

#### RabbitMQ
- **Port** : 5672, exposé sur le port 30645
- **Credentials** : Configurés via RabbitMQ Credentials Block

### Gestion des Secrets avec Prefect Blocks

1. **OVH Credentials Block**
   ```python
   OVHCredentials(
       llm_api_token="votre_token_ovh"
   )
   ```

2. **RabbitMQ Credentials Block**
   ```python
   RabbitMQCredentials(
       username="votre_username",
       password="votre_password",
       host="votre_host",
       port="votre_port"
   )
   ```

3. **Neo4j Credentials Block**
   ```python
   Neo4jCredentials(
       uri="votre_uri",
       username="votre_username",
       password="votre_password"
   )
   ```

### Configuration des Modèles LLM OVH

1. **LLM pour le traitement du texte**
   - Modèle : Meta-Llama-3_1-70B-Instruct
   - Endpoint : llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net

2. **Modèle d'Embedding**
   - Modèle : multilingual-e5-base
   - Endpoint : multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net
   - Dimension des embeddings : 768

### Path Configuration Update

**Important Change**: As of the latest update, we've standardized the `VECTOR_DB_PATH` to `/app/data` across all environments. This ensures consistent data storage in both local and Kubernetes deployments.

- Local development: Uses a relative path to `nano-vectorDB`
- Kubernetes/microk8s: Uses `/app/data` as the standard vector database path

## Architecture

### Composants Principaux

1. **API REST**
   - Endpoints pour l'indexation et la recherche
   - Compatible avec l'API OpenAI

2. **Traitement des Messages**
   - Intégration RabbitMQ pour le traitement asynchrone
   - Gestion des reconnexions et monitoring

3. **Stockage**
   - Neo4j pour les graphes de connaissances
   - Stockage vectoriel local pour les embeddings

## Déploiement

### Prérequis Kubernetes
- MicroK8s installé et configuré
- Registry local sur le port 32000
- Buildah pour la construction d'images

### Construction et Déploiement de l'Image

1. **Construction de l'image**
```bash
# Build de l'image
buildah build --layers --force-rm -t localhost:32000/lightrag:v5-prefect .

# Vérification de l'image
buildah images | grep lightrag

# Push vers le registry local
buildah push localhost:32000/lightrag:v5-prefect
```

2. **Configuration des Secrets et ConfigMap**
```bash
# Suppression des secrets
microk8s kubectl delete secret lightrag-config 

# Création des secrets
microk8s kubectl create secret generic lightrag-secrets \
  --from-literal=RABBITMQ_PASSWORD=xxx \
  --from-literal=NEO4J_PASSWORD=xxx \
  --from-literal=OVH_LLM_API_TOKEN=xxx

# Suppression des ConfigMap
microk8s kubectl delete configmap lightrag-config 

# Création du ConfigMap
microk8s kubectl create configmap lightrag-config \
  --from-literal=NEO4J_URI=bolt://51.77.200.196:32719 \
  --from-literal=NEO4J_USERNAME=neo4j \
  --from-literal=PREFECT_ACCOUNT_ID=1de47cd9-a32e-4a43-8545-fd3bab9eaabe \
  --from-literal=PREFECT_WORKSPACE_ID=59349ca6-8f64-4b16-b768-5c70d28a342e \
  --from-literal=RABBITMQ_HOST=51.77.200.196 \
  --from-literal=RABBITMQ_PORT=30645 \
  --from-literal=RABBITMQ_USERNAME=rabbitmq \
  --from-literal=VECTOR_DB_PATH=/home/ubuntu/lightrag_data
```

3. **Configuration du Volume Persistant**
```bash
# Création du PV et PVC
cat << 'EOF' | microk8s kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: lightrag-data-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  storageClassName: microk8s-hostpath
  hostPath:
    path: /home/ubuntu/lightrag_data
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lightrag-vectordb-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: microk8s-hostpath
EOF

# Création du répertoire de données
mkdir -p /home/ubuntu/lightrag_data/nano-vectorDB
```

4. **Déploiement de l'Application**
```bash
# Application du déploiement
microk8s kubectl apply -f yaml/lightrag-deployment.yaml

# Mise à jour de l'image (si nécessaire)
microk8s kubectl set image deployment/lightrag lightrag=localhost:32000/lightrag:v5-prefect
```

5. **Vérification du Déploiement**
```bash
# Vérification des pods
microk8s kubectl get pods -l app=lightrag

# Consultation des logs
microk8s kubectl logs -f -l app=lightrag

# Vérification des volumes
microk8s kubectl get pv,pvc
```

6. **Maintenance**
```bash
# Redémarrage du déploiement
microk8s kubectl rollout restart deployment lightrag

# Suppression des anciennes images
buildah rmi localhost:32000/lightrag:old-tag

# Nettoyage complet (si nécessaire)
microk8s kubectl delete deployment lightrag
microk8s kubectl delete configmap lightrag-config
microk8s kubectl delete secret lightrag-secrets
microk8s kubectl delete pvc lightrag-vectordb-pvc
microk8s kubectl delete pv lightrag-data-pv
```

### Déploiement Kubernetes

```bash
# Déployer l'application
microk8s kubectl apply -f yaml/lightrag-deployment.yaml

# Mettre à jour l'image
microk8s kubectl set image deployment/lightrag lightrag=localhost:32000/lightrag:v5-prefect
```

### Secrets Kubernetes

```bash
# Créer les secrets
microk8s kubectl create secret generic lightrag-secrets \
  --from-literal=RABBITMQ_PASSWORD=xxx \
  --from-literal=NEO4J_PASSWORD=xxx \
  --from-literal=OVH_LLM_API_TOKEN=xxx
```

## Stockage des Données

### Volumes Persistants Kubernetes

Les données sont accessibles via trois chemins différents qui pointent tous vers le même emplacement physique :

```bash
# 1. Chemin simplifié via lien symbolique sur le VPS
~/lightrag_data/nano-vectorDB/

# 2. Chemin dans le stockage microk8s sur le VPS (emplacement physique)
/var/snap/microk8s/common/default-storage/default-lightrag-vectordb-pvc-pvc-6783594a-fcaa-42c5-a54c-15bd6de8415d/

# 3. Chemin dans le pod Kubernetes
/app/data/
```

Pour accéder aux données depuis votre Mac local :
```bash
# Via le lien symbolique (recommandé)
ssh ubuntu@vps-ovh "ls -l ~/lightrag_data/nano-vectorDB/"

# Via le chemin physique
ssh ubuntu@vps-ovh "sudo ls -l /var/snap/microk8s/common/default-storage/default-lightrag-vectordb-pvc-pvc-6783594a-fcaa-42c5-a54c-15bd6de8415d/"
```

Note: Les trois chemins sont synchronisés et les modifications faites via l'un des chemins sont immédiatement visibles dans les autres.

### Structure des Données

Les fichiers stockés incluent :
- `kv_store_full_docs.json` : Documents complets
- `kv_store_text_chunks.json` : Chunks de texte
- `kv_store_llm_response_cache.json` : Cache des réponses LLM
- `vdb_chunks.json` : Données vectorielles des chunks
- `vdb_entities.json` : Entités extraites
- `vdb_relationships.json` : Relations entre entités
- `lightrag.log` : Fichier de logs
