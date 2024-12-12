# Milvus Docker Setup

Ce répertoire contient la configuration Docker pour Milvus ainsi que des scripts Python utilitaires pour tester et gérer les collections.

## Configuration

Le fichier `docker-compose.yml` configure trois services :
- `etcd` : Pour la gestion des métadonnées
- `minio` : Pour le stockage d'objets
- `standalone` : Le serveur Milvus en mode standalone

## Démarrage des services

```bash
docker compose up -d
```

## Scripts Python utilitaires

### 1. Test de connexion (`test_milvus.py`)

Ce script vérifie simplement la connexion à Milvus et affiche les collections existantes.

```bash
python test_milvus.py
```

Exemple de sortie :
```
 Connexion à Milvus réussie!
Collections existantes:
[]
Déconnexion réussie!
```

### 2. Création d'une collection de test (`create_collection.py`)

Ce script crée une collection de test avec des embeddings aléatoires et effectue une recherche de similarité.

```bash
python create_collection.py
```

Exemple de sortie :
```
 Connecté à Milvus
 Collection 'test_collection' créée
 Index créé
 3 documents insérés

Résultats de la recherche:
ID: 454561115562312775, Distance: 19.345123291015625, Texte: Deuxième document pour l'exemple
ID: 454561115562312776, Distance: 21.495853424072266, Texte: Troisième document avec des embeddings
```

### 3. Suppression d'une collection (`delete_collection.py`)

Ce script permet de supprimer une collection spécifique.

```bash
python delete_collection.py test_collection
```

Exemple de sortie :
```
 Connecté à Milvus
 Collection 'test_collection' supprimée avec succès
 Déconnexion réussie
```

## Structure des données

La collection de test créée contient :
- Un ID auto-généré
- Un champ texte (VARCHAR)
- Un vecteur d'embedding de dimension 128

## Arrêt des services

```bash
docker compose down
```

Pour arrêter et supprimer tous les conteneurs, y compris les orphelins :
```bash
docker compose down --remove-orphans
```