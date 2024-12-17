"""
Logique de paramétrage du PageRank personnalisé pour les recommandations utilisateur
-------------------------------------------------------------------------------

1. PONDÉRATION DES ENTITÉS
-------------------------
Les poids sont attribués selon l'importance relative de chaque type d'entité :

* user_preference (1.2) : 
    - Surpondéré car représente directement les intérêts explicites de l'utilisateur
    - Crucial pour des recommandations personnalisées pertinentes
    
* positive_point (1.0) :
    - Poids standard servant de référence
    - Représente les interactions positives objectives
    
* negative_point (0.8) :
    - Sous-pondéré pour réduire l'impact des retours négatifs
    - Évite de trop pénaliser mais garde une influence modérée
    
* activity (1.1) :
    - Légèrement surpondéré car indique un engagement actif
    - Favorise les éléments avec interaction utilisateur

2. FACTEURS D'AJUSTEMENT
------------------------
* connection_bonus (1.1) :
    - Bonus pour les nœuds ayant plus de 5 connexions
    - Favorise les éléments bien connectés dans le graphe
    - Reflète la pertinence collective d'un élément
    
* description_weight (0.1) :
    - Bonus de 10% pour les descriptions détaillées (>50 caractères)
    - Encourage la qualité du contenu
    - Améliore la pertinence sémantique

3. PARAMÈTRES PAGERANK
---------------------
* damping_factor (0.85) :
    - Probabilité de suivre les liens vs. saut aléatoire
    - Valeur standard optimisant convergence et pertinence
    
* max_iterations (100) :
    - Limite pour garantir la terminaison
    - Suffisant pour la convergence habituelle
    
* epsilon (1e-8) :
    - Seuil de convergence
    - Balance précision et performance

4. LOGIQUE DE SCORING
--------------------
Score final = PageRank × (
    poids_type_entité × 
    (1 + bonus_connexions) × 
    (1 + bonus_description)
)

Cette approche assure :
- Une personnalisation basée sur les préférences utilisateur
- Une prise en compte de la popularité (connexions)
- Une valorisation de la qualité du contenu
- Un équilibre entre signaux positifs et négatifs
"""

import os
import sys
import logging
from typing import List, Dict
from neo4j import GraphDatabase
import numpy as np
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Ajouter le chemin parent pour importer lightrag
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Neo4jPageRank:
    def __init__(
        self, 
        uri: str = None, 
        username: str = None, 
        password: str = None,
        pagerank_config: dict = None
    ):
        """
        Initialise la connexion à la base de données Neo4j
        
        :param uri: URI de connexion à la base Neo4j
        :param username: Nom d'utilisateur
        :param password: Mot de passe
        :param pagerank_config: Configuration personnalisée pour PageRank
        """
        # Configuration par défaut du PageRank
            # DAMPING FACTOR (Facteur d'amortissement)
            # - Probabilité de continuer à suivre les liens
            # - Valeur standard : 0.85
            # - Plage : 0 à 1
            # - Plus proche de 1 : plus de poids aux liens existants
            # - Plus proche de 0 : plus de randomness

            # MAX ITERATIONS (Nombre maximum d'itérations)
            # - Limite le nombre de fois où l'algorithme va itérer
            # - Évite les boucles infinies
            # - Augmenter si convergence lente
            # - Diminuer pour des calculs plus rapides
            
            # EPSILON (Seuil de convergence)
            # - Différence minimale entre deux itérations pour considérer comme convergé
            # - Plus petit = plus précis mais plus long
            # - Valeurs typiques : 1e-8 à 1e-4
            # - Diminuer pour plus de précision
            # - Augmenter pour des calculs plus rapides
        self.pagerank_config = {
            'damping_factor': 0.85,  
            'max_iterations': 100,   
            'epsilon': 1e-8,
            'relation_threshold': 0.1,
            # Nouveaux paramètres pour la pondération
            'entity_weights': {
                'user_preference': 1.2,  # Surpondération des préférences utilisateurs
                'positive_point': 1.0,   # Poids standard pour les points positifs
                'negative_point': 0.8,   # Poids réduit pour les points négatifs
                'activity': 1.1         # Poids légèrement augmenté pour les activités
            },
            'connection_bonus': 1.1,     # Bonus pour les nœuds bien connectés
            'description_weight': 0.1    # Poids pour la pertinence de la description
        }

        # Mettre à jour avec la configuration personnalisée si fournie
        if pagerank_config:
            self.pagerank_config.update(pagerank_config)

        # Utiliser les variables d'environnement si non spécifiées
        self.uri = uri or os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')

        # Déboguer les informations de connexion
        logging.info(f"Tentative de connexion à Neo4j:")
        logging.info(f"URI: {self.uri}")
        logging.info(f"Nom d'utilisateur: {self.username}")
        logging.info(f"Configuration PageRank: {self.pagerank_config}")

        # Créer une connexion directe avec le driver Neo4j
        try:
            self._driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.username, self.password)
            )
        except Exception as e:
            logging.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def close(self):
        """Ferme la connexion à la base de données"""
        self._driver.close()

    def create_pagerank_relationships(self, pagerank_results):
        """
        Liste les relations potentielles entre nœuds avec entity_type='user_preference' 
        et entity_type='positive_point' basées sur les scores de PageRank.
        
        :param pagerank_results: Résultats du PageRank
        """
        threshold = self.pagerank_config['relation_threshold']
        
        logging.info(f"Analyse des relations potentielles avec seuil de PageRank : {threshold}")
        
        with self._driver.session() as session:
            high_pagerank_nodes = {
                node_id: result for node_id, result in pagerank_results.items() 
                if result['score'] > threshold
            }
            
            logging.info(f"Nombre de nœuds au-dessus du seuil : {len(high_pagerank_nodes)}")
            
            nodes_query = """
            UNWIND $node_ids AS node_id
            MATCH (n) 
            WHERE elementId(n) = node_id 
              AND (n.entity_type = 'user_preference' OR n.entity_type = 'positive_point')
            RETURN elementId(n) AS id, n.entity_type AS entity_type
            """
            node_details = session.run(nodes_query, {'node_ids': list(high_pagerank_nodes.keys())}).data()
            
            potential_relations = []
            for source in node_details:
                for target in node_details:
                    if source['entity_type'] != target['entity_type']:
                        potential_relation = {
                            'source_id': source['id'],
                            'source_entity_type': source['entity_type'],
                            'target_id': target['id'],
                            'target_entity_type': target['entity_type'],
                            'pagerank_score': high_pagerank_nodes[source['id']]['score']
                        }
                        potential_relations.append(potential_relation)
            
            print("\n--- Relations Potentielles basées sur PageRank ---")
            for relation in potential_relations:
                print(f"Source (ID: {relation['source_id']}, Entity Type: {relation['source_entity_type']}) "
                      f"-> Target (ID: {relation['target_id']}, Entity Type: {relation['target_entity_type']}) "
                      f"| PageRank Score: {relation['pagerank_score']:.4f}")
            
            print(f"\nNombre total de relations potentielles : {len(potential_relations)}")
            
            return potential_relations

    def calculate_node_weight(self, node_type: str, connection_count: int, description: str = None) -> float:
        """
        Calcule le poids d'un nœud basé sur son type, ses connexions et sa description
        
        :param node_type: Type du nœud (user_preference, positive_point, etc.)
        :param connection_count: Nombre de connexions du nœud
        :param description: Description du nœud (optionnel)
        :return: Poids calculé du nœud
        """
        # Poids de base selon le type d'entité
        base_weight = self.pagerank_config['entity_weights'].get(node_type, 1.0)
        
        # Bonus pour les nœuds bien connectés
        if connection_count > 5:
            base_weight *= self.pagerank_config['connection_bonus']
        
        # Bonus basé sur la description si disponible
        if description and self.pagerank_config['description_weight'] > 0:
            # Bonus si la description est substantielle (plus de 50 caractères)
            if len(description) > 50:
                base_weight *= (1 + self.pagerank_config['description_weight'])
        
        return base_weight

    def page_rank_user_preferences(self):
        """
        Calcule le PageRank entre les nœuds avec entity_type='user_preference' 
        et entity_type='positive_point' avec pondération améliorée et élimination des nœuds isolés
        
        :return: Dictionnaire des scores PageRank
        """
        logging.info(f"Début du calcul PageRank avec configuration : {self.pagerank_config}")
        
        with self._driver.session() as session:
            # Requête pour identifier le sous-graphe connecté
            connected_graph_query = """
            MATCH (n)-[r]->(m)
            WHERE n.entity_type IN ['user_preference', 'positive_point', 'activity']
            AND m.entity_type IN ['user_preference', 'positive_point', 'activity']
            WITH DISTINCT n, m
            
            // Collecte des informations sur les nœuds connectés
            WITH collect(DISTINCT n) + collect(DISTINCT m) AS connected_nodes
            
            UNWIND connected_nodes AS node
            WITH DISTINCT node, 
                 COUNT { (node)--() } as connection_count
            
            RETURN 
                elementId(node) AS id, 
                node.entity_type AS type,
                node.description AS description,
                connection_count
            """
            
            nodes = session.run(connected_graph_query).data()
            logging.info(f"Nombre de nœuds connectés trouvés : {len(nodes)}")
            
            # Requête pour les relations dans le sous-graphe
            relations_query = """
            MATCH (source)-[r]->(target)
            WHERE source.entity_type IN ['user_preference', 'positive_point', 'activity']
            AND target.entity_type IN ['user_preference', 'positive_point', 'activity']
            RETURN 
                elementId(source) AS source_id, 
                elementId(target) AS target_id,
                type(r) AS relation_type
            """
            relations = session.run(relations_query).data()
            logging.info(f"Nombre de relations dans le sous-graphe : {len(relations)}")
            
            node_ids = {node['id']: idx for idx, node in enumerate(nodes)}
            num_nodes = len(node_ids)
            
            # Initialisation de la matrice d'adjacence avec les poids
            adjacency_matrix = np.zeros((num_nodes, num_nodes))
            
            # Calcul des poids des nœuds
            node_weights = np.ones(num_nodes)
            for node in nodes:
                idx = node_ids[node['id']]
                weight = self.calculate_node_weight(
                    node['type'],
                    node['connection_count'],
                    node.get('description')
                )
                node_weights[idx] = weight
            
            # Application des poids à la matrice d'adjacence
            for rel in relations:
                if rel['source_id'] in node_ids and rel['target_id'] in node_ids:
                    source_idx = node_ids[rel['source_id']]
                    target_idx = node_ids[rel['target_id']]
                    # Pondération bidirectionnelle
                    adjacency_matrix[source_idx, target_idx] = node_weights[target_idx]
                    adjacency_matrix[target_idx, source_idx] = node_weights[source_idx]
            
            # Normalisation de la matrice
            out_degree = adjacency_matrix.sum(axis=1)
            
            # Gestion des nœuds sans connexions
            out_degree_safe = np.where(out_degree == 0, 1, out_degree)
            
            # Normalisation sécurisée avec gestion des divisions par zéro
            with np.errstate(divide='ignore', invalid='ignore'):
                transition_matrix = adjacency_matrix / out_degree_safe[:, np.newaxis]
                transition_matrix = np.nan_to_num(transition_matrix, 0)
                
            # Initialisation du PageRank avec les poids des nœuds
            pagerank = node_weights / np.sum(node_weights)
            
            # Itérations du PageRank
            damping_factor = self.pagerank_config['damping_factor']
            max_iterations = self.pagerank_config['max_iterations']
            epsilon = self.pagerank_config['epsilon']
            
            for iteration in range(max_iterations):
                prev_pagerank = pagerank.copy()
                
                pagerank = (1 - damping_factor) * node_weights / np.sum(node_weights) + \
                          damping_factor * transition_matrix.T.dot(prev_pagerank)
                
                convergence_delta = np.sum(np.abs(pagerank - prev_pagerank))
                logging.debug(f"Itération {iteration+1}, Delta de convergence : {convergence_delta}")
                
                if convergence_delta < epsilon:
                    logging.info(f"Convergence atteinte à l'itération {iteration+1}")
                    break
            
            # Préparation des résultats de PageRank
            pagerank_results = {}
            for idx, node in enumerate(nodes):
                pagerank_results[node['id']] = {
                    'type': node['type'],
                    'score': pagerank[idx],
                    'connection_count': node.get('connection_count', 0),
                    'description': node.get('description', '')
                }
            
            # Calcul du seuil de PageRank dynamique
            pagerank_threshold = max(
                0.01,  # Seuil minimal
                np.percentile(pagerank, 50)  # Médiane comme base
            )
            
            # Logging détaillé pour le débogage
            logging.info(f"Statistiques du PageRank :")
            logging.info(f"Min: {pagerank.min()}")
            logging.info(f"Max: {pagerank.max()}")
            logging.info(f"Moyenne: {pagerank.mean()}")
            logging.info(f"Médiane: {np.median(pagerank)}")
            logging.info(f"Seuil de PageRank calculé: {pagerank_threshold}")
            
            # Filtrage des nœuds au-dessus du seuil par type d'entité
            high_pagerank_nodes = {
                node_id: node_info for node_id, node_info in pagerank_results.items() 
                if node_info['score'] >= pagerank_threshold
            }
            
            logging.info(f"Nœuds au-dessus du seuil : {len(high_pagerank_nodes)}")
            for node_id, node_info in high_pagerank_nodes.items():
                logging.info(f"Nœud {node_id} - Type: {node_info['type']}, Score: {node_info['score']}")
            
            # Ajustement dynamique du seuil si aucun nœud n'est trouvé
            if not high_pagerank_nodes:
                pagerank_threshold = np.percentile(pagerank, 25)
                logging.warning(f"Aucun nœud au-dessus du seuil initial. Réduction du seuil à : {pagerank_threshold}")
                
                high_pagerank_nodes = {
                    node_id: node_info for node_id, node_info in pagerank_results.items() 
                    if node_info['score'] >= pagerank_threshold
                }
                
                logging.info(f"Nœuds après ajustement du seuil : {len(high_pagerank_nodes)}")
            
            return high_pagerank_nodes

    def save_pagerank_results(self, pagerank_results):
        """
        Sauvegarde les résultats du PageRank dans Neo4j
        
        :param pagerank_results: Dictionnaire des scores PageRank
        """
        with self._driver.session() as session:
            for node_id, result in pagerank_results.items():
                update_query = """
                MATCH (n) WHERE elementId(n) = $node_id
                SET n.pagerank_score = $score
                """
                session.run(update_query, {
                    'node_id': node_id, 
                    'score': result['score']
                })

def main():
    logging.basicConfig(
        level=logging.INFO,  
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('pagerank_process.log'),  
            logging.StreamHandler()  
        ]
    )
    
    pagerank_engine = None
    try:
        custom_pagerank_config = {
            'damping_factor': 0.90,  
            'max_iterations': 150,   
            'epsilon': 1e-10,        
            'relation_threshold': 0.15,  
            # Nouveaux paramètres pour la pondération
            'entity_weights': {
                'user_preference': 1.2,  # Surpondération des préférences utilisateurs
                'positive_point': 1.0,   # Poids standard pour les points positifs
                'negative_point': 0.8,   # Poids réduit pour les points négatifs
                'activity': 1.1         # Poids légèrement augmenté pour les activités
            },
            'connection_bonus': 1.1,     # Bonus pour les nœuds bien connectés
            'description_weight': 0.1    # Poids pour la pertinence de la description
        }
        
        pagerank_engine = Neo4jPageRank(pagerank_config=custom_pagerank_config)
        
        pagerank_results = pagerank_engine.page_rank_user_preferences()
        
        pagerank_engine.save_pagerank_results(pagerank_results)
        
        pagerank_engine.create_pagerank_relationships(pagerank_results)
    
    except Exception as e:
        logging.error(f"Erreur lors du traitement : {e}", exc_info=True)
    finally:
        if pagerank_engine:
            pagerank_engine.close()

if __name__ == '__main__':
    main()
