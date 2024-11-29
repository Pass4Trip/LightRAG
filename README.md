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

Créez un fichier `.env` à la racine du projet :

```env
# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=votre_mot_de_passe

# RabbitMQ
RABBITMQ_USER=rabbitmq
RABBITMQ_PASSWORD=votre_mot_de_passe
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# OpenAI/OVH
OPENAI_API_KEY=votre_clé_api
```

## Dépendances Principales

Le projet utilise plusieurs bibliothèques essentielles :
- accelerate >= 0.25.0
- aioboto3 >= 11.3.0
- hnswlib >= 0.7.0
- nano-vectordb >= 0.0.4
- ollama >= 0.1.6
- openai >= 1.3.7
- transformers >= 4.36.1
- neo4j >= 5.14.0
- pika >= 1.3.2

## Composants Principaux

### 1. Traitement des Messages RabbitMQ (`examples/lightrag_openai_compatible_demo_rabbitmq.py`)

Ce composant :
- Consomme les messages de la queue RabbitMQ
- Traite les données des restaurants
- Normalise les labels pour Neo4j
- Insère les documents dans LightRAG

### 2. Intégration Neo4j

- Stockage des relations entre entités
- Labels normalisés pour les nœuds
- Structure graphe optimisée pour les requêtes

### 3. Visualisation du Graphe (`examples/graph_visual_with_html.py`)

- Génère une visualisation interactive du graphe de connaissances
- Affiche les relations entre restaurants et attributs
- Nœuds colorés par type d'entité
- Export au format HTML

### 4. Analyse avec NetworkX (`examples/networkX.py`)

- Construction d'une base de graphes en mémoire
- Analyse des relations et de la structure
- Export en format GraphML

## Points Restants à Traiter

- Certaines entités générées ne possèdent pas de connexion (**edge**)
- Des hallucinations peuvent apparaître dans certaines réponses
- ⚠️ Implémentation de la personnalisation via `addon_params` à corriger
- Optimisation possible des prompts pour améliorer la qualité de l'extraction
- Gestion des erreurs RabbitMQ et reconnexion automatique
- Validation des données avant insertion dans Neo4j

## Installation avec UV (Recommandé)

UV est un gestionnaire de paquets Python ultra-rapide écrit en Rust. Pour installer le projet avec UV :

1. Installer UV :
   ```bash
   # macOS / Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Cloner le projet et se placer dans le répertoire :
   ```bash
   git clone https://github.com/MyBoun/LightRAG.git
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
