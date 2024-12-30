import logging
from neo4j import GraphDatabase
import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pymilvus import connections, Collection


# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Charger les variables d'environnement
load_dotenv()

class Neo4jGraphFilter:
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

    def filter_nodes(self, node_ids):
        """
        Filtre les nœuds du graphe Neo4j en utilisant custom_id
        
        Args:
            node_ids (List[str]): Liste des custom_id de nœuds à filtrer
        
        Returns:
            list: Liste des nœuds et relations filtrés
        """
        with self.driver.session() as session:
            query = """
            // Trouver les nœuds par leur custom_id
            MATCH (n)
            WHERE n.custom_id IN $node_ids
            
            // Récupérer les nœuds et leurs relations
            MATCH (n)-[r]-(connected)
            RETURN 
                n AS source_node, 
                r AS relationship, 
                connected AS target_node,
                labels(n) AS source_labels,
                labels(connected) AS target_labels,
                properties(n) AS source_properties,
                properties(r) AS relationship_properties,
                properties(connected) AS target_properties
            """
            
            try:
                # Créer la requête finale avec les identifiants
                final_query = query.replace("$node_ids", str(node_ids))
                logger.info("Requête Cypher finale :\n" + final_query)
                
                logger.debug(f"Filtrage des nœuds avec custom_id : {node_ids}")
                
                result = session.run(query, {"node_ids": node_ids})
                
                # Collecter les résultats
                filtered_results = []
                for record in result:
                    filtered_results.append({
                        'source_node': {
                            'node': dict(record['source_node']),
                            'labels': record['source_labels'],
                            'properties': record['source_properties']
                        },
                        'relationship': {
                            'relation': dict(record['relationship']),
                            'properties': record['relationship_properties']
                        },
                        'target_node': {
                            'node': dict(record['target_node']),
                            'labels': record['target_labels'],
                            'properties': record['target_properties']
                        }
                    })
                
                logger.info(f"Filtrage réussi : {len(filtered_results)} résultats trouvés")
                
                return filtered_results
            
            except Exception as e:
                logger.error(f"Erreur lors du filtrage du graphe Neo4j : {e}")
                raise

    def extract_filtered_ids(self, filtered_results):
        """
        Extrait les entity_ids et relation_ids à partir des résultats filtrés.
        
        Args:
            filtered_results (list): Liste des résultats filtrés
        
        Returns:
            dict: Dictionnaire contenant les node_ids et relation_ids
        """
        filtered_ids = {
            'node_ids': set(),
            'relation_ids': set()
        }
        
        for result in filtered_results:
            # Extraire l'entity_id du nœud source
            source_entity_id = result['source_node']['properties'].get('entity_id')
            if source_entity_id:
                filtered_ids['node_ids'].add(source_entity_id)
            
            # Extraire l'entity_id du nœud cible
            target_entity_id = result['target_node']['properties'].get('entity_id')
            if target_entity_id:
                filtered_ids['node_ids'].add(target_entity_id)
            
            # Extraire le relation_id
            relation_id = result['relationship']['properties'].get('relation_id')
            if relation_id:
                filtered_ids['relation_ids'].add(relation_id)
        
        # Convertir les sets en listes
        filtered_ids['node_ids'] = list(filtered_ids['node_ids'])
        filtered_ids['relation_ids'] = list(filtered_ids['relation_ids'])
        
        return filtered_ids




def export_milvus_to_dataframe(collection_name="entities", filtered_ids=None):
    """
    Exporter une collection Milvus vers un DataFrame pandas selon un filtre d'IDs.
    
    :param collection_name: Nom de la collection Milvus
    :param filtered_ids: Liste des IDs à filtrer (optionnel)
    :return: DataFrame pandas contenant les données de la collection
    """

    try:
        # Charger les variables d'environnement
        env_path = Path(__file__).parent / '.env'
        load_dotenv(dotenv_path=env_path)

        # Récupérer les paramètres de connexion
        milvus_uri = os.environ.get("MILVUS_URI", "tcp://localhost:19530")
        db_name = os.environ.get("MILVUS_DB_NAME", "lightrag")

        # Connexion à Milvus
        connections.connect(
            alias="default",
            uri=milvus_uri,
            db_name=db_name
        )
        print(f"✅ Connecté au serveur Milvus")

        # Charger la collection
        collection = Collection(collection_name)
        collection.load()
        print(f"📚 Collection '{collection_name}' chargée")

        # Construire l'expression de filtrage si des IDs sont fournis
        if filtered_ids:
            filter_expr = 'id in [' + ', '.join(f'"{id}"' for id in filtered_ids) + ']'
            print(f"🔍 Expression de filtrage : {filter_expr}")
        else:
            filter_expr = ""
            print("🌐 Aucun filtre d'ID spécifié, exportation de toute la collection")

        # Paramètres de recherche constants
        # search_params = {
        #     "metric_type": "COSINE",  # Utiliser COSINE au lieu de L2
        #     "params": {"nprobe": 10}
        # }

        search_params = {"metric_type": "COSINE"}

        # Récupérer les données avec l'expression de filtrage
        results = collection.search(
            data=vec,
            #expr='entity_type == "positive_point"',
            expr=filter_expr,
            param=search_params,
            anns_field="vector",
            output_fields=["id", "entity_name", "entity_type"],
            limit=8  # Ajustez selon la taille de votre collection
        )

        print(f"\n🔍 Nombre de résultats trouvés : {len(results)}")

        # Si aucun résultat, retourner un DataFrame vide
        if not results:
            return pd.DataFrame()



        for hits in results:
            print("TopK results:")
            for hit in hits:
                print(hit)

        # Convertir les résultats en DataFrame
        df = pd.DataFrame(results)

        # Afficher tous les champs disponibles
        # print("\n📋 Champs disponibles :")
        # for column in df.columns:
        #     print(f"  - {column}")

        return df

    except Exception as e:
        print(f"❌ Une erreur s'est produite : {e}")
        return None

    finally:
        # Décharger la collection et se déconnecter
        #collection.release()
        #connections.disconnect("default")
        print("🔌 Déconnecté du serveur Milvus")





def main():
    # Exemples d'identifiants à filtrer
    test_node_ids = ['13294163500777077759', 'lea']

    try:
        # Initialiser le filtre de graphe
        graph_filter = Neo4jGraphFilter()
        
        # Filtrer les nœuds
        filtered_results = graph_filter.filter_nodes(test_node_ids)
        
        # Extraire les IDs
        filtered_ids = graph_filter.extract_filtered_ids(filtered_results)
        
        # Afficher les informations de base
        logger.info(f"Type du Resultat du filtrage: {type(filtered_results)}")
        logger.debug(f"Resultats du filtrage: {filtered_results}")
        logger.info(f"IDs collectés : {filtered_ids}")
        

        # Exemple d'utilisation
        filtered_ids = [
            "ent-0083fd68b176b558d7f14787622dc9fe"
        ]
        
        # Exporter avec filtrage
        df = export_milvus_to_dataframe(
            collection_name="entities", 
            filtered_ids=filtered_ids
        )

    except Exception as e:
        logger.error(f"Erreur lors du filtrage : {e}")
    finally:
        pass

if __name__ == "__main__":
    main()