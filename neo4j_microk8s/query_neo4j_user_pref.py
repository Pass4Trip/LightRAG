import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase
import openai
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
import json
import base64
from kubernetes import client, config

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

def get_api_key_from_kubernetes_secret(secret_name='openai-api-key', secret_key='OPENAI_API_KEY'):
    """
    Récupère une clé API depuis un secret Kubernetes.
    
    Args:
        secret_name (str, optional): Nom du secret Kubernetes. Défaut à 'openai-api-key'.
        secret_key (str, optional): Clé dans le secret. Défaut à 'OPENAI_API_KEY'.
    
    Returns:
        str: Clé API décodée, ou chaîne vide si non trouvée.
    """
    try:
        from kubernetes import client, config
        import base64
        
        # Charger la configuration Kubernetes
        try:
            config.load_incluster_config()  # Pour les pods dans le cluster
        except config.ConfigException:
            config.load_kube_config()  # Pour le développement local
        
        # Récupérer le secret
        v1 = client.CoreV1Api()
        secret = v1.read_namespaced_secret(secret_name, 'default')
        
        # Décoder la clé API du secret
        api_key = base64.b64decode(secret.data.get(secret_key, '')).decode('utf-8').strip()
        
        return api_key
    except Exception as e:
        logger.error(f"Impossible de récupérer la clé API depuis le secret Kubernetes : {e}")
        return ''

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
        
        # Si la clé est vide, essayer de la récupérer depuis le secret Kubernetes
        if not openai_api_key:
            openai_api_key = get_api_key_from_kubernetes_secret()
        
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
        Enrichit la requête en utilisant les informations de l'utilisateur
        
        Args:
            user_info (dict): Informations de l'utilisateur depuis Neo4j
            query_context (str): Contexte de la requête initiale
        
        Returns:
            dict: Informations utilisateur avec suggestions
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
Contexte de recherche : Suggestions de restaurants basées sur les préférences utilisateur

Requête originale : "{query_context}"

Informations utilisateur extraites de Neo4j :
{json.dumps(all_user_info, indent=2)}

Objectif : 
1. Utiliser UNIQUEMENT les informations factuelles de l'utilisateur
2. Filtrer les données pertinentes pour la recherche de restaurant
3. Proposer des suggestions basées strictement sur les préférences existantes

Consignes de filtrage :
- Ne pas inventer ou déduire de nouvelles préférences
- Extraire uniquement les informations directement liées à la recherche de restaurant
- Rester factuel et précis

Format de réponse attendu :
- Une phrase d'introduction commençant par "💡 Options bonus :"
- Liste à puces des suggestions basées SUR LES DONNÉES EXISTANTES
- Ton : Neutre et informatif
- Suggestions extraites directement des préférences utilisateur

Exemple de filtrage :
- Si "cuisine végétarienne" est une préférence : suggérer des restaurants végétariens
- Si "ambiance décontractée" est présente : mentionner des lieux avec cette atmosphère

Contraintes importantes :
- AUCUNE suggestion qui ne provient pas directement des données
- Utiliser uniquement les descriptions et mots-clés existants
- Garder les suggestions courtes et factuelles

Exemple complet de traitement :
🔍 Question Initiale : "Je cherche un restaurant"
👤 Données Neo4j :
- Préférence : "Cuisine végétarienne"
- Attribut : "Budget modéré"
- Mot-clé : "Alimentation durable"

💡 Suggestions attendues :
- Restaurants végétariens correspondant à un budget modéré
- Établissements proposant une cuisine respectueuse de l'environnement

📝 Requête enrichie finale :
"Je cherche un restaurant. 💡 Options bonus : Restaurants végétariens à prix modéré, avec une approche durable."
"""
        
        try:
            # Utiliser GPT-4o-mini pour générer les suggestions
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Tu es un assistant qui filtre et présente des suggestions de restaurants basées uniquement sur les données existantes."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.5  # Réduire la température pour plus de précision
            )
            
            # Récupérer les suggestions
            suggestions = response.choices[0].message.content.strip()
            
            # Fallback si la génération échoue
            if not suggestions:
                suggestions = "💡 Options bonus : Aucune suggestion spécifique basée sur vos préférences."
            
            # Générer la requête enrichie finale
            requete_enrichie = f"{query_context}. {suggestions}"
            
            user_info['restaurant_suggestions'] = suggestions
            user_info['requete_enrichie'] = requete_enrichie
            return user_info
        
        except Exception as e:
            logger.error(f"Erreur lors de la génération des suggestions : {e}")
            user_info['restaurant_suggestions'] = "💡 Options bonus : Aucune suggestion spécifique basée sur vos préférences."
            user_info['requete_enrichie'] = query_context
            return user_info

def main(username=None):
    # Initialisation des composants
    graphQuery = Neo4jQuery()
    enhancer = UserContextEnhancer(graphQuery)
    
    # Utiliser le nom d'utilisateur passé en argument ou par défaut
    if username is None:
        username = "lea"
    
    # Exemple de requête de restaurant
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
        Markdown(f"## 🍽️ Profil Utilisateur : {username.capitalize()}"),
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
    
    # Suggestions
    console.print(Panel(
        Markdown(f"""
### Suggestions de Restaurants
{user_preferences.get('restaurant_suggestions', 'Aucune suggestion disponible')}
"""),
        title="💡 Suggestions",
        border_style="bold green"
    ))
    
    # Requête enrichie finale
    console.print(Panel(
        Markdown(f"""
### Requête Enrichie
{user_preferences.get('requete_enrichie', 'Aucune requête enrichie disponible')}
"""),
        title="💡 Requête Enrichie",
        border_style="bold green"
    ))

if __name__ == "__main__":
    import sys
    
    # Permettre de passer le nom d'utilisateur en argument
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
