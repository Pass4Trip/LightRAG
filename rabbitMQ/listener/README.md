# RabbitMQ Listener

## 📝 Description
Un microservice de listener RabbitMQ conçu pour consommer et traiter des messages à partir d'une file d'attente spécifique.

## 🚀 Fonctionnalités
- Connexion dynamique à un serveur RabbitMQ
- Écoute sur une queue configurable
- Support des messages JSON
- Logging détaillé avec des emojis 🎉

## 🔧 Configuration
Les paramètres sont configurables via des variables d'environnement :

| Variable | Description | Défaut |
|----------|-------------|--------|
| `RABBITMQ_HOST` | Adresse du serveur RabbitMQ | `51.77.200.196` |
| `RABBITMQ_PORT` | Port du serveur RabbitMQ | `30645` |
| `RABBITMQ_USER` | Nom d'utilisateur RabbitMQ | `rabbitmq` |
| `RABBITMQ_PASSWORD` | Mot de passe RabbitMQ | `mypassword` |
| `RABBITMQ_QUEUE` | Nom de la queue à écouter | `queue_vinh_test` |

## 🐳 Déploiement
Déployé via Kubernetes sur Microk8s avec un script de déploiement personnalisé.

## 🔄 Gestion du Pod

### Mise en pause du listener
Pour mettre en pause le listener RabbitMQ :
```bash
# Mettre à l'échelle à zéro (arrêter)
microk8s kubectl scale deployment rabbitmq-listener --replicas=0
```

### Redémarrage du listener
Pour redémarrer le listener :
```bash
# Relancer le déploiement
microk8s kubectl scale deployment rabbitmq-listener --replicas=1
```

### Vérification du statut
```bash
# Voir les pods
microk8s kubectl get pods -l app=rabbitmq-listener
```

## 📦 Dépendances
- Python 3.10
- Pika 1.3.2

## 🔍 Comportement
- Reçoit des messages JSON
- Log chaque message reçu
- Gestion des erreurs avec acquittement/rejet des messages

## 🛠️ Développement
```bash
# Installation des dépendances
pip install -r requirements.txt

# Lancement local
python rabbitmq_listener.py
```

## 🚨 Notes
- Configuré pour un environnement de développement
- Utilise des secrets Kubernetes pour la gestion des credentials
- Écoute en continu sur la queue RabbitMQ
