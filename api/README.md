# LightRAG Insert Service

## 📝 Description
Microservice pour l'insertion de données via RabbitMQ et LightRAG.

## 🚀 Fonctionnalités
- Consommation asynchrone de messages RabbitMQ
- Insertion de données avec LightRAG
- Déploiement Kubernetes

## 🔧 Configuration
Configuré via variables d'environnement :
- `RABBITMQ_HOST`
- `RABBITMQ_PORT`
- `RABBITMQ_USER`
- `RABBITMQ_PASSWORD`

## 🐳 Déploiement Microk8s

### Construction de l'image
```bash
docker build -t lightrag-insert:v1 .
```

### Déploiement
```bash
./deploy_lightrag_insert.sh
```

### Gestion du pod
```bash
# Mettre à l'échelle à zéro
microk8s kubectl scale deployment lightrag-insert --replicas=0

# Redémarrer
microk8s kubectl scale deployment lightrag-insert --replicas=1
```

## 🐳 Déploiement Docker Local

### Prérequis
- Docker installé
- Clé API OpenAI (optionnelle mais recommandée pour les embeddings)

### Déploiement standard
```bash
./deploy_lightrag.sh
```

### Déploiement avec clé API OpenAI
```bash
# Option 1 : Exporter la variable avant le déploiement
export OPENAI_API_KEY=votre_clé_api_openai
./deploy_lightrag.sh

# Option 2 : Passer la clé directement
OPENAI_API_KEY=votre_clé_api_openai ./deploy_lightrag.sh
```

#### Notes importantes
- La clé API OpenAI est passée dynamiquement lors du déploiement
- Si aucune clé n'est fournie, certaines fonctionnalités utilisant des embeddings seront limitées
- Ne partagez jamais votre clé API publiquement

## 🚨 Notes
- Utilise des secrets Kubernetes
- Écoute en continu les messages RabbitMQ
