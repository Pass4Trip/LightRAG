import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
import openai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import json

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialiser la console rich
console = Console()

# Charger les variables d'environnement
load_dotenv()


class Neo4jQuery:
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
                return result
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

class UserContextEnhancer:
    def __init__(self, neo4j_query, openai_api_key=None):
        """
        Initialise l'amélioration du contexte utilisateur
        
        Args:
            neo4j_query (Neo4jQuery): Instance de requête Neo4j
            openai_api_key (str, optional): Clé API OpenAI
        """
        self.neo4j_query = neo4j_query
        
        # Configuration OpenAI
        openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            client = openai.OpenAI(api_key=openai_api_key)
        else:
            logger.warning("Pas de clé OpenAI fournie. Certaines fonctionnalités seront limitées.")
            client = None
        
        self.openai_client = client

    def extract_user_preferences(self, username, query_context=None):
        """
        Extrait les préférences et attributs d'un utilisateur avec leurs relations
        
        Args:
            username (str): Nom de l'utilisateur
            query_context (str, optional): Contexte de la requête pour affinage
        
        Returns:
            dict: Informations détaillées sur l'utilisateur
        """
        # Requête Cypher enrichie pour capturer les relations et leurs propriétés
        cypher_query = """
        MATCH (u {entity_type: "user", custom_id: $username})
        OPTIONAL MATCH (u)-[r:LIKES|HAS_INFORMATION]-(related)
        RETURN 
            u as user,
            collect({
                entity: related, 
                relation_type: type(r), 
                relation_description: r.description, 
                relation_keywords: r.keywords,
                relation_weight: r.weight
            }) as related_entities
        """
        
        try:
            with self.neo4j_query.driver.session() as session:
                result = session.run(cypher_query, {"username": username})
                record = result.single()
                
                if not record:
                    logger.warning(f"Aucune information trouvée pour l'utilisateur {username}")
                    return {}
                
                # Structurer les informations de manière plus riche
                user_info = {
                    "user_details": dict(record["user"]),
                    "relationships": []
                }
                
                # Traiter les entités liées
                for rel in record["related_entities"]:
                    relationship = {
                        "entity": dict(rel['entity']),
                        "relation_type": rel['relation_type'],
                        "relation_description": rel['relation_description'],
                        "relation_keywords": rel['relation_keywords'],
                        "relation_weight": rel['relation_weight']
                    }
                    user_info["relationships"].append(relationship)
                
                # Catégoriser les relations
                user_info["preferences"] = [
                    rel for rel in user_info["relationships"] 
                    if rel['relation_type'] == 'LIKES'
                ]
                user_info["attributes"] = [
                    rel for rel in user_info["relationships"] 
                    if rel['relation_type'] == 'HAS_INFORMATION'
                ]
                
                # Enrichissement direct de la requête avec les préférences de l'utilisateur
                user_info = self._refine_user_context(user_info, query_context)
                
                return user_info
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des préférences : {e}")
            return {}

    def _refine_user_context(self, user_info, query_context):
        """
        Enrichit la requête en utilisant toutes les informations de l'utilisateur
        
        Args:
            user_info (dict): Informations complètes de l'utilisateur depuis Neo4j
            query_context (str): Contexte de la requête initiale
        
        Returns:
            dict: Informations utilisateur avec requête enrichie
        """
        # Collecter TOUTES les informations disponibles
        all_user_info = []
        
        # Préférences
        for pref in user_info.get('preferences', []):
            description = pref['entity'].get('description', '')
            keywords = pref.get('relation_keywords', [])
            all_user_info.append({
                'type': 'Préférence',
                'description': description,
                'keywords': keywords
            })
        
        # Attributs
        for attr in user_info.get('attributes', []):
            description = attr['entity'].get('description', '')
            keywords = attr.get('relation_keywords', [])
            all_user_info.append({
                'type': 'Attribut',
                'description': description,
                'keywords': keywords
            })
        
        # Détails utilisateur
        user_details = user_info.get('user_details', {})
        all_user_info.append({
            'type': 'Détails Utilisateur',
            'description': user_details.get('description', ''),
            'keywords': user_details.get('keywords', [])
        })
        
        # Préparer le prompt pour GPT-4o-mini
        prompt = f"""
Contexte de recherche : Personnalisation d'une requête de restaurant

Requête originale : "{query_context}"

Informations utilisateur complètes :
{json.dumps(all_user_info, indent=2)}

Objectif : 
1. Analyse toutes les informations disponibles
2. Sélectionne uniquement les éléments pertinents pour enrichir la requête
3. Crée une requête naturelle qui intègre subtilement les préférences

Critères de sélection :
- Pertinence par rapport à la recherche de restaurant
- Impact potentiel sur le choix du restaurant
- Clarté et concision de l'enrichissement

Fournis une requête enrichie qui guide efficacement la recherche, 
en mettant en valeur les aspects les plus significatifs des préférences de l'utilisateur.
"""
        
        try:
            # Utiliser GPT-4o-mini pour générer la requête enrichie
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant expert en personnalisation de requêtes de recherche."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.7
            )
            
            # Récupérer la requête enrichie
            enriched_query = response.choices[0].message.content.strip()
            
            # Fallback si la génération échoue
            if not enriched_query:
                enriched_query = query_context
            
            user_info['enriched_query'] = enriched_query
            return user_info
        
        except Exception as e:
            logger.error(f"Erreur lors de l'enrichissement de la requête : {e}")
            user_info['enriched_query'] = query_context
            return user_info

def main():
    # Initialisation des composants
    graphQuery = Neo4jQuery()
    enhancer = UserContextEnhancer(graphQuery)
    
    # Exemple de requête de restaurant
    username = "lea"
    query_context = "Je cherche un restaurant pour ce soir"
    
    # Récupérer les préférences utilisateur
    user_preferences = enhancer.extract_user_preferences(username, query_context)
    
    # Question initiale
    console.print(Panel(
        Markdown(f"""
### 🔍 Requête Initiale
**Utilisateur**: {username}
**Question**: {query_context}
"""),
        title="Contexte de la Recherche",
        border_style="bold yellow"
    ))
    
    # Affichage riche et coloré
    console.print(Panel.fit(
        Markdown("## 🍽️ Profil Utilisateur : Lea"),
        title="Analyse de Préférences Culinaires",
        border_style="bold blue"
    ))
    
    # Détails utilisateur
    console.print(Panel(
        Markdown(f"""
### Détails de l'Utilisateur
- **ID Personnalisé**: {user_preferences['user_details']['custom_id']}
- **Description**: {user_preferences['user_details']['description']}
"""),
        title="Informations Personnelles",
        border_style="green"
    ))
    
    # Préférences
    console.print(Panel(
        Markdown("### Préférences Culinaires\n" + "\n".join([
            f"- 🍕 **{pref['entity']['description']}** (Poids: {pref['relation_weight']})"
            for pref in user_preferences.get('preferences', [])
        ])),
        title="Goûts et Passions",
        border_style="bold magenta"
    ))
    
    # Requête enrichie
    console.print(Panel(
        Markdown(f"""
### Requête Enrichie
{user_preferences.get('enriched_query', 'Aucune requête enrichie disponible')}
"""),
        title="🌟 Requête Enrichie",
        border_style="bold green"
    ))

if __name__ == "__main__":
    main()
