# Stratégie de Gestion Flexible des Attributs de Nœuds dans LightRAG

## Contexte
Besoin d'ajouter des attributs dynamiques aux nœuds du graphe de connaissances, en particulier pour les entités de type restaurant.

## Objectifs
- Préserver la compatibilité avec le code existant
- Permettre l'ajout dynamique d'attributs
- Maintenir la robustesse de l'extraction des entités
- Minimiser les risques de régression

## Approche en Deux Phases

### Phase 1 : Extraction des Attributs de Base
```python
def extract_base_attributes(record_attributes: list[str], chunk_key: str):
    """
    Extrait les attributs fondamentaux de manière sécurisée.
    
    Validation :
    - Nombre minimal d'attributs
    - Type d'entité correct
    - Nettoyage et validation du nom
    
    Attributs garantis :
    - entity_name
    - entity_type
    - description
    - source_id
    """
```

### Phase 2 : Extraction des Attributs Supplémentaires
```python
def extract_additional_attributes(record_attributes: list[str], base_attributes: dict):
    """
    Gestion flexible des attributs supplémentaires.
    
    Stratégies :
    - Extraction dynamique via clé:valeur
    - Valeurs par défaut
    - Attributs spécifiques par type d'entité
    
    Exemples d'attributs :
    - Pour restaurants : cuisine, prix, accessibilité
    - Génériques : métadonnées contextuelles
    """
```

## Implémentation Détaillée

### Fonction d'Extraction des Attributs de Base

```python
def extract_base_attributes(record_attributes: list[str], chunk_key: str):
    """
    Extrait les attributs de base de manière robuste et sécurisée.
    
    Args:
        record_attributes (list[str]): Liste des attributs d'entrée
        chunk_key (str): Identifiant de la source
    
    Returns:
        dict: Attributs de base avec validation et nettoyage
    """
    # Validation du nombre minimal d'attributs
    if len(record_attributes) < 4:
        logger.warning(f"Pas assez d'attributs : {len(record_attributes)}")
        return None
    
    # Vérification du type d'entité
    first_attr = record_attributes[0]
    if first_attr.lower() != "entity":
        logger.warning(f"Premier attribut n'est pas 'entity' : {first_attr}")
        return None
    
    # Extraction et nettoyage des attributs de base
    entity_name = clean_str(record_attributes[1])
    if not entity_name.strip():
        logger.warning("Le nom de l'entité est vide après nettoyage")
        return None
    
    entity_type = clean_str(record_attributes[2])
    entity_description = clean_str(record_attributes[3])
    entity_source_id = chunk_key
    
    return {
        "entity_name": entity_name,
        "entity_type": entity_type,
        "description": entity_description,
        "source_id": entity_source_id,
    }
```

### Fonction d'Extraction des Attributs Supplémentaires

```python
def extract_additional_attributes(record_attributes: list[str], base_attributes: dict):
    """
    Extrait les attributs supplémentaires de manière flexible.
    
    Args:
        record_attributes (list[str]): Liste des attributs supplémentaires
        base_attributes (dict): Attributs de base précédemment extraits
    
    Returns:
        dict: Attributs supplémentaires avec validation et valeurs par défaut
    """
    # Initialisation des attributs supplémentaires
    additional_attrs = {}
    
    # Extraction dynamique des attributs supplémentaires
    for attr in record_attributes:
        if ":" in attr:
            key, value = map(str.strip, attr.split(":", 1))
            key = key.lower().replace(" ", "_")
            additional_attrs[key] = value
    
    # Attributs spécifiques aux restaurants
    if base_attributes.get("entity_type", "").lower() == "restaurant":
        restaurant_attrs = {
            "cuisine_type": additional_attrs.get("cuisine_type", "non spécifié"),
            "price_range": additional_attrs.get("price_range", "€€"),
            "accessibility_score": float(additional_attrs.get("accessibility_score", "0")),
            "opening_hours": additional_attrs.get("opening_hours", "non spécifié"),
            "address": additional_attrs.get("address", ""),
            "phone": additional_attrs.get("phone", ""),
            "website": additional_attrs.get("website", ""),
            "last_visit": additional_attrs.get("last_visit", ""),
            "average_rating": float(additional_attrs.get("average_rating", "0"))
        }
        return restaurant_attrs
    
    # Pour les autres types d'entités, retourne les attributs génériques
    return additional_attrs
```

### Fonction Principale d'Extraction d'Entité

```python
async def _handle_single_entity_extraction(
    record_attributes: list[str],
    chunk_key: str,
):
    # Phase 1 : Extraction des attributs de base
    base_attributes = extract_base_attributes(record_attributes, chunk_key)
    if base_attributes is None:
        return None
    
    # Phase 2 : Extraction des attributs supplémentaires
    additional_attributes = extract_additional_attributes(
        record_attributes[4:], 
        base_attributes
    )
    
    # Fusion des attributs
    result = {**base_attributes, **additional_attributes}
    
    logger.info(f"DEBUG: Returning entity: {result}")
    return result
```

## Exemple d'Utilisation

### Cas Standard
```text
ENTITY Le Petit Bistrot restaurant française price_range:€€ accessibility_score:8
```

### Cas Complexe
```text
ENTITY Restaurant Gastronomique 
    type:restaurant 
    cuisine_type:moléculaire 
    price_range:€€€ 
    michelin_stars:2 
    chef_name:Jean Dupont
```

## Exemples de Cas d'Utilisation

#### Exemple 1 : Restaurant Simple
```python
# Entrée
record_attributes = [
    "ENTITY", 
    "Le Petit Bistrot", 
    "restaurant", 
    "Un charmant restaurant français", 
    "cuisine_type:française", 
    "price_range:€€", 
    "accessibility_score:8"
]

# Résultat attendu
{
    "entity_name": "Le Petit Bistrot",
    "entity_type": "restaurant",
    "description": "Un charmant restaurant français",
    "source_id": "chunk_123",
    "cuisine_type": "française",
    "price_range": "€€",
    "accessibility_score": 8.0,
    # ... autres attributs avec valeurs par défaut
}
```

#### Exemple 2 : Entité Générique
```python
# Entrée
record_attributes = [
    "ENTITY", 
    "Projet Innovation", 
    "projet", 
    "Un projet innovant", 
    "statut:en_cours", 
    "priorite:haute"
]

# Résultat attendu
{
    "entity_name": "Projet Innovation",
    "entity_type": "projet",
    "description": "Un projet innovant",
    "source_id": "chunk_456",
    "statut": "en_cours",
    "priorite": "haute"
}
```

## Garanties et Robustesse

### Validation
- Nettoyage systématique des attributs
- Gestion des attributs manquants
- Conversion de type sécurisée

### Compatibilité
- Requêtes existantes non impactées
- Structure de base des nœuds préservée
- Extension optionnelle

## Cas Limites Gérés

1. Attributs insuffisants
   - Retour `None`
   - Log d'avertissement

2. Attributs vides
   - Nettoyage et validation
   - Valeurs par défaut

3. Types d'entités variés
   - Stratégie d'extraction adaptative
   - Extension possible pour nouveaux types

## Performance

### Complexité
- O(n) pour l'extraction des attributs
- Overhead minimal comparé aux bénéfices

### Optimisations
- Utilisation de dictionnaires
- Parsing léger
- Logs conditionnels

## Risques et Atténuations

### Risques Identifiés
- Surcharge cognitive
- Potentielle inconsistance des données

### Stratégies d'Atténuation
- Documentation claire
- Validation stricte
- Logs détaillés
- Tests de non-régression

## Perspectives d'Évolution

1. Validation de schéma
2. Typage dynamique
3. Indexation des attributs supplémentaires
4. Stratégies d'agrégation avancées

## Conclusion

Une approche flexible, robuste et évolutive pour l'enrichissement dynamique des nœuds dans un graphe de connaissances.
