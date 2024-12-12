# MongoDB Docker Setup

Cette configuration Docker inclut :
- MongoDB (dernière version)
- Mongo Express (interface web d'administration)

## Configuration

Le fichier `docker-compose.yml` configure deux services :
- `mongodb` : Le serveur MongoDB
- `mongo-express` : Interface web d'administration

## Identifiants par défaut

### MongoDB
- Username : root
- Password : root
- Port : 27017
- URI de connexion : mongodb://root:root@localhost:27017/

### Mongo Express (Interface Web)
- URL : http://localhost:8081
- Username : admin
- Password : admin123

## Commandes

### Démarrer les services
```bash
docker compose up -d
```

### Arrêter les services
```bash
docker compose down
```

### Vérifier les logs
```bash
# Tous les services
docker compose logs

# MongoDB uniquement
docker compose logs mongodb

# Mongo Express uniquement
docker compose logs mongo-express
```

## Structure des données
Les données MongoDB sont persistées dans le dossier `./data/db`

## Utilisation avec LightRAG
La configuration est déjà alignée avec les paramètres par défaut de LightRAG :
```python
MONGO_URI = "mongodb://root:root@localhost:27017/"
MONGO_DATABASE = "LightRAG"
```
