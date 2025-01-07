# Neo4j Backup Solution

Cette solution permet de synchroniser une base de données Neo4j entre un environnement de production (VPS) et un environnement local via Docker.

## 🏗️ Structure du Projet

```
neo4j_microk8s/
├── neo4j_backup.py        # Classe pour créer des backups Neo4j
├── neo4j_restore.py       # Classe pour restaurer des backups Neo4j
├── sync_to_local.py       # Script de synchronisation Production → Local
├── sync_to_prod.py        # Script de synchronisation Local → Production
└── backups/              # Dossier contenant les fichiers de backup
```

## 🚀 Installation

### Prérequis
- Docker
- Python 3.8+
- Neo4j en production (sur VPS)

### Installation des dépendances Python
```bash
pip install neo4j
```

### Configuration de Neo4j Local

1. Créer les dossiers pour les volumes :
```bash
mkdir -p neo4j-data neo4j-logs
```

2. Lancer le conteneur Neo4j :
```bash
docker run -d \
  --name neo4j-backup \
  -p 7475:7474 \
  -p 7688:7687 \
  -e NEO4J_AUTH=neo4j/testpassword123 \
  -v ./neo4j-data:/data \
  -v ./neo4j-logs:/logs \
  neo4j:5.13.0
```

L'interface web sera accessible sur http://localhost:7475

## 🔄 Synchronisation

### Production → Local (`sync_to_local.py`)

1. Configurer les variables d'environnement pour la production :
```bash
export NEO4J_URI="bolt://votre-vps:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="votre_mot_de_passe_prod"
```

2. Lancer la synchronisation :
```bash
python sync_to_local.py
```

### Local → Production (`sync_to_prod.py`)

⚠️ **Attention** : Cette opération écrase les données de production !

1. Configurer les variables d'environnement pour la production :
```bash
export NEO4J_URI="bolt://votre-vps:7687"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="votre_mot_de_passe_prod"
```

2. Lancer la synchronisation :
```bash
python sync_to_prod.py
```

Le script demandera une confirmation avant de procéder. Pour éviter la confirmation (scripts automatisés) :
```bash
python sync_to_prod.py --force
```

## 🔧 Architecture

### `neo4j_backup.py`
- Classe `Neo4jBackup` pour créer des sauvegardes
- Extrait tous les nœuds et relations
- Sauvegarde au format JSON avec métadonnées
- Utilise les variables d'environnement pour la connexion

### `neo4j_restore.py`
- Classe `Neo4jRestore` pour restaurer des sauvegardes
- Recrée les nœuds et relations avec préfixe "restore_"
- Maintient la cohérence des IDs
- Gère les erreurs et les logs

### Identifiants par défaut

Production (VPS) :
- URI : défini par `NEO4J_URI`
- Username : défini par `NEO4J_USERNAME`
- Password : défini par `NEO4J_PASSWORD`

Local (Docker) :
- URI : bolt://localhost:7688
- Interface web : http://localhost:7475
- Username : neo4j
- Password : testpassword123

## 📝 Notes

1. Les backups sont stockés dans le dossier `backups/` avec un timestamp
2. Les données restaurées ont le préfixe "restore_" pour éviter les conflits
3. Les volumes Docker persistent les données entre les redémarrages
4. Les logs détaillés sont disponibles pendant la synchronisation

## 🚨 Sécurité

- Ne jamais commiter les mots de passe ou variables d'environnement
- Toujours vérifier les données avant de synchroniser vers la production
- Faire des backups réguliers de la production
- Utiliser des mots de passe forts en production

## 🐛 Dépannage

1. Si le conteneur ne démarre pas :
```bash
docker stop neo4j-backup
docker rm neo4j-backup
# Puis relancer la commande docker run
```

2. Si les permissions sont incorrectes :
```bash
sudo chown -R 7474:7474 neo4j-data neo4j-logs
```

3. Pour voir les logs du conteneur :
```bash
docker logs -f neo4j-backup
```

4. Pour redémarrer le conteneur :
```bash
docker restart neo4j-backup
```
