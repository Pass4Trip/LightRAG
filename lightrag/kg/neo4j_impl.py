import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any, Union, Tuple, List, Dict
import inspect
from lightrag.utils import logger
from ..base import BaseGraphStorage
from neo4j import (
    AsyncGraphDatabase,
    exceptions as neo4jExceptions,
    AsyncDriver,
    AsyncManagedTransaction,
)


from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)


@dataclass
class Neo4JStorage(BaseGraphStorage):
    @staticmethod
    def load_nx_graph(file_name):
        print("no preloading of graph with neo4j in production")

    def __init__(self, namespace, global_config, embedding_func):
        super().__init__(
            namespace=namespace,
            global_config=global_config,
            embedding_func=embedding_func,
        )
        self._driver = None
        self._driver_lock = asyncio.Lock()
        URI = os.environ["NEO4J_URI"]
        USERNAME = os.environ["NEO4J_USERNAME"]
        PASSWORD = os.environ["NEO4J_PASSWORD"]
        self._driver: AsyncDriver = AsyncGraphDatabase.driver(
            URI, auth=(USERNAME, PASSWORD)
        )
        return None

    def __post_init__(self):
        self._node_embed_algorithms = {
            "node2vec": self._node2vec_embed,
        }

    async def close(self):
        if self._driver:
            await self._driver.close()
            self._driver = None

    async def __aexit__(self, exc_type, exc, tb):
        if self._driver:
            await self._driver.close()

    async def index_done_callback(self):
        print("KG successfully indexed.")

    async def has_node(self, node_id: str) -> bool:
        entity_name_label = node_id.strip('"')

        async with self._driver.session() as session:
            query = (
                f"MATCH (n:`{entity_name_label}`) RETURN count(n) > 0 AS node_exists"
            )
            result = await session.run(query)
            single_result = await result.single()
            logger.debug(
                f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{single_result["node_exists"]}'
            )
            return single_result["node_exists"]

    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        entity_name_label_source = source_node_id.strip('"')
        entity_name_label_target = target_node_id.strip('"')

        async with self._driver.session() as session:
            query = (
                f"MATCH (a:`{entity_name_label_source}`)-[r]-(b:`{entity_name_label_target}`) "
                "RETURN COUNT(r) > 0 AS edgeExists"
            )
            result = await session.run(query)
            single_result = await result.single()
            logger.debug(
                f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{single_result["edgeExists"]}'
            )
            return single_result["edgeExists"]

    async def get_node(self, node_id: str) -> Union[dict, None]:
        async with self._driver.session() as session:
            entity_name_label = node_id.strip('"')
            query = f"MATCH (n:`{entity_name_label}`) RETURN n"
            result = await session.run(query)
            record = await result.single()
            if record:
                node = record["n"]
                node_dict = dict(node)
                logger.debug(
                    f"{inspect.currentframe().f_code.co_name}: query: {query}, result: {node_dict}"
                )
                return node_dict
            return None

    async def node_degree(self, node_id: str) -> int:
        entity_name_label = node_id.strip('"')

        async with self._driver.session() as session:
            query = f"""
                MATCH (n:`{entity_name_label}`)
                RETURN COUNT{{ (n)--() }} AS totalEdgeCount
            """
            result = await session.run(query)
            record = await result.single()
            if record:
                edge_count = record["totalEdgeCount"]
                logger.debug(
                    f"{inspect.currentframe().f_code.co_name}:query:{query}:result:{edge_count}"
                )
                return edge_count
            else:
                return None

    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        entity_name_label_source = src_id.strip('"')
        entity_name_label_target = tgt_id.strip('"')
        src_degree = await self.node_degree(entity_name_label_source)
        trg_degree = await self.node_degree(entity_name_label_target)

        # Convert None to 0 for addition
        src_degree = 0 if src_degree is None else src_degree
        trg_degree = 0 if trg_degree is None else trg_degree

        degrees = int(src_degree) + int(trg_degree)
        logger.debug(
            f"{inspect.currentframe().f_code.co_name}:query:src_Degree+trg_degree:result:{degrees}"
        )
        return degrees

    async def get_edge(
        self, source_node_id: str, target_node_id: str
    ) -> Union[dict, None]:
        entity_name_label_source = source_node_id.strip('"')
        entity_name_label_target = target_node_id.strip('"')
        """
        Find all edges between nodes of two given labels

        Args:
            source_node_label (str): Label of the source nodes
            target_node_label (str): Label of the target nodes

        Returns:
            list: List of all relationships/edges found
        """
        async with self._driver.session() as session:
            query = f"""
            MATCH (start:`{entity_name_label_source}`)-[r]->(end:`{entity_name_label_target}`)
            RETURN properties(r) as edge_properties
            LIMIT 1
            """.format(
                entity_name_label_source=entity_name_label_source,
                entity_name_label_target=entity_name_label_target,
            )

            result = await session.run(query)
            record = await result.single()
            if record:
                result = dict(record["edge_properties"])
                logger.debug(
                    f"{inspect.currentframe().f_code.co_name}:query:{query}:result:{result}"
                )
                return result
            else:
                return None

    async def get_node_edges(self, source_node_id: str) -> List[Tuple[str, str]]:
        node_label = source_node_id.strip('"')

        """
        Retrieves all edges (relationships) for a particular node identified by its label.
        :return: List of dictionaries containing edge information
        """
        query = f"""MATCH (n:`{node_label}`)
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN n, r, connected"""
        async with self._driver.session() as session:
            results = await session.run(query)
            edges = []
            async for record in results:
                source_node = record["n"]
                connected_node = record["connected"]

                source_label = (
                    list(source_node.labels)[0] if source_node.labels else None
                )
                target_label = (
                    list(connected_node.labels)[0]
                    if connected_node and connected_node.labels
                    else None
                )

                if source_label and target_label:
                    edges.append((source_label, target_label))

            return edges

    RELATION_TYPE_MAPPING = {
        # Structure : (source_type, target_type) : new_label
        ('activity', 'positive_point'): 'HAS_FEATURE',
        ('positive_point', 'activity'): 'HAS_FEATURE',
        ('activity', 'negative_point'): 'HAS_FEATURE',
        ('negative_point', 'activity'): 'HAS_FEATURE',
        ('activity', 'recommandation'): 'RECOMMENDS',
        ('recommandation', 'activity'): 'RECOMMENDS',
        ('user', 'user_preference'): 'LIKES',
        ('user_preference', 'user'): 'LIKES',
        ('user', 'user_attribute'): 'HAS_INFORMATION',
        ('user_attribute', 'user'): 'HAS_INFORMATION',
    }

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (
                neo4jExceptions.ServiceUnavailable,
                neo4jExceptions.TransientError,
                neo4jExceptions.WriteServiceUnavailable,
                neo4jExceptions.ClientError,
            )
        ),
    )
    async def upsert_node(self, node_id: str, node_data: Dict[str, Any]):
        """
        Upsert a node in the Neo4j database.

        Args:
            node_id: The unique identifier for the node
            node_data: Dictionary of node properties
        """
        # Vérification de la connexion
        if not self._driver:
            logger.error("❌ Connexion Neo4j non initialisée")
            return

        # Log TRÈS détaillé
        logger.info(f"🔍 DEBUG upsert_node - node_id: {node_id}")
        logger.info(f"🔍 DEBUG upsert_node - node_data BRUT: {node_data}")
        logger.info(f"🔍 DEBUG upsert_node - node_data keys: {list(node_data.keys())}")
        logger.info(f"🔍 DEBUG upsert_node - node_data types: {[type(val) for val in node_data.values()]}")

        # Validation des propriétés
        if "custom_id" in node_data:
            logger.info(f"🏷️ Custom ID trouvé pour le nœud {node_id}: {node_data['custom_id']}")

        # Vérifier que toutes les propriétés sont des types supportés par Neo4j
        for key, value in list(node_data.items()):
            if not isinstance(value, (str, int, float, bool, list)):
                logger.warning(f"⚠️ Propriété {key} de type {type(value)} non supportée par Neo4j, conversion en str")
                node_data[key] = str(value)

        # Ajout explicite du milvus_id s'il existe
        if 'milvus_id' in node_data:
            logger.info(f"🌟 Milvus ID trouvé : {node_data['milvus_id']}")
        else:
            logger.warning("❌ Aucun Milvus ID trouvé dans node_data")

        label = node_id.strip('"')
        logger.info(f"🏷️ Label du nœud : {label}")

        properties = node_data

        async def _do_upsert(tx: AsyncManagedTransaction):
            try:
                # Convertir toutes les propriétés en types supportés par Neo4j
                clean_properties = {}
                for key, value in properties.items():
                    if isinstance(value, (str, int, float, bool)):
                        clean_properties[key] = value
                    else:
                        clean_properties[key] = str(value)

                # Log détaillé des propriétés
                logger.info(f"🧹 clean_properties avant insertion: {clean_properties}")
                logger.info(f"🧹 clean_properties keys: {list(clean_properties.keys())}")

                query = f"""
                MERGE (n:`{label}`)
                SET n = $properties
                RETURN n
                """
                result = await tx.run(query, properties=clean_properties)
                record = await result.single()

                if record:
                    logger.info(f"✅ Nœud créé/mis à jour avec succès : {label}")
                    # Log du nœud inséré
                    node_record = record.data()['n']
                    logger.info(f"🔬 DEBUG nœud inséré : {node_record}")
                else:
                    logger.warning(f"⚠️ Aucun nœud créé pour : {label}")
            except Exception as e:
                logger.error(f"❌ Erreur lors de la création du nœud : {e}")
                raise

        try:
            async with self._driver.session() as session:
                await session.execute_write(_do_upsert)
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'exécution de la transaction : {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(
            (
                neo4jExceptions.ServiceUnavailable,
                neo4jExceptions.TransientError,
                neo4jExceptions.WriteServiceUnavailable,
            )
        ),
    )
    async def upsert_edge(
        self, source_node_id: str, target_node_id: str, edge_data: Dict[str, Any]
    ):
        """
        Upsert an edge and its properties between two nodes identified by their labels.

        Args:
            source_node_id (str): Label of the source node (used as identifier)
            target_node_id (str): Label of the target node (used as identifier)
            edge_data (dict): Dictionary of properties to set on the edge
        """
        source_node_label = source_node_id.strip('"')
        target_node_label = target_node_id.strip('"')
        edge_properties = edge_data

        async def _do_upsert_edge(tx: AsyncManagedTransaction):
            # Récupérer les types de nœuds source et target
            type_query = f"""
            MATCH (source:`{source_node_label}`), (target:`{target_node_label}`)
            RETURN 
                source.entity_type as source_type, 
                target.entity_type as target_type
            """
            
            result = await tx.run(type_query)
            type_record = await result.single()

            # Déterminer le type de relation
            new_label = 'DIRECTED'
            if type_record:
                source_type = type_record['source_type']
                target_type = type_record['target_type']

                # Recherche dynamique dans le mapping
                relation_key = (source_type, target_type)
                new_label = self.RELATION_TYPE_MAPPING.get(relation_key, 'DIRECTED')

            # Ajouter le type de relation aux propriétés
            edge_properties['type'] = new_label

            query = f"""
            MATCH (source:`{source_node_label}`)
            WITH source
            MATCH (target:`{target_node_label}`)
            MERGE (source)-[r:{new_label}]->(target)
            SET r += $properties
            RETURN r
            """
            await tx.run(query, properties=edge_properties)
            logger.debug(
                f"Upserted edge from '{source_node_label}' to '{target_node_label}' with type: {new_label}, properties: {edge_properties}"
            )

        try:
            async with self._driver.session() as session:
                await session.execute_write(_do_upsert_edge)
        except Exception as e:
            logger.error(f"Error during edge upsert: {str(e)}")
            raise

    async def _node2vec_embed(self):
        print("Implemented but never called.")

    async def categorize_activities(
        self, 
        activity_categories_manager, 
        use_model_func=None, 
        session=None
    ) -> Dict[str, int]:
        """
        Catégorise les activités dans la base de données Neo4j.
        
        Args:
            activity_categories_manager: Gestionnaire des catégories d'activités
            use_model_func: Fonction optionnelle pour générer des catégories via LLM
            session: Session Neo4j optionnelle
        
        Returns:
            Dictionnaire avec les compteurs de catégorisation
        """
        # Relation type mapping
        RELATION_TYPE_MAPPING = {
            ('activity', 'ActivityCategory'): 'CLASSIFIED_AS',
        }
        
        # Utiliser la session existante ou en créer une nouvelle
        if session is None:
            session = self._driver.session()
        
        async with session:
            # Initialiser les catégories prédéfinies
            init_query = """
            MERGE (restauration:ActivityCategory {name: 'Restauration'})
            MERGE (culture:ActivityCategory {name: 'Culture et Loisirs'})
            MERGE (sport:ActivityCategory {name: 'Sport et Fitness'})
            MERGE (voyage:ActivityCategory {name: 'Voyage et Tourisme'})
            MERGE (formation:ActivityCategory {name: 'Formation et Éducation'})
            MERGE (bienetre:ActivityCategory {name: 'Bien-être et Santé'})
            MERGE (pro:ActivityCategory {name: 'Événements Professionnels'})
            MERGE (unknown:ActivityCategory {name: 'Unknown'})
            
            // Requête pour récupérer les activités sans catégorie
            WITH 1 as dummy
            MATCH (n {entity_type: 'activity'})
            WHERE NOT (n)-[:CLASSIFIED_AS]->(:ActivityCategory)
            RETURN n.description as description, elementId(n) as node_id, labels(n) as node_labels
            """
            
            # Exécuter l'initialisation et récupérer les activités
            result = await session.run(init_query)
            activities = await result.data()
            
            # Compteurs de catégorisation
            categorization_counts = {
                'total': 0,
                'categorized': 0,
                'uncategorized': 0
            }
            
            for activity in activities:
                description = activity['description']
                node_id = activity['node_id']
                node_labels = activity['node_labels']
                
                # Utiliser le gestionnaire de catégories pour déterminer la catégorie
                if use_model_func:
                    category = await use_model_func(description)
                else:
                    category = activity_categories_manager.get_category(description)
                
                # Catégorisation par défaut si aucune catégorie n'est trouvée
                if not category:
                    category = 'Unknown'
                    categorization_counts['uncategorized'] += 1
                else:
                    categorization_counts['categorized'] += 1
                
                categorization_counts['total'] += 1
                
                # Requête pour créer la relation de catégorisation
                categorize_query = """
                MATCH (activity) WHERE elementId(activity) = $node_id
                WITH activity
                MATCH (cat:ActivityCategory {name: $category_name})
                MERGE (activity)-[r:CLASSIFIED_AS]->(cat)
                RETURN activity, cat
                """
                
                try:
                    await session.run(
                        categorize_query, 
                        node_id=node_id, 
                        category_name=category
                    )
                    logger.info(f"🏷️ Catégorisation de l'activité {node_id} dans la catégorie {category}")
                except Exception as e:
                    logger.error(f"❌ Erreur lors de la catégorisation de l'activité {node_id} : {e}")
            
            logger.info("📊 Résumé de la catégorisation :")
            logger.info(f"   - Total d'activités : {categorization_counts['total']}")
            logger.info(f"   - Activités catégorisées : {categorization_counts['categorized']}")
            logger.info(f"   - Activités non catégorisées : {categorization_counts['uncategorized']}")
            
            return categorization_counts

    async def merge_duplicate_users(self):
        """
        Fusionne les nœuds utilisateurs qui ont le même custom_id.
        Conserve toutes les relations existantes.
        """
        if not self._driver:
            logger.error("❌ Connexion Neo4j non initialisée")
            return

        async def _do_merge(tx):
            # Trouver les custom_id qui ont des doublons
            find_duplicates_query = """
            MATCH (u:user)
            WHERE u.custom_id IS NOT NULL
            WITH u.custom_id as cid, collect(u) as users
            WHERE size(users) > 1
            RETURN cid, users
            """
            
            result = await tx.run(find_duplicates_query)
            records = await result.records()  # Utiliser records() au lieu de fetch()
            
            for record in records:
                custom_id = record["cid"]
                users = record["users"]
                logger.info(f"Fusion des utilisateurs avec custom_id: {custom_id}")
                
                # Garder le premier nœud et fusionner les autres
                primary_user = users[0]
                duplicate_users = users[1:]
                
                for duplicate in duplicate_users:
                    # Transférer toutes les relations entrantes
                    merge_in_query = """
                    MATCH (duplicate) WHERE id(duplicate) = $duplicate_id
                    MATCH (primary) WHERE id(primary) = $primary_id
                    MATCH (source)-[r]->(duplicate)
                    WHERE NOT source = primary
                    CALL apoc.merge.relationship(source, type(r), r.properties, primary) YIELD rel
                    DELETE r
                    """
                    
                    # Transférer toutes les relations sortantes
                    merge_out_query = """
                    MATCH (duplicate) WHERE id(duplicate) = $duplicate_id
                    MATCH (primary) WHERE id(primary) = $primary_id
                    MATCH (duplicate)-[r]->(target)
                    WHERE NOT target = primary
                    CALL apoc.merge.relationship(primary, type(r), r.properties, target) YIELD rel
                    DELETE r
                    """
                    
                    # Supprimer le nœud dupliqué
                    delete_query = """
                    MATCH (n) WHERE id(n) = $node_id
                    DETACH DELETE n
                    """
                    
                    params = {
                        "duplicate_id": duplicate.id,
                        "primary_id": primary_user.id,
                        "node_id": duplicate.id
                    }
                    
                    try:
                        await tx.run(merge_in_query, params)
                        await tx.run(merge_out_query, params)
                        await tx.run(delete_query, params)
                        logger.info(f"✅ Nœud fusionné et supprimé: {duplicate.id}")
                    except Exception as e:
                        logger.error(f"❌ Erreur lors de la fusion du nœud {duplicate.id}: {str(e)}")

        try:
            async with self._driver.session() as session:
                await session.execute_write(_do_merge)
                logger.info("✅ Fusion des utilisateurs terminée")
        except Exception as e:
            logger.error(f"❌ Erreur lors de la fusion des utilisateurs: {str(e)}")