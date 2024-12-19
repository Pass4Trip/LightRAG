import os
import logging
import json
import numpy as np
from typing import List, Dict, Optional
from pymilvus import MilvusClient
from scipy.spatial.distance import cosine

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration Milvus
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
MILVUS_DB_NAME = "lightrag"

def connect_milvus(
    host: str = MILVUS_HOST, 
    port: str = MILVUS_PORT,
    db_name: str = MILVUS_DB_NAME
) -> Optional[MilvusClient]:
    """
    Établit une connexion à Milvus.
    """
    try:
        client = MilvusClient(
            uri=f"tcp://{host}:{port}",
            db_name=db_name
        )
        logger.info(f"Connexion à Milvus établie : {host}:{port}, base de données : {db_name}")
        return client
    except Exception as e:
        logger.error(f"Erreur de connexion à Milvus : {e}")
        return None

def compute_node_ann_correlations(
    client, 
    collection_name: str,
    source_node_id: str, 
    target_node_ids: List[str], 
    top_k: int = 5, 
    distance_threshold: float = 0.7
) -> List[Dict]:
    """
    Calcule les corrélations ANN entre un nœud source et des nœuds cibles.
    """
    try:
        logger.info(f"Début de la recherche de similarité")
        logger.info(f"Nœud source : {source_node_id}")
        logger.info(f"Nœuds cibles : {target_node_ids}")
        logger.info(f"Seuil de distance : {distance_threshold}")
        
        # Récupérer l'embedding du nœud source
        source_query_expr = f'id == "{source_node_id}"'
        source_results = client.query(
            collection_name=collection_name,
            filter=source_query_expr, 
            output_fields=["id", "vector", "content"]
        )
        
        if not source_results:
            logger.warning(f"Aucun résultat trouvé pour le nœud source {source_node_id}")
            return []
        
        # Extraire l'embedding du nœud source
        source_embedding = source_results[0].get('vector')
        source_content = source_results[0].get('content')
        
        if source_embedding is None:
            logger.warning(f"Pas d'embedding trouvé pour le nœud {source_node_id}")
            return []
        
        logger.info(f"Embedding source récupéré. Longueur : {len(source_embedding)}")
        
        # Paramètres de recherche ANN
        search_params = {
            "metric_type": "COSINE",
            "params": {
                "nlist": 1024,
                "nprobe": 20
            }
        }
        
        # Recherche des voisins les plus proches avec filtrage sur les nœuds cibles
        results = client.search(
            collection_name=collection_name,
            data=[source_embedding],
            anns_field="vector",
            search_params=search_params,
            limit=top_k + 1,  # +1 pour exclure potentiellement le nœud source lui-même
            filter=f'id in {target_node_ids}',  # Filtrer uniquement sur les nœuds cibles
            output_fields=["id", "content"]
        )
        
        logger.info(f"Résultats de recherche : {len(results[0])} résultats")
        
        # Filtrer et formater les résultats
        correlations = []
        
        for hit in results[0]:
            node_id = hit.get('id')
            distance = hit.get('distance')
            
            logger.info(f"Candidat : {node_id}, Distance : {distance}")
            
            # Filtres supplémentaires
            if (node_id not in [source_node_id] and 
                node_id in target_node_ids and
                distance < distance_threshold):
                
                logger.info(f"Candidat {node_id} passe les filtres")
                
                correlations.append({
                    "target_node_id": node_id,
                    "distance": distance,
                    "source_content": source_content,
                    "target_content": hit.get('content')
                })
            
            if len(correlations) == top_k:
                break
        
        logger.info(f"Nombre de corrélations trouvées : {len(correlations)}")
        return correlations
    
    except Exception as e:
        logger.error(f"Erreur lors de la recherche ANN : {e}")
        return []

def main():
    # Configuration de la connexion à Milvus
    from pymilvus import MilvusClient
    
    # Initialisation du client Milvus
    client = MilvusClient(
        uri="tcp://localhost:19530",  
        db_name="lightrag"
    )
    
    # Exemple d'utilisation
    source_node_id = "ent-cbbc1cd12a3fa7e9ddc0d1c89c179e3c"
    target_node_ids = [
        "ent-d1ebbdf6da13b990b03c8031ee32cbc9"
    ]
    
    # Appel de la fonction de recherche de similarité
    correlations = compute_node_ann_correlations(
        client, 
        collection_name="entities", 
        source_node_id=source_node_id, 
        target_node_ids=target_node_ids,
        distance_threshold=0.7  
    )
    
    # Affichage des résultats
    print("Corrélations ANN entre nœuds :")
    for correlation in correlations:
        print(f"Nœud source : {source_node_id}")
        print(f"Nœud cible : {correlation['target_node_id']}")
        print(f"Distance : {correlation['distance']}")
        print(f"Contenu source : {correlation['source_content']}")
        print(f"Contenu cible : {correlation['target_content']}")
        print("---")

if __name__ == "__main__":
    main()
