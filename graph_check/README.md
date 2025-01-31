# Vérification d'Intégrité du Graphe Neo4j

## Description
Ce script permet de vérifier et réparer l'intégrité du graphe de connaissances Neo4j.

## Prérequis
- Python 3.8+
- Bibliothèques : 
  - `neo4j`
  - `asyncio`

## Installation des Dépendances
```bash
uv pip install neo4j
```

## Configuration
Assurez-vous de définir les variables d'environnement suivantes :
- `NEO4J_URI`
- `NEO4J_USERNAME`
- `NEO4J_PASSWORD`

## Utilisation

### Lancement Manuel
```bash
python graph_integrity.py
```

### Modes d'Exécution
1. **Validation** : Vérifie l'intégrité sans modifier le graphe
2. **Réparation** : Corrige automatiquement les problèmes détectés

## Journalisation
Les résultats sont enregistrés dans `/graph_check/graph_integrity.log`

## Avertissement
- Utilisez avec précaution
- Faites une sauvegarde avant toute réparation
