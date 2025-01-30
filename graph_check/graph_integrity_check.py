import os
import logging
import traceback
from typing import List, Dict, Any

import sshtunnel
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

# Configuration du logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/Users/vinh/Documents/LightRAG/graph_check/graph_integrity.log'
)
logger = logging.getLogger(__name__)

class GraphIntegrityChecker:
    def __init__(self, ssh_host='51.77.200.196', neo4j_host='10.1.77.8', neo4j_port=7687):
        """
        Initialise le vérificateur d'intégrité du graphe
        """
        self.ssh_host = ssh_host
        self.neo4j_host = neo4j_host
        self.neo4j_port = neo4j_port
        self.tunnel = None
        self.driver = None

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

    def check_node_integrity(self) -> Dict[str, Any]:
        """
        Vérifie l'intégrité des nœuds dans le graphe
        """
        if not self._connect_to_neo4j():
            return {"error": "Impossible de se connecter"}

        try:
            with self.driver.session() as session:
                # Requête pour identifier les nœuds problématiques
                query = """
                MATCH (n)
                WHERE 
                    n.name IS NULL OR 
                    size(labels(n)) = 0
                RETURN 
                    labels(n) AS node_labels, 
                    count(*) AS problematic_count,
                    collect(properties(n)) AS sample_properties
                LIMIT 100
                """
                
                result = session.run(query)
                problematic_nodes = [
                    {
                        "labels": record["node_labels"],
                        "count": record["problematic_count"],
                        "sample_properties": record["sample_properties"]
                    } for record in result
                ]

                return {
                    "problematic_nodes": problematic_nodes,
                    "total_problematic_nodes": sum(node["count"] for node in problematic_nodes)
                }
        
        except Neo4jError as e:
            logger.error(f"Erreur Neo4j lors de la vérification des nœuds : {e}")
            return {"error": str(e)}
        
        finally:
            self._close_connections()

    def check_relationship_integrity(self) -> Dict[str, Any]:
        """
        Vérifie l'intégrité des relations dans le graphe
        """
        if not self._connect_to_neo4j():
            return {"error": "Impossible de se connecter"}

        try:
            with self.driver.session() as session:
                # Requête pour identifier les relations problématiques
                query = """
                MATCH (start)-[r]->(end)
                WHERE 
                    start IS NULL OR 
                    end IS NULL OR 
                    keys(r) = []
                RETURN 
                    type(r) AS relation_type, 
                    count(*) AS problematic_count,
                    collect({
                        start_node: start.name,
                        start_labels: labels(start),
                        end_node: end.name,
                        end_labels: labels(end),
                        relation_properties: keys(r)
                    }) AS sample_details
                LIMIT 100
                """
                
                result = session.run(query)
                problematic_relations = [
                    {
                        "type": record["relation_type"],
                        "count": record["problematic_count"],
                        "samples": record["sample_details"]
                    } for record in result
                ]

                return {
                    "problematic_relations": problematic_relations,
                    "total_problematic_relations": sum(rel["count"] for rel in problematic_relations)
                }
        
        except Neo4jError as e:
            logger.error(f"Erreur Neo4j lors de la vérification des relations : {e}")
            return {"error": str(e)}
        
        finally:
            self._close_connections()

    def generate_integrity_report(self):
        """
        Génère un rapport complet sur l'intégrité du graphe
        """
        logger.info("Début de la génération du rapport d'intégrité")
        
        node_integrity = self.check_node_integrity()
        relationship_integrity = self.check_relationship_integrity()
        
        report_path = '/Users/vinh/Documents/LightRAG/graph_check/integrity_report.md'
        
        with open(report_path, 'w') as f:
            f.write("# Rapport d'Intégrité du Graphe Neo4j\n\n")
            
            # Rapport sur les nœuds
            f.write("## Intégrité des Nœuds\n")
            if "error" in node_integrity:
                f.write(f"**Erreur :** {node_integrity['error']}\n")
            else:
                f.write(f"Total de nœuds problématiques : {node_integrity['total_problematic_nodes']}\n\n")
                for node in node_integrity.get('problematic_nodes', []):
                    f.write(f"### Labels : {node['labels']}\n")
                    f.write(f"Nombre de nœuds : {node['count']}\n")
                    f.write("Exemples de propriétés :\n")
                    for prop in node['sample_properties'][:3]:
                        f.write(f"- {prop}\n")
                    f.write("\n")
            
            # Rapport sur les relations
            f.write("## Intégrité des Relations\n")
            if "error" in relationship_integrity:
                f.write(f"**Erreur :** {relationship_integrity['error']}\n")
            else:
                f.write(f"Total de relations problématiques : {relationship_integrity['total_problematic_relations']}\n\n")
                for relation in relationship_integrity.get('problematic_relations', []):
                    f.write(f"### Type de Relation : {relation['type']}\n")
                    f.write(f"Nombre de relations : {relation['count']}\n")
                    f.write("Échantillons :\n")
                    for sample in relation['samples'][:3]:
                        f.write(f"- Départ : {sample['start_node']} (Labels: {sample['start_labels']})\n")
                        f.write(f"  Arrivée : {sample['end_node']} (Labels: {sample['end_labels']})\n")
                        f.write(f"  Propriétés : {sample['relation_properties']}\n")
                    f.write("\n")
        
        logger.info(f"Rapport d'intégrité généré : {report_path}")
        return report_path

def main():
    checker = GraphIntegrityChecker()
    checker.generate_integrity_report()

if __name__ == "__main__":
    main()
