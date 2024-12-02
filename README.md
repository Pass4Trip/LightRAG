# LightRAG

LightRAG est une implémentation légère de RAG (Retrieval-Augmented Generation) avec intégration Neo4j et RabbitMQ.

## Prérequis

- Python >= 3.9
- UV (gestionnaire de paquets Python)
- Neo4j (base de données graphe)
- RabbitMQ (message broker)

## Installation Rapide

Un script d'installation automatique est disponible :

```bash
# Exécuter le script d'installation
./setup_uv_env.sh
```

Ce script :
- Installe UV si nécessaire
- Crée un environnement virtuel
- Installe toutes les dépendances

## Services Requis

### Neo4j
- **Installation** : Suivez les instructions sur [neo4j.com](https://neo4j.com/download/)
- **Configuration** :
  - Créez une base de données
  - Notez les identifiants (URI, utilisateur, mot de passe)
  - Configurez ces informations dans votre fichier `.env`

### RabbitMQ
- **Installation** : Suivez les instructions sur [rabbitmq.com](https://www.rabbitmq.com/download.html)
- **Configuration** :
  - Le serveur doit être accessible sur le port 5672
  - Configurez les identifiants dans votre fichier `.env`

## Configuration

### Gestion des Secrets avec Prefect Blocks

Le projet utilise Prefect Blocks pour gérer les secrets et les configurations de manière sécurisée :

1. **OVH Credentials Block**
   - Stocke le token d'accès à l'API LLM d'OVH
   - Nom du block : "ovh-credentials"
   ```python
   OVHCredentials(
       llm_api_token="votre_token_ovh"
   )
   ```

2. **RabbitMQ Credentials Block**
   - Stocke les identifiants de connexion RabbitMQ
   - Nom du block : "rabbitmq-credentials"
   ```python
   RabbitMQCredentials(
       username="votre_username",
       password="votre_password",
       host="votre_host",
       port="votre_port"
   )
   ```

3. **Neo4j Credentials Block**
   - Stocke les identifiants de connexion Neo4j
   - Nom du block : "neo4j-credentials"
   ```python
   Neo4jCredentials(
       uri="votre_uri",
       username="votre_username",
       password="votre_password"
   )
   ```

### Configuration des Modèles LLM OVH

Le projet utilise deux modèles d'OVH AI :

1. **LLM pour le traitement du texte**
   - Modèle : Meta-Llama-3_1-70B-Instruct
   - Endpoint : llama-3-1-70b-instruct.endpoints.kepler.ai.cloud.ovh.net

2. **Modèle d'Embedding**
   - Modèle : multilingual-e5-base
   - Endpoint : multilingual-e5-base.endpoints.kepler.ai.cloud.ovh.net
   - Dimension des embeddings : 768

## Composants Principaux

### 1. Traitement des Messages RabbitMQ (`examples/lightrag_openai_compatible_demo_rabbitmq.py`)

Ce composant est le cœur du système, gérant le traitement des données via RabbitMQ :

#### Fonctionnalités Principales
- **Consommation des Messages**
  - Connexion automatique à RabbitMQ avec gestion des reconnexions
  - Configuration et monitoring de la queue de messages
  - Traitement asynchrone des messages

- **Traitement des Données**
  - Normalisation des données restaurants pour Neo4j
  - Extraction intelligente des informations avec LLM
  - Génération automatique des labels et relations

- **Intégration LightRAG**
  - Insertion optimisée des documents dans la base
  - Gestion des relations entre entités
  - Structure de graphe optimisée pour les requêtes

#### Gestion des Erreurs
- Reconnexion automatique à RabbitMQ en cas de perte de connexion
- Retry pattern pour les appels API
- Logging détaillé pour le debugging

#### Monitoring
- Métriques sur le traitement des messages
- Logs en temps réel des opérations
- Statut des connexions RabbitMQ et Neo4j

### 2. Autres Composants

D'autres composants sont disponibles dans le dossier `examples/` pour la visualisation et l'analyse des données.

## Installation avec UV (Recommandé)

UV est un gestionnaire de paquets Python ultra-rapide écrit en Rust. Pour installer le projet avec UV :

1. Installer UV :
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Cloner le projet et se placer dans le répertoire :
   ```bash
   git clone -b feature/clean-start git@github.com:Pass4Trip/LightRAG.git
   cd LightRAG
   ```

3. Créer et activer l'environnement virtuel avec UV :
   ```bash
   # Créer l'environnement
   uv venv
   
   # Activer l'environnement (Linux/macOS)
   source .venv/bin/activate
   ```

4. Installer les dépendances avec UV :
   ```bash
   uv pip install -r requirements.txt
   ```

## Déploiement avec MicroK8s

### Prérequis
- MicroK8s installé et configuré
- Registry local sur le port 32000
- Buildah pour la gestion des conteneurs

### 1. Construction de l'image
```bash
# Build de l'image avec optimisation
buildah build --layers --force-rm -t localhost:32000/lightrag:v5-prefect .

# Vérifier l'image
buildah images | grep lightrag

# Push vers le registry local
buildah push localhost:32000/lightrag:v5-prefect
```


### 2. Configuration Prefect et Déploiement

Si le déploiement existe déjà, mettez simplement à jour l'image :
```bash
microk8s kubectl set image deployment/lightrag lightrag=localhost:32000/lightrag:v5-prefect

```bash
# Créer le secret pour l'API Prefect
microk8s kubectl create secret generic prefect-secrets \
  --from-literal=PREFECT_API_KEY="XXX""

# Créer le ConfigMap pour la configuration
microk8s kubectl create configmap prefect-config \
  --from-file=/home/ubuntu/value_prefect_worker.yaml

# Créer le déploiement
microk8s kubectl create deployment lightrag \
  --image=localhost:32000/lightrag:v5-prefect

# Configurer les variables d'environnement
microk8s kubectl set env deployment/lightrag \
  PREFECT_ACCOUNT_ID=42cb0262-af09-4eb2-9d92-97142d7fcedd \
  PREFECT_WORKSPACE_ID=a0d5688e-41c6-4d18-bc27-294f7fd7a9e7 \
  --from=secret/prefect-secrets

  Version local : 
  export 
# Monter le ConfigMap dans le pod
microk8s kubectl patch deployment lightrag --patch '
{
  "spec": {
    "template": {
      "spec": {
        "volumes": [{
          "name": "config-volume",
          "configMap": {
            "name": "prefect-config"
          }
        }],
        "containers": [{
          "name": "lightrag",
          "volumeMounts": [{
            "name": "config-volume",
            "mountPath": "/home/ubuntu"
          }]
        }]
      }
    }
  }
}'
```

### 2.5 Configuration du Volume Persistant pour LightRAG
```bash
# Créer le fichier de configuration du volume persistant
cat > pv-lightrag-data.yaml << 'EOL'
apiVersion: v1
kind: PersistentVolume
metadata:
  name: lightrag-data-pv
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /home/ubuntu/lightrag_data

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: lightrag-data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
EOL

# Créer les dossiers nécessaires
sudo mkdir -p /home/ubuntu/lightrag_data/nano-vectorDB
sudo chown -R ubuntu:ubuntu /home/ubuntu/lightrag_data

# Appliquer la configuration
microk8s kubectl apply -f pv-lightrag-data.yaml

# Mettre à jour le déploiement pour utiliser le volume
microk8s kubectl patch deployment lightrag --patch '
{
  "spec": {
    "template": {
      "spec": {
        "volumes": [
          {
            "name": "config-volume",
            "configMap": {
              "name": "prefect-config"
            }
          },
          {
            "name": "lightrag-data",
            "persistentVolumeClaim": {
              "claimName": "lightrag-data-pvc"
            }
          }
        ],
        "containers": [{
          "name": "lightrag",
          "volumeMounts": [
            {
              "name": "config-volume",
              "mountPath": "/home/ubuntu"
            },
            {
              "name": "lightrag-data",
              "mountPath": "/data"
            }
          ]
        }]
      }
    }
  }
}'

# Redémarrer le déploiement pour appliquer les changements
microk8s kubectl rollout restart deployment lightrag
```

Cette configuration permet de persister les données de LightRAG dans `/home/ubuntu/lightrag_data/nano-vectorDB` sur le VPS, assurant ainsi que les données sont conservées même en cas de redémarrage du pod.

### 3. Vérification et Monitoring
```bash
# Vérifier le statut des pods
microk8s kubectl get pods -n default

# Voir les logs en temps réel
microk8s kubectl logs -f $(microk8s kubectl get pods -n default | grep lightrag | awk '{print $1}') -n default
```

### 4. Maintenance et Nettoyage
```bash
# Supprimer le déploiement
microk8s kubectl delete deployment lightrag -n default
microk8s kubectl delete configmap prefect-config
microk8s kubectl delete secret prefect-secrets

# Nettoyer les anciennes images
buildah rmi localhost:32000/lightrag:v4-prefect-fix2
buildah rmi --all  # Attention: supprime toutes les images

# Vérifier l'espace disque
df -h /var/snap/microk8s/common/
```

Note : Il est recommandé de nettoyer régulièrement les anciennes images pour libérer de l'espace disque.
