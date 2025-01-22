# Répertoire actif : /Users/vinh/Documents/Prefect

# LightRAG

LightRAG est avec intégration RabbitMQ, Neo4J (graphDB), Milvus (vectorDB), MongoDB (kvDB)

## Table des Matières
1. [Prérequis](#prérequis)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Architecture](#architecture)
5. [Déploiement](#déploiement)
6. [Stockage des Données](#stockage-des-données)
7. [Dépannage](#dépannage)

## Prérequis

- Python >= 3.9
- UV (gestionnaire de paquets Python)
- Neo4j (base de données graphe) >> version OVH microk8s
- Milvus (base de données vectorielle) >> version local Docker
- MongoDB (base de données key-value) >> version local Docker
- RabbitMQ (message broker) >> version OVH microk8s
- Kubernetes (microk8s) >> version OVH 

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

### Installation serveur OVH

- Clone le repo

- Build docker image
```bash
docker build --tag localhost:32000/lightrag-api:v1 .
```
- Deploy pod
```bash
kubectl apply -f api/lightrag_deployment.yaml
```
- Deploy ingress
```bash
kubectl apply -f api/lightrag-api-ingress.yaml
```

## Configuration

### Services Requis

#### Neo4j
- **Port** : 7687 (Bolt), exposé sur le port 32719
- **Credentials** : Configurés via Neo4j Credentials Block

#### RabbitMQ
- **Port** : 5672, exposé sur le port 30645
- **Credentials** : Configurés via RabbitMQ Credentials Block

#### Milvus
- **Port** : 19530
- **Base de données** : `lightrag` (doit être configurée via la variable d'environnement `MILVUS_DB_NAME`)
- **Collections** : 
  - `relationships` : stocke les relations entre les entités
  - `chunks` : stocke les chunks de texte vectorisés
  - `entities` : stocke les entités extraites
- **Configuration** :
  ```python
  # Variables d'environnement requises
  MILVUS_URI="tcp://localhost:19530"  # URI de connexion
  MILVUS_DB_NAME="lightrag"           # Nom de la base de données
  ```

#### MongoDB
- **Port** : 27017
- **Base de données** : `LightRAG` (attention à la casse)
- **Collections** : Créées automatiquement selon les besoins
- **Configuration** :
  ```env
  # Variables d'environnement requises
  MONGO_URI="mongodb://root:root@localhost:27017/"  # URI de connexion
  MONGO_DATABASE="LightRAG"                         # Nom de la base de données (sensible à la casse)
  ```

**Note importante** : Le nom de la base de données MongoDB est sensible à la casse. Assurez-vous d'utiliser exactement `LightRAG` (et non `lightrag` ou `Lightrag`).

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

## Organisation du projet

```
LightRAG/
├── examples/                    # Exemples d'utilisation
├── lightrag/                   # Package principal
├── local/                     # Versions locales des fichiers
│   └── llm.py                # Version légère sans torch/transformers
├── scripts/                   # Scripts de déploiement
│   ├── build.sh              # Construction de l'image
│   └── deploy.sh             # Déploiement sur le VPS
├── requirements.txt           # Dépendances Python
└── README.md                 # Documentation
```


### Scripts de déploiement

Le dossier `scripts/` contient les scripts nécessaires pour le déploiement :
- `build.sh` : Construction de l'image Docker
- `deploy.sh` : Déploiement complet sur le VPS

Pour déployer l'application :

```bash
# Rendre le script exécutable
chmod +x scripts/deploy.sh

# Exécuter le déploiement
./scripts/deploy.sh
```

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

prérequis : s'assurer que le github est actualisé avec les derniers commits

0. **Git clone de LightRAG**
ssh ubuntu@vps-ovh "rm -rf ~/lightrag && git clone https://github.com/Pass4Trip/LightRAG.git ~/lightrag"

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

### Script de Déploiement Automatisé

Un script `deploy.sh` est fourni pour automatiser le processus de déploiement complet :

```bash
# Rendre le script exécutable
chmod +x scripts/deploy.sh

# Exécuter le déploiement
./scripts/deploy.sh
```

Ce script effectue automatiquement :
1. Suppression et re-clonage du code source
2. Construction de l'image avec buildah
3. Push de l'image vers le registry local
4. Application des configurations Kubernetes
5. Redémarrage du pod pour prendre en compte les changements

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

### Structure des Données

Les fichiers stockés incluent :
- `kv_store_full_docs.json` : Documents complets
- `kv_store_text_chunks.json` : Chunks de texte
- `kv_store_llm_response_cache.json` : Cache des réponses LLM
- `vdb_chunks.json` : Données vectorielles des chunks
- `vdb_entities.json` : Entités extraites
- `vdb_relationships.json` : Relations entre entités
- `lightrag.log` : Fichier de logs


### 3. Configuration du pyproject.toml

Modifiez votre `pyproject.toml` pour retirer la dépendance à `lightrag-hku` puisque vous utilisez la version locale :

```toml
[tool.poetry.dependencies]
python = "^3.9"
# Retirer ou commenter la ligne suivante :
# lightrag-hku = "^0.1.0"
```

### 4. Mise à jour des Requirements

Régénérez votre `requirements.txt` pour refléter les changements :

```bash
uv pip freeze > requirements.txt
```s instructions pour notre cas d'usage

### 6. Configuration de l'API OVH

Pour utiliser les modèles OVH AI :

1. Configurez votre token OVH AI dans `.env` :
```bash
OVH_LLM_API_TOKEN=votre_token_ici
```

2. Les endpoints sont configurés dans le code :
- LLM : `llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net`
- Embeddings : `multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net`

### 7. Tests

Vous pouvez tester la connexion aux API OVH avec :

```bash
python tests/test_connexion_api_llm_ovh.py
```

### 8. Développement

Toute modification dans `local_source/LightRAG/lightrag/` sera immédiatement prise en compte grâce à l'installation en mode éditable.

## Développement Local

### Structure du Projet

```
LightRAG/
├── lightrag/                 # Package principal
│   ├── __init__.py           # Point d'entrée du package
│   ├── lightrag.py           # Classe principale LightRAG
│   ├── base.py               # Classes de base
│   ├── llm.py                # Fonctions de traitement LLM
│   ├── operate.py            # Opérations de traitement
│   ├── kg/                   # Modules de gestion de graphes de connaissances
│   └── utils.py              # Utilitaires
├── examples/                 # Exemples d'utilisation
└── requirements.txt          # Dépendances du projet
```

### Configuration pour le Développement Local

Pour développer et tester localement :

1. Clonez le dépôt
2. Créez un environnement virtuel
3. Installez les dépendances
4. Ajoutez le chemin du projet au PYTHONPATH

```bash
# Exemple de configuration
git clone https://github.com/votre-repo/LightRAG.git
cd LightRAG

# Création de l'environnement virtuel
python -m venv .venv
source .venv/bin/activate

# Installation des dépendances
pip install -r requirements.txt

# Pour l'import local, ajoutez au début de vos scripts
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

### Imports dans le Code

Pour importer LightRAG dans vos scripts :

```python
from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm import gpt_4o_mini_complete
from lightrag.utils import EmbeddingFunc
```

### Résolution des Problèmes

- Assurez-vous que le dossier parent est dans le PYTHONPATH
- Vérifiez que tous les modules sont correctement importés
- Utilisez des imports absolus de préférence

### Vérification de l'Import Local

Pour vérifier que vous utilisez bien la version locale de LightRAG, vous pouvez créer un script de test :

```python
import sys
from pathlib import Path

# Add local LightRAG source to Python path
sys.path.insert(0, str(Path.cwd()))

import lightrag
print('Chemin de lightrag:', lightrag.__file__)
```

La sortie devrait indiquer que lightrag est importé depuis votre dossier local :
```bash
Chemin de lightrag: /Users/vinh/Documents/LightRAG/lightrag/__init__.py
```

Si vous voyez un chemin différent (par exemple dans site-packages), cela signifie que vous utilisez une version installée du package au lieu de la version locale.



### Personnalisation de la lib LightRAG

Les fichiers principalement modifiés sont :

operate.py 

/Users/vinh/Documents/LightRAG/lightrag/kg/milvus_impl.py
Correction d'une faute de frappe : MilvusVectorDBStorge → MilvusVectorDBStorage
Ajout de méthodes pour gérer la création de bases de données Milvus
Amélioration de la gestion des connexions et des bases de données

/Users/vinh/Documents/LightRAG/lightrag/lightrag.py
Mise à jour des références à MilvusVectorDBStorge pour utiliser MilvusVectorDBStorage

/Users/vinh/Documents/LightRAG/lightrag/prompt.py (mentionné précédemment)


**Note Importante :** Dans ce projet, nous avons modifié directement le fichier `prompt.py` de la bibliothèque LightRAG en local. Cette approche nous permet de :

- Personnaliser finement les prompts d'extraction d'entités
- Adapter le comportement de l'IA à nos besoins spécifiques
- Expérimenter rapidement avec différentes configurations de prompts

Les modifications incluent :
- Ajustement des prompts d'extraction d'entités
- Personnalisation des exemples et du contexte
- Adaptation du langage et de



## Architecture et Stockage

LightRAG utilise plusieurs technologies de stockage pour différents aspects de son système :

### Bases de Données

1. **MongoDB** 
   - Stockage clé-valeur 
   - Utilisé pour :
     - Cache des réponses LLM
     - Stockage des documents complets
     - Stockage des chunks de texte
   - Configuration détaillée : [mongodb_docker/README.md](mongodb_docker/README.md)

2. **Milvus**
   - Stockage vectoriel
   - Utilisé pour :
     - Indexation et recherche vectorielle
     - Stockage des embeddings
   - Configuration détaillée : [milvus_docker/README.md](milvus_docker/README.md)

3. **Neo4j**
   - Base de données de graphe
   - Utilisé pour :
     - Modélisation des relations entre entités
     - Requêtes de graphe complexes
   - Configuration détaillée : [neo4j_docker/README.md](neo4j_docker/README.md)

### Outils de Développement

- **Docker Compose** utilisé pour la gestion des conteneurs
- **Mongo Express** pour la visualisation des données MongoDB
- **Volumes persistants** pour la conservation des données entre les redémarrages

### Prérequis

- Docker
- Docker Compose
- Python 3.10+

### Démarrage Rapide

1. Cloner le dépôt
2. Installer les dépendances : `pip install -r requirements.txt`
3. Démarrer les conteneurs : `docker-compose up -d`
4. Exécuter les exemples : `python examples/lightrag_openai_demo.py`

### Documentation Détaillée

Pour plus d'informations sur chaque composant, consultez les README spécifiques dans chaque dossier de configuration.

## Dépannage

### Problèmes avec Milvus

1. **Collections vides ou non visibles**
   - Vérifiez que la variable d'environnement `MILVUS_DB_NAME` est définie sur "lightrag"
   - Utilisez le script `milvus_docker/test_milvus_connection.py` pour vérifier la connexion et lister les collections
   ```bash
   python3 milvus_docker/test_milvus_connection.py
   ```

2. **Warning "All chunks are already in the storage"**
   - Ce message indique que les documents sont déjà présents dans la base de données
   - Pour réinsérer les documents, vous devez d'abord les supprimer de la collection

3. **Erreur de connexion**
   - Vérifiez que Milvus est en cours d'exécution : `docker ps | grep milvus`
   - Vérifiez l'URI de connexion (par défaut : tcp://localhost:19530)
   - Assurez-vous que le port 19530 est accessible

### Problèmes avec RabbitMQ

1. **Erreur de connexion**
   - Vérifiez les credentials dans la configuration
   - Assurez-vous que le service est accessible sur le port configuré (30645)
   - Vérifiez les logs pour plus de détails sur l'erreur

### Problèmes avec Neo4j

1. **Erreur de connexion**
   - Vérifiez l'URI et les credentials dans la configuration
   - Assurez-vous que le service est accessible sur le port configuré (32719)
   - Vérifiez que la base de données existe et est active

## Branches Spéciales

### 🔬 clean-neo4j_milvus_mongodb_fineTune

**Version Fine-Tuned de LightRAG**

Cette branche représente une version améliorée et optimisée de LightRAG, avec un focus sur :

- 🧠 **Extraction d'Entités Avancée** 
  - Amélioration des prompts pour les domaines `user` et `activity`
  - Génération systématique de relations entre entités
  - Stratégies d'extraction plus dynamiques et contextuelles

- 🔗 **Intégration Multi-Base de Données**
  - Optimisation des interactions entre Neo4j, Milvus et MongoDB
  - Stratégies de modélisation de graphe plus flexibles
  - Amélioration de la cohérence des données entre différents systèmes de stockage

- 🚀 **Performance et Fine-Tuning**
  - Réduction de la redondance dans l'extraction d'entités
  - Amélioration de la précision des embeddings
  - Optimisation des requêtes inter-bases de données

#### Principaux Changements
- Refactoring des prompts d'extraction d'entités
- Ajout de scripts utilitaires pour la gestion des bases de données
- Amélioration de la modularité du code
- Correction de bugs mineurs

**⚠️ Note**: Cette branche est en cours de développement et de test. Utilisez-la avec précaution.
