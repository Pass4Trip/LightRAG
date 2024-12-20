from pymilvus import MilvusClient, Collection
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
import numpy as np
import logging
from openai import OpenAI
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jQueryExecutor:
    def __init__(self, uri=None, username=None, password=None):
        """
        Initialise la connexion à Neo4j
        
        Args:
            uri (str, optional): URI de la base de données Neo4j. 
                                 Par défaut, utilise la variable d'environnement NEO4J_URI.
            username (str, optional): Nom d'utilisateur. 
                                      Par défaut, utilise NEO4J_USERNAME.
            password (str, optional): Mot de passe. 
                                      Par défaut, utilise NEO4J_PASSWORD.
        """
        self.uri = uri or os.getenv('NEO4J_URI')
        self.username = username or os.getenv('NEO4J_USERNAME')
        self.password = password or os.getenv('NEO4J_PASSWORD')
        
        if not all([self.uri, self.username, self.password]):
            raise ValueError("Informations de connexion Neo4j manquantes. Vérifiez vos variables d'environnement.")
        
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            logger.info(f"Connexion à Neo4j établie : {self.uri}")
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j : {e}")
            raise

    def execute_cypher_query(self, query, parameters=None):
        """
        Exécute une requête Cypher avec des paramètres optionnels
        
        Args:
            query (str): Requête Cypher à exécuter
            parameters (dict, optional): Paramètres de la requête
        
        Returns:
            list: Résultats de la requête
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.values()[0] for record in result]
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de la requête Cypher : {e}")
            raise

    def close(self):
        """
        Ferme la connexion au driver Neo4j
        """
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée.")

    def get_node_details(self, node_ids):
        """
        Récupère les détails supplémentaires des nœuds depuis Neo4j
        
        Args:
            node_ids (list): Liste des IDs de nœuds à récupérer
        
        Returns:
            dict: Dictionnaire avec les détails des nœuds, indexés par leur ID
        """
        try:
            # Préparer la requête Cypher pour récupérer les détails
            cypher_query = """
            MATCH (n)
            WHERE n.entity_id IN $node_ids
            RETURN 
                n.entity_id AS entity_id, 
                labels(n) AS labels, 
                n.description AS description, 
                n.entity_type AS entity_type
            """
            
            # Exécuter la requête
            with self.driver.session() as session:
                result = session.run(cypher_query, {"node_ids": node_ids})
                
                # Convertir les résultats en dictionnaire
                node_details = {}
                for record in result:
                    node_id = record['entity_id']
                    node_details[node_id] = {
                        'labels': record['labels'],
                        'description': record['description'] or 'Pas de description',
                        'entity_type': record['entity_type'] or 'Type non spécifié'
                    }
                
                return node_details
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails des nœuds : {e}")
            return {}

# Paramètres de connexion Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_DB_NAME = "lightrag"

def connect_milvus(host: str = MILVUS_HOST, 
                   port: str = MILVUS_PORT, 
                   db_name: str = MILVUS_DB_NAME):
    """
    Établit une connexion à Milvus.
    
    Args:
        host (str): Hôte Milvus
        port (str): Port Milvus
        db_name (str): Nom de la base de données
    
    Returns:
        bool: True si la connexion est réussie
    """
    try:
        from pymilvus import connections
        connections.connect(alias="default", host=host, port=port, db_name=db_name)
        return True
    except Exception as e:
        logger.error(f"Erreur de connexion à Milvus : {e}")
        return False

def get_user_preferences_nodes(neo4j_client, custom_id):
    """
    Récupère les IDs des nœuds de préférences utilisateur pour un utilisateur donné
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
        custom_id (str): ID personnalisé de l'utilisateur
    
    Returns:
        list: Liste des IDs de nœuds de préférences utilisateur
    """
    query = """
    MATCH (n {custom_id: $custom_id})-[r:LIKES]-(m)
    WHERE m.entity_type = 'user_preference'
    RETURN collect(m.entity_id) AS entity_ids
    """
    
    try:
        res = neo4j_client.execute_cypher_query(query, {"custom_id": custom_id})
        return res[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des préférences utilisateur : {e}")
        return []

def get_positive_points_nodes(neo4j_client):
    """
    Récupère les IDs des nœuds de type 'positive_point'
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
    
    Returns:
        list: Liste des IDs de nœuds de type 'positive_point'
    """
    query = """
    MATCH (m)
    WHERE m.entity_type = 'positive_point'
    RETURN collect(m.entity_id) AS entity_ids
    """
    
    try:
        return neo4j_client.execute_cypher_query(query)[0]
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des points positifs : {e}")
        return []

def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calcule la similarité cosinus entre deux vecteurs.
    
    Args:
        vec1 (np.ndarray): Premier vecteur
        vec2 (np.ndarray): Deuxième vecteur
    
    Returns:
        float: Similarité cosinus (plus proche de 0 = plus similaire)
    """
    return 1 - np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

def compute_ann_correlations_with_filter(collection_name, node_ids, target_node_ids, top_k_milvus=1000, top_k_cosine=5, distance_threshold=0.5):
    """
    Calcule les corrélations ANN avec un filtrage sur les nœuds cibles
    
    Args:
        collection_name (str): Nom de la collection Milvus
        node_ids (list): Liste des IDs de nœuds sources
        target_node_ids (list): Liste des IDs de nœuds cibles
        top_k_milvus (int, optional): Nombre de résultats Milvus. Défaut à 10.
        top_k_cosine (int, optional): Nombre de résultats après similarité cosinus. Défaut à 5.
        distance_threshold (float, optional): Seuil de distance maximal. Défaut à 0.5.
    
    Returns:
        list: Liste des corrélations ANN filtrées
    """
    if not connect_milvus():
        return []
    
    try:
        from pymilvus import Collection, utility
        
        # Vérifier si la collection existe
        if collection_name not in utility.list_collections():
            logger.error(f"La collection '{collection_name}' n'existe pas.")
            logger.error(f"Collections disponibles : {utility.list_collections()}")
            return []
        
        # Charger la collection
        collection = Collection(collection_name)
        collection.load()
        
        # Préparer les résultats
        correlations = []
        
        # Pour chaque nœud source
        for source_node_id in node_ids:
            # Récupérer l'embedding du nœud source
            source_query_expr = f'id == "{source_node_id}"'
            source_results = collection.query(
                expr=source_query_expr, 
                output_fields=["id", "vector", "content"]
            )
            
            if not source_results:
                logger.warning(f"Aucun résultat trouvé pour le nœud source {source_node_id}")
                continue
            
            # Extraire l'embedding du nœud source
            source_embedding = source_results[0].get('vector')
            source_content = source_results[0].get('content')
            
            if source_embedding is None:
                logger.warning(f"Pas d'embedding trouvé pour le nœud {source_node_id}")
                continue
            
            # Recherche des voisins les plus proches
            search_params = {
                "metric_type": "COSINE",  # Similarité cosinus
                "params": {
                    "nlist": 1024,  # Nombre de clusters pour l'indexation IVF
                    "nprobe": 20    # Réduction du nombre de clusters à sonder
                }
            }
            
            results = collection.search(
                data=[source_embedding],
                anns_field="vector",
                param=search_params,
                limit=top_k_milvus,
                output_fields=["id", "content"]
            )
            
            # Filtrer et formater les résultats
            source_correlations = []
            
            for result in results[0]:
                # Filtres supplémentaires
                if (result.id not in [source_node_id] and 
                    result.id in target_node_ids and
                    result.distance < distance_threshold):

                    # Récupérer l'embedding du nœud corrélé
                    correlated_query_expr = f'id == "{result.id}"'
                    correlated_results = collection.query(
                        expr=correlated_query_expr, 
                        output_fields=["vector"]
                    )
                    
                    if correlated_results:
                        correlated_embedding = correlated_results[0].get('vector')
                        
                        # Calculer la similarité cosinus
                        cosine_sim = cosine_similarity(
                            np.array(source_embedding), 
                            np.array(correlated_embedding)
                        )
                        
                        source_correlations.append({
                            "correlated_node_id": result.id,
                            "distance": result.distance,
                            "cosine_similarity": cosine_sim,
                            "content": result.entity.get('content')
                        })
            
            # Trier les corrélations par similarité cosinus
            source_correlations.sort(key=lambda x: x['cosine_similarity'])
            
            # Limiter au top_k_cosine
            source_correlations = source_correlations[:top_k_cosine]
            
            # Ajouter les corrélations si non vides
            if source_correlations:
                correlations.append({
                    "source_node_id": source_node_id,
                    "correlations": source_correlations
                })
            else:
                # Log supplémentaire si aucune corrélation n'est trouvée
                logger.warning(f"Aucune corrélation trouvée pour le nœud {source_node_id}")
        
        return correlations
    
    except Exception as e:
        logger.error(f"Erreur lors du calcul des corrélations ANN : {e}")
        return []

def validate_correlation_with_gpt(
    source_description: str, 
    correlated_description: str, 
    model: str = "gpt-4o-mini"
) -> dict:
    """
    Valide la corrélation entre un nœud source et un nœud corrélé en utilisant GPT.
    
    Args:
        source_description (str): Description du nœud source
        correlated_description (str): Description du nœud corrélé
        model (str, optional): Modèle GPT à utiliser. Défaut à "gpt-4o-mini".
    
    Returns:
        dict: Résultat de la validation GPT
    """
    try:
        client = OpenAI()
        
        # Prompt de validation
        prompt = f"""
        Tâche : Analyser la compatibilité entre une préférence utilisateur et un point positif de restaurant.

        Préférence Utilisateur : {source_description}
        Point Positif Restaurant : {correlated_description}

        Instructions :
        1. Évalue si le point positif du restaurant correspond à la préférence de l'utilisateur.
        2. Génère un score de compatibilité entre 0 et 1.
        3. Fournis une justification détaillée.
        4. Si compatible, génère une description de recommandation personnalisée.

        Format de réponse JSON :
        {{
            "is_valid": bool,
            "compatibility_score": float,
            "justification": str,
            "recommendation_description": str
        }}
        """
        
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "Tu es un assistant spécialisé en recommandations personnalisées de restaurants."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parser la réponse JSON
        validation_result = json.loads(response.choices[0].message.content)
        
        return validation_result
    
    except Exception as e:
        logger.error(f"Erreur lors de la validation GPT : {e}")
        return {
            "is_valid": False,
            "compatibility_score": 0.0,
            "justification": f"Erreur de validation : {str(e)}",
            "recommendation_description": ""
        }

def enrich_correlations_with_gpt_validation(correlations, neo4j_client):
    """
    Enrichit les corrélations avec une validation GPT.
    
    Args:
        correlations (list): Liste des corrélations ANN
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
    
    Returns:
        list: Corrélations enrichies avec validation GPT
    """
    try:
        # Récupérer les détails des nœuds sources et corrélés
        all_node_ids = set()
        for correlation_group in correlations:
            all_node_ids.add(correlation_group['source_node_id'])
            for corr in correlation_group['correlations']:
                all_node_ids.add(corr['correlated_node_id'])
        
        # Récupérer les détails des nœuds
        node_details = neo4j_client.get_node_details(list(all_node_ids))
        
        # Enrichir les corrélations
        for correlation_group in correlations:
            source_node_id = correlation_group['source_node_id']
            source_description = node_details.get(source_node_id, {}).get('description', '')
            
            for corr in correlation_group['correlations']:
                correlated_node_id = corr['correlated_node_id']
                correlated_description = node_details.get(correlated_node_id, {}).get('description', '')
                
                # Validation GPT
                gpt_validation = validate_correlation_with_gpt(
                    source_description, 
                    correlated_description
                )
                
                # Ajouter la validation GPT à la corrélation
                corr['gpt_validation'] = gpt_validation
        
        return correlations
    
    except Exception as e:
        logger.error(f"Erreur lors de l'enrichissement des corrélations : {e}")
        return correlations

def create_gpt_validated_relationships(neo4j_client, correlations):
    """
    Crée des relations 'RECO' dans Neo4j pour les corrélations validées par GPT.
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
        correlations (list): Liste des corrélations ANN avec validation GPT
    
    Returns:
        int: Nombre de relations créées
    """
    try:
        # Requête Cypher pour créer les relations
        cypher_query = """
        MATCH (source {entity_id: $source_id}), (target {entity_id: $target_id})
        CREATE (source)-[r:RECO {
            description: $description,
            weight_distance_cosine: $weight_distance,
            weight_similarity_cosine: $weight_similarity,
            llm_compatibility_score: $compatibility_score,
            status: 'a valider'
        }]->(target)
        RETURN id(r) AS relationship_id
        """
        
        relationships_created = 0
        
        # Parcourir les corrélations
        for correlation_group in correlations:
            source_node_id = correlation_group['source_node_id']
            
            for corr in correlation_group['correlations']:
                # Vérifier si la corrélation est validée par GPT
                gpt_validation = corr.get('gpt_validation', {})
                if gpt_validation.get('is_valid', False):
                    # Préparer les paramètres pour la requête
                    params = {
                        'source_id': source_node_id,
                        'target_id': corr['correlated_node_id'],
                        'description': gpt_validation.get('justification', ''),
                        'weight_distance': corr['distance'],
                        'weight_similarity': corr['cosine_similarity'],
                        'compatibility_score': gpt_validation.get('compatibility_score', 0.0)
                    }
                    
                    # Exécuter la requête Cypher
                    with neo4j_client.driver.session() as session:
                        result = session.run(cypher_query, params)
                        relationship_id = result.single()['relationship_id']
                        relationships_created += 1
                        
                        logger.info(f"Relation RECO créée : {source_node_id} -> {corr['correlated_node_id']} (ID relation: {relationship_id})")
        
        return relationships_created
    
    except Exception as e:
        logger.error(f"Erreur lors de la création des relations : {e}")
        return 0

def verify_gpt_validated_relationships(neo4j_client, custom_id):
    """
    Vérifie les relations RECO créées pour un utilisateur spécifique.
    
    Args:
        neo4j_client (Neo4jQueryExecutor): Client Neo4j
        custom_id (str): ID de l'utilisateur
    
    Returns:
        list: Liste des relations RECO trouvées
    """
    try:
        # Requête Cypher pour récupérer les relations RECO
        cypher_query = """
        MATCH (source {custom_id: $custom_id})-[r:RECO]->(target)
        RETURN 
            source.entity_id AS source_id, 
            target.entity_id AS target_id, 
            r.description AS description,
            r.weight_distance_cosine AS weight_distance,
            r.weight_similarity_cosine AS weight_similarity,
            r.llm_compatibility_score AS compatibility_score,
            r.status AS status
        """
        
        # Exécuter la requête
        with neo4j_client.driver.session() as session:
            result = session.run(cypher_query, {"custom_id": custom_id})
            
            # Convertir les résultats en liste de dictionnaires
            relationships = []
            for record in result:
                relationships.append({
                    'source_id': record['source_id'],
                    'target_id': record['target_id'],
                    'description': record['description'],
                    'weight_distance': record['weight_distance'],
                    'weight_similarity': record['weight_similarity'],
                    'compatibility_score': record['compatibility_score'],
                    'status': record['status']
                })
            
            return relationships
    
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des relations : {e}")
        return []

def main():
    """
    Exemple d'utilisation de la fonction de corrélation ANN avec filtrage.
    """
    # Initialiser le client Neo4j
    neo4j_client = Neo4jQueryExecutor()
    
    try:
        # ANSI color codes
        RESET = "\033[0m"
        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        MAGENTA = "\033[95m"
        RED = "\033[91m"
        
        # Exemple avec un utilisateur spécifique
        custom_id = 'lea'
        
        # Récupérer les IDs des préférences utilisateur
        user_preference_node_ids = get_user_preferences_nodes(neo4j_client, custom_id)

        # Récupérer les IDs des points positifs
        positive_points_node_ids = get_positive_points_nodes(neo4j_client)
    
        # Calculer les corrélations ANN
        correlations = compute_ann_correlations_with_filter(
            collection_name="entities", 
            node_ids=user_preference_node_ids, 
            target_node_ids=positive_points_node_ids,
            top_k_milvus=1000, 
            top_k_cosine=1, 
            distance_threshold=0.8  # Augmentation du seuil
        )
        
        # Enrichir les corrélations avec validation GPT
        correlations = enrich_correlations_with_gpt_validation(correlations, neo4j_client)
        
        # Créer les relations pour les corrélations validées
        relationships_created = create_gpt_validated_relationships(neo4j_client, correlations)
        print(f"\n{GREEN}✨ Nombre de relations RECO créées : {relationships_created}{RESET}")
        
        # Vérifier les relations créées
        verified_relationships = verify_gpt_validated_relationships(neo4j_client, custom_id)
        
        # Afficher les relations vérifiées
        print(f"\n{BOLD}🔗 Relations RECO vérifiées :{RESET}")
        if verified_relationships:
            for rel in verified_relationships:
                print("\n" + "-" * 50)
                print(f"{BLUE}Source ID:{RESET} {rel['source_id']}")
                print(f"{BLUE}Target ID:{RESET} {rel['target_id']}")
                print(f"{YELLOW}Description:{RESET} {rel['description']}")
                print(f"{GREEN}Distance Weight:{RESET} {rel['weight_distance']}")
                print(f"{GREEN}Similarity Weight:{RESET} {rel['weight_similarity']}")
                print(f"{MAGENTA}Compatibility Score:{RESET} {rel['compatibility_score']}")
                print(f"{RED}Status:{RESET} {rel['status']}")
        else:
            print(f"\n{RED}❌ Aucune relation RECO trouvée{RESET}")
        
        # Afficher les résultats
        print(f"\n{BOLD}🔍 Résultats des corrélations ANN{RESET}")
        print("=" * 50)
        
        # Récupérer les détails des nœuds sources
        node_details = neo4j_client.get_node_details(user_preference_node_ids)
        
        for source_node_id in user_preference_node_ids:
            # Afficher les informations du nœud source
            source_details = node_details.get(source_node_id, {})
            print(f"\n{'🌟' * 10} {BLUE}Nœud Source : {source_node_id}{RESET} {'🌟' * 10}")
            print(f"{GREEN}  ◽ Labels     : {', '.join(source_details.get('labels', ['Aucun']))}{RESET}")
            print(f"{YELLOW}  ◽ Description: {source_details.get('description', 'Pas de description')}{RESET}")
            print(f"{MAGENTA}  ◽ Type       : {source_details.get('entity_type', 'Non spécifié')}{RESET}")
            
            # Rechercher les corrélations pour ce nœud source
            source_correlations = next((
                result['correlations'] for result in correlations 
                if result['source_node_id'] == source_node_id
            ), None)
            
            # Afficher les corrélations ou un message si aucune n'est trouvée
            if source_correlations:
                print(f"\n{BOLD}Corrélations :{RESET}")
                for corr in source_correlations:
                    correlated_node_id = corr['correlated_node_id']
                    node_corr_details = neo4j_client.get_node_details([correlated_node_id])
                    node_corr_details = node_corr_details.get(correlated_node_id, {})
                    
                    print(f"\n{GREEN}  🔗 Nœud Corrélé : {correlated_node_id}{RESET}")
                    print(f"{GREEN}    ◽ Labels     : {', '.join(node_corr_details.get('labels', ['Aucun']))}{RESET}")
                    print(f"{YELLOW}    ◽ Description: {node_corr_details.get('description', 'Pas de description')}{RESET}")
                    print(f"{MAGENTA}    ◽ Type       : {node_corr_details.get('entity_type', 'Non spécifié')}{RESET}")
                    print(f"{BLUE}    ◽ Distance   : {corr['distance']}{RESET}")
                    print(f"{BLUE}    ◽ Similarité cosinus : {corr['cosine_similarity']}{RESET}")
                    
                    # Afficher la validation GPT
                    gpt_validation = corr.get('gpt_validation', {})
                    print(f"{MAGENTA}    ◽ Validation GPT :{RESET}")
                    print(f"      - Validité : {gpt_validation.get('is_valid', False)}")
                    print(f"      - Score de compatibilité : {gpt_validation.get('compatibility_score', 0.0)}")
                    print(f"      - Justification : {gpt_validation.get('justification', 'Aucune')}")
                    print(f"      - Description de recommandation : {gpt_validation.get('recommendation_description', 'Aucune')}")
            else:
                print(f"\n{RED}  ❌ Aucune corrélation trouvée pour ce nœud{RESET}")
            
            print("-" * 50)
    
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")
    
    finally:
        # Fermer la connexion Neo4j
        neo4j_client.close()

if __name__ == "__main__":
    main()