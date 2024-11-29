# LightRAG

LightRAG est une implémentation légère de RAG avec intégration RabbitMQ.

## Prérequis

- Python >= 3.9
- UV (gestionnaire de paquets Python)

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

## Dépendances Principales

Le projet utilise plusieurs bibliothèques essentielles :
- accelerate >= 0.25.0
- aioboto3 >= 11.3.0
- hnswlib >= 0.7.0
- nano-vectordb >= 0.0.4
- ollama >= 0.1.6
- openai >= 1.3.7
- transformers >= 4.36.1

## Utilisation du Code Python `examples/lightrag_openai_compatible_demo.py`

- **Modèle** : API OVH compatible OpenAI
- **Source de données** : Extraction de la base `Myboun`, incluant les informations et les résumés des restaurants.
- **Résultat** : Les données sont déposées dans le répertoire `WORKING_DIR = "./restaurant_openai_p4t_test"`.
- **Personnalisation** :
  - ⚠️ Note importante : La personnalisation via `addon_params` ne fonctionne pas actuellement
  - Pour personnaliser l'extraction d'entités, modifiez directement les valeurs dans `lightrag/prompt.py` :
    - `DEFAULT_ENTITY_TYPES` : types d'entités (restaurant, cuisine, prix, etc.)
    - `entity_extraction` : prompt d'extraction adapté aux restaurants
  - Une mise à jour future permettra l'utilisation de `addon_params`
- **Fonctionnement** :
  - La partie non commentée du code crée la base vectorielle et les fichiers JSON.
  - Le script est conçu pour un traitement incrémental des données.
  - La partie commentée permet de lancer des requêtes sur les restaurants.
- **Configuration** :
  - Nécessite un token OVH API (à stocker dans un fichier `.env`)
  - Compatible avec les endpoints OVH pour les embeddings et le LLM

## Utilisation du Code Python `examples/graph_visual_with_html.py`

- **Objectif** : Générer une visualisation interactive du graphe de connaissances.
- **Sortie** : Le fichier HTML est créé dans `examples/knowledge_graph.html`.
- **Visualisation** : 
  - Affiche les relations entre les restaurants et leurs attributs
  - Les nœuds sont colorés selon leur type d'entité
  - Les arêtes montrent les relations avec leur force

## Analyse du Graphe avec `examples/networkX.py`

- **Création** : Construction d'une base de graphes en mémoire avec **NetworkX**.
- **Analyse** : Permet d'explorer les relations et la structure du graphe.
- **Export** : Le graphe peut être exporté en format GraphML pour d'autres analyses.

## Points Restants à Traiter

- Certaines entités générées ne possèdent pas de connexion (**edge**).
- Des hallucinations peuvent apparaître dans certaines réponses.
- ⚠️ Implémentation de la personnalisation via `addon_params` à corriger
- Optimisation possible des prompts pour améliorer la qualité de l'extraction.

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
   # Installation en mode développement
   uv pip install -e ".[dev]"
   
   # OU installation simple
   uv pip install -e .
   ```

Les dépendances sont gérées via le fichier `pyproject.toml`. UV assure une installation rapide et déterministe des paquets.

## Configuration

1. Créer un fichier `.env` à la racine du projet
2. Ajouter votre token OVH API :
   ```
   OVH_AI_ENDPOINTS_ACCESS_TOKEN=votre_token_ici
   ```
3. Le fichier `.env` est ignoré par git pour la sécurité
