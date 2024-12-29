# Gestion des Sous-Graphes avec Labels et Attributs

Cette solution utilise **labels** pour marquer les nœuds et **propriétés** pour marquer les relations dans Neo4j, sans dépendre de `APOC` ou de namespaces.

---

## Étape 1 : Marquer les Nœuds avec des Labels

### Ajouter un Label aux Nœuds du Sous-Graphe
```cypher
MATCH (n)
WHERE n.custom_id IN ['5390255707819795563', '3529332825818922980']
SET n:SubGraphLabel
RETURN n;
```

### Visualiser les Nœuds du Sous-Graphe
```cypher
MATCH (n:SubGraphLabel)
RETURN n;
```

---

## Étape 2 : Marquer les Relations avec des Attributs

### Ajouter une Propriété aux Relations
```cypher
MATCH (n:SubGraphLabel)-[r]-(m:SubGraphLabel)
SET r.subGraph = true
RETURN r, n, m;
```

### Visualiser les Relations Marquées
```cypher
MATCH (n:SubGraphLabel)-[r]-(m:SubGraphLabel)
WHERE r.subGraph = true
RETURN n, r, m;
```

---

## Étape 3 : Manipuler Plusieurs Sous-Graphes

### Marquer les Relations pour un Sous-Graphe Spécifique
- Sous-Graphe "A" :
```cypher
MATCH (n:SubGraphA)-[r]-(m:SubGraphA)
SET r.subGraph = "A";
```

- Sous-Graphe "B" :
```cypher
MATCH (n:SubGraphB)-[r]-(m:SubGraphB)
SET r.subGraph = "B";
```

### Visualiser les Relations d’un Sous-Graphe
- Sous-Graphe "A" :
```cypher
MATCH (n:SubGraphA)-[r]-(m:SubGraphA)
WHERE r.subGraph = "A"
RETURN n, r, m;
```

- Sous-Graphe "B" :
```cypher
MATCH (n:SubGraphB)-[r]-(m:SubGraphB)
WHERE r.subGraph = "B"
RETURN n, r, m;
```

### Gérer les Relations Partagées entre Plusieurs Sous-Graphes
Ajouter plusieurs sous-graphes dans une propriété :
```cypher
MATCH (n)-[r]-(m)
WHERE n.type = "activity" AND m.type = "user_preference"
SET r.subGraph = ["A", "B"];
```

Filtrer par appartenance à un sous-graphe :
```cypher
MATCH (n)-[r]-(m)
WHERE "A" IN r.subGraph
RETURN n, r, m;
```

---

## Étape 4 : Supprimer ou Réinitialiser les Marqueurs

### Supprimer un Label des Nœuds
```cypher
MATCH (n:SubGraphLabel)
REMOVE n:SubGraphLabel
RETURN n;
```

### Supprimer une Propriété des Relations
```cypher
MATCH ()-[r]->()
WHERE r.subGraph = true
REMOVE r.subGraph;
```

---

## Étape 5 : Affiner le Sous-Graphe

### Filtrer les Nœuds
```cypher
MATCH (n:SubGraphLabel)
WHERE n.type = "activity" AND n.status = "active"
RETURN n;
```

### Filtrer les Relations
```cypher
MATCH (n:SubGraphLabel)-[r]-(m:SubGraphLabel)
WHERE r.subGraph = true AND r.weight > 0.5
RETURN n, r, m;
```

### Limiter les Relations par Nœud
```cypher
MATCH (n:SubGraphLabel)-[r]-(m:SubGraphLabel)
WITH n, COUNT(r) AS num_relations
WHERE num_relations < 50
MATCH (n)-[r]-(m)
RETURN n, r, m;
```

---

## Étape 6 : Indexer pour Améliorer les Performances

### Index sur les Labels des Nœuds
```cypher
CREATE INDEX FOR (n:SubGraphLabel) ON (n.type);
```

### Index sur les Propriétés des Relations
```cypher
CREATE INDEX FOR ()-[r]-() ON (r.subGraph);
```

---

## Avantages de la Solution
1. **Flexible** : Gère plusieurs sous-graphes en parallèle.
2. **Performante** : Compatible avec les index pour un filtrage rapide.
3. **Sans Extensions** : Pas besoin d'APOC ou d'autres dépendances.
4. **Scalable** : Facile à adapter à des graphes complexes.

---

## Résumé
1. Utilisez **labels** pour marquer les nœuds (`:SubGraphLabel`).
2. Utilisez **propriétés** pour marquer les relations (`subGraph = "A"`).
3. Filtrez, affinez et manipulez les sous-graphes en utilisant des critères précis.
4. Optimisez avec des index et gérez des sous-graphes multiples sans interférences.

Cette approche garantit une gestion propre et performante des sous-graphes dans Neo4j.

