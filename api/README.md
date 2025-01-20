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

## 🚨 Notes
- Utilise des secrets Kubernetes
- Écoute en continu les messages RabbitMQ
