# Fork du Répo LightRAG

## Utilisation du Code Python `examples/lightrag_openai_demo.py`

- **Modèle** : OpenAI avec **GPT4oMini**.
- **Source de données** : Extraction de la base `Myboun`, incluant les informations et les résumés.
- **Résultat** : Les données sont déposées dans le répertoire `WORKING_DIR = "./restaurant_openai_p4t_test"`.
- **Fonctionnement** :
  - La partie non commentée du code crée uniquement la base vectorielle et les fichiers JSON.
  - Le script est conçu pour ne traiter que les données non encore intégrées, permettant un ajout **incrémental**.
  - La partie commentée permet de lancer une question.
- **Extraction** : Ce fichier utilise `lightrag/prompt.py` pour réaliser l'extraction.

## Utilisation du Code Python `examples/graph_visual_with_html.py`

- **Objectif** : Générer un fichier HTML représentant le graphe.
- **Sortie** : Le fichier HTML est créé dans `examples/knowledge_graph.html`.

## Analyse du Graphe avec `examples/networkX.py`

- **Création** : Construction d'une base de graphes en mémoire avec **NetworkX** pour analyser le graphe.

## Points Restants à Traiter

- Certaines entités générées ne possèdent pas de connexion (**edge**).
- Des hallucinations semblent présentes dans certaines réponses.
