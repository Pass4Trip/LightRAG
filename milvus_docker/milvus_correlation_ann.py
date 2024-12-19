from typing import List, Dict, Any
from pymilvus import connections, Collection, utility
import numpy as np

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
        connections.connect(alias="default", host=host, port=port, db_name=db_name)
        return True
    except Exception as e:
        print(f"Erreur de connexion à Milvus : {e}")
        return False

def get_all_node_ids(collection_name: str, 
                      id_field: str = "id", 
                      limit: int = None,
                      expr: str = "id != ''") -> List[str]:
    """
    Récupère tous les IDs de nœuds dans une collection Milvus.
    
    Args:
        collection_name (str): Nom de la collection Milvus
        id_field (str): Nom du champ contenant l'ID des entités
        limit (int, optional): Limite du nombre d'IDs à retourner
        expr (str, optional): Expression de filtrage. Par défaut, tous les documents.
    
    Returns:
        List[str]: Liste des IDs de nœuds
    """
    if not connect_milvus():
        return []
    
    try:
        # Vérifier si la collection existe
        if collection_name not in utility.list_collections():
            print(f"ERREUR : La collection '{collection_name}' n'existe pas.")
            print("Collections disponibles :", utility.list_collections())
            return []
        
        collection = Collection(collection_name)
        collection.load()
        
        # Vérifier les champs disponibles
        schema = collection.schema
        available_fields = [field.name for field in schema.fields]
        print(f"Champs disponibles dans la collection : {available_fields}")
        
        # Vérifier si le champ d'ID existe
        if id_field not in available_fields:
            # Essayer de trouver un champ d'ID alternatif
            id_alternatives = [f for f in available_fields if 'id' in f.lower()]
            if id_alternatives:
                id_field = id_alternatives[0]
                print(f"Utilisation du champ d'ID alternatif : {id_field}")
            else:
                print(f"ERREUR : Aucun champ d'ID trouvé.")
                print(f"Champs disponibles : {available_fields}")
                return []
        
        # Paramètres de requête
        query_params = {
            "expr": expr,
            "output_fields": [id_field]
        }
        
        # Ajouter une limite si spécifiée
        if limit is not None:
            query_params["limit"] = limit
        
        # Requête pour récupérer les IDs
        results = collection.query(**query_params)
        
        # Extraire les IDs
        node_ids = [str(result[id_field]) for result in results]
        
        print(f"Nombre de nœuds récupérés : {len(node_ids)}")
        return node_ids
    
    except Exception as e:
        print(f"Erreur lors de la récupération des IDs de nœuds : {e}")
        return []

def compute_ann_correlations(collection_name: str, 
                             node_ids: List[str], 
                             top_k: int = 5, 
                             embedding_field: str = "vector",
                             metric_type: str = "COSINE",  
                             nlist: int = 1024,
                             nprobe: int = 20) -> List[Dict[str, Any]]:
    """
    Calcule les corrélations ANN entre les nœuds avec des paramètres ANN optimisés.
    
    Args:
        collection_name (str): Nom de la collection Milvus
        node_ids (List[str]): Liste des IDs de nœuds
        top_k (int): Nombre de voisins les plus proches à retourner
        embedding_field (str): Nom du champ contenant l'embedding
        metric_type (str): Type de métrique de distance 
            - "COSINE" pour la similarité cosinus
            - "L2" pour distance euclidienne
        nlist (int): Nombre de clusters pour l'indexation IVF
        nprobe (int): Nombre de clusters à sonder lors de la recherche
    
    Returns:
        List[Dict[str, Any]]: Liste des corrélations ANN
    """
    if not connect_milvus():
        return []
    
    try:
        collection = Collection(collection_name)
        collection.load()
        
        # Récupérer les embeddings et les noms d'entités
        query_params = {
            "expr": f"id in {node_ids}",
            "output_fields": ["id", embedding_field]
        }
        results = collection.query(**query_params)
        
        # Créer un dictionnaire d'embeddings
        embeddings = {
            str(result["id"]): result[embedding_field] 
            for result in results
        }
        
        # Paramètres de recherche optimisés
        search_params = {
            "metric_type": metric_type,
            "params": {
                "nlist": nlist,
                "nprobe": nprobe
            }
        }
        
        # Stocker les résultats de corrélation
        correlations = []
        
        # Calculer les plus proches voisins pour chaque nœud
        for node_id, embedding in embeddings.items():
            # Recherche des voisins les plus proches
            search_results = collection.search(
                data=[embedding],
                anns_field=embedding_field,
                param=search_params,
                limit=top_k + 1,
                output_fields=["id"]
            )
            
            # Traiter les résultats
            node_correlations = []
            for result in search_results[0]:
                # Ignorer le premier résultat (le nœud lui-même)
                if str(result.id) != node_id:
                    node_correlations.append({
                        "correlated_node_id": str(result.id),
                        "distance": result.distance
                    })
            
            correlations.append({
                "source_node_id": node_id,
                "correlations": node_correlations
            })
        
        return correlations
    
    except Exception as e:
        print(f"Erreur lors du calcul des corrélations ANN : {e}")
        import traceback
        traceback.print_exc()
        return []

def list_milvus_collections() -> List[str]:
    """
    Liste toutes les collections disponibles dans Milvus.
    
    Returns:
        List[str]: Liste des noms de collections
    """
    if not connect_milvus():
        return []
    
    try:
        collections = utility.list_collections()
        print("Collections disponibles :", collections)
        return collections
    
    except Exception as e:
        print(f"Erreur lors de la récupération des collections : {e}")
        return []

def main():
    """
    Exemple d'utilisation de la fonction de corrélation ANN.
    """
    # Lister les collections disponibles
    available_collections = list_milvus_collections()
    
    if not available_collections:
        print("Aucune collection trouvée dans Milvus.")
        return
    
    # Utiliser la collection "entities"
    collection_name = "entities"
    print(f"Utilisation de la collection : {collection_name}")
    
    try:
        # Charger la collection
        collection = Collection(collection_name)
        collection.load()
        
        # Vérifier le nombre total de documents
        num_entities = collection.num_entities
        print(f"Nombre total d'entités dans la collection : {num_entities}")
        
        # Récupérer un nombre limité de nœuds
        node_ids = get_all_node_ids(collection_name, limit=10)
        
        # Vérifier si des nœuds sont disponibles
        if not node_ids:
            print("Aucun nœud trouvé dans la collection.")
            print("Essayez de vérifier la connexion à Milvus ou le contenu de la collection.")
            return
        
        print("\nCalcul des corrélations ANN...")
        # Calculer les corrélations
        correlations = compute_ann_correlations(collection_name, node_ids)
        
        # Afficher les résultats
        print("\nRésultats des corrélations :")
        for result in correlations:
            source_node_id = result['source_node_id']
            
            # Préparer la liste des nœuds pour la requête Cypher
            cypher_node_list = [source_node_id] + [
                corr['correlated_node_id'] for corr in result['correlations']
            ]
            
            # Générer la requête Cypher
            cypher_query = f"""
MATCH (n)
WHERE n.entity_id IN {cypher_node_list}
RETURN n
"""
            
            print(f"\nNœud source : {source_node_id}")
            print("Requête Cypher :")
            print(cypher_query)
            
            print("Corrélations :")
            for corr in result['correlations']:
                print(f"  - Nœud : {corr['correlated_node_id']}")
                print(f"    Distance : {corr['distance']}")
            print("-" * 50)
    
    except Exception as e:
        print(f"Erreur lors de l'exécution : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
