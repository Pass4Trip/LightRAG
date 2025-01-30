import os
import logging
import json
from typing import List, Dict, Any

import sshtunnel
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/Users/vinh/Documents/LightRAG/graph_check/detailed_graph_problems.log'
)
logger = logging.getLogger(__name__)

class GraphProblemDetector:
    def __init__(self, ssh_host='51.77.200.196', neo4j_host='10.1.77.8', neo4j_port=7687):
        """
        Initialise le détecteur de problèmes de graphe
        """
        self.ssh_host = ssh_host
        self.neo4j_host = neo4j_host
        self.neo4j_port = neo4j_port
        self.tunnel = None
        self.driver = None
        self.problems = {
            'nodes': [],
            'relationships': []
        }

    def _establish_ssh_tunnel(self):
        """
        Établit un tunnel SSH sécurisé vers le serveur Neo4j
        """
        try:
            self.tunnel = sshtunnel.SSHTunnelForwarder(
                (self.ssh_host, 22),
                ssh_username='ubuntu',
                remote_bind_address=(self.neo4j_host, self.neo4j_port)
            )
            self.tunnel.start()
            logger.info("Tunnel SSH établi avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'établissement du tunnel SSH : {e}")
            return False

    def _connect_to_neo4j(self):
        """
        Connexion à la base de données Neo4j via le tunnel SSH
        """
        try:
            if not self._establish_ssh_tunnel():
                return False

            uri = f"bolt://{self.tunnel.local_bind_host}:{self.tunnel.local_bind_port}"
            username = "neo4j"
            password = os.getenv('NEO4J_PASSWORD', 'my-initial-password')

            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            logger.info("Connexion à Neo4j réussie")
            return True
        except Exception as e:
            logger.error(f"Erreur de connexion à Neo4j : {e}")
            return False

    def _close_connections(self):
        """
        Ferme les connexions SSH et Neo4j
        """
        if self.driver:
            self.driver.close()
            logger.info("Connexion Neo4j fermée")
        
        if self.tunnel:
            self.tunnel.close()
            logger.info("Tunnel SSH fermé")

    def detect_problematic_nodes(self):
        """
        Détecte les nœuds problématiques avec des détails précis
        """
        if not self._connect_to_neo4j():
            return []

        try:
            with self.driver.session() as session:
                # Requête détaillée pour identifier les nœuds problématiques
                query = """
                MATCH (n)
                WHERE 
                    n.name IS NULL OR 
                    size(labels(n)) = 0 OR
                    all(prop IN keys(n) WHERE n[prop] IS NULL)
                RETURN 
                    id(n) AS node_id,
                    labels(n) AS node_labels, 
                    properties(n) AS node_properties,
                    size(labels(n)) AS label_count,
                    size(keys(n)) AS property_count
                LIMIT 200
                """
                
                result = session.run(query)
                problematic_nodes = []

                for record in result:
                    node_problem = {
                        'node_id': record['node_id'],
                        'labels': record['node_labels'],
                        'properties': record['node_properties'],
                        'label_count': record['label_count'],
                        'property_count': record['property_count'],
                        'problem_reasons': []
                    }

                    # Déterminer les raisons spécifiques des problèmes
                    if record['node_labels'] is None or record['label_count'] == 0:
                        node_problem['problem_reasons'].append('Absence de labels')
                    
                    if record['node_properties'] is None or record['property_count'] == 0:
                        node_problem['problem_reasons'].append('Absence de propriétés')
                    
                    if record.get('node_properties', {}).get('name') is None:
                        node_problem['problem_reasons'].append('Propriété name manquante')

                    problematic_nodes.append(node_problem)

                self.problems['nodes'] = problematic_nodes
                return problematic_nodes
        
        except Neo4jError as e:
            logger.error(f"Erreur Neo4j lors de la détection des nœuds : {e}")
            return []
        
        finally:
            self._close_connections()

    def detect_problematic_relationships(self):
        """
        Détecte les relations problématiques avec des détails précis
        """
        if not self._connect_to_neo4j():
            return []

        try:
            with self.driver.session() as session:
                # Requête détaillée pour identifier les relations problématiques
                query = """
                MATCH (start)-[r]->(end)
                WHERE 
                    start IS NULL OR 
                    end IS NULL OR 
                    keys(r) = [] OR
                    all(prop IN keys(r) WHERE r[prop] IS NULL)
                RETURN 
                    type(r) AS relation_type,
                    id(r) AS relation_id,
                    start.name AS start_node_name,
                    end.name AS end_node_name,
                    labels(start) AS start_labels,
                    labels(end) AS end_labels,
                    properties(r) AS relation_properties
                LIMIT 200
                """
                
                result = session.run(query)
                problematic_relations = []

                for record in result:
                    relation_problem = {
                        'relation_type': record['relation_type'],
                        'relation_id': record['relation_id'],
                        'start_node': {
                            'name': record['start_node_name'],
                            'labels': record['start_labels']
                        },
                        'end_node': {
                            'name': record['end_node_name'],
                            'labels': record['end_labels']
                        },
                        'properties': record['relation_properties'],
                        'problem_reasons': []
                    }

                    # Déterminer les raisons spécifiques des problèmes
                    if record['start_node_name'] is None:
                        relation_problem['problem_reasons'].append('Nœud de départ sans nom')
                    
                    if record['end_node_name'] is None:
                        relation_problem['problem_reasons'].append('Nœud de destination sans nom')
                    
                    if not record['relation_properties']:
                        relation_problem['problem_reasons'].append('Relation sans propriétés')

                    problematic_relations.append(relation_problem)

                self.problems['relationships'] = problematic_relations
                return problematic_relations
        
        except Neo4jError as e:
            logger.error(f"Erreur Neo4j lors de la détection des relations : {e}")
            return []
        
        finally:
            self._close_connections()

    def generate_detailed_report(self):
        """
        Génère un rapport détaillé des problèmes dans le graphe
        """
        logger.info("Début de la génération du rapport détaillé")
        
        # Détecter les problèmes
        self.detect_problematic_nodes()
        self.detect_problematic_relationships()
        
        # Chemin du rapport
        report_path = '/Users/vinh/Documents/LightRAG/graph_check/detailed_graph_problems.json'
        
        # Sauvegarder le rapport au format JSON
        with open(report_path, 'w') as f:
            json.dump(self.problems, f, indent=2)
        
        logger.info(f"Rapport détaillé généré : {report_path}")
        
        # Résumé des problèmes
        print("🔍 Résumé des Problèmes du Graphe :")
        print(f"- Nœuds problématiques : {len(self.problems['nodes'])}")
        print(f"- Relations problématiques : {len(self.problems['relationships'])}")
        
        return report_path

def main():
    detector = GraphProblemDetector()
    detector.generate_detailed_report()

if __name__ == "__main__":
    main()
