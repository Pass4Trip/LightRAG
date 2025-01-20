# Imports système et configuration de base
from pathlib import Path
import sys
import logging
import traceback
import uuid
from datetime import datetime

# Imports FastAPI et Pydantic
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

# Ajout du chemin parent pour importer LightRAG
sys.path.append(str(Path(__file__).parent.parent))

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports LightRAG
from lightrag.lightrag import LightRAG
from lightrag.llm import gpt_4o_mini_complete

class MessageProcessor:
    def __init__(self):
        self.rag = None
        try:
            # Utiliser MilvusVectorDBStorage explicitement
            self.rag = LightRAG(
                working_dir=str(Path(__file__).parent.parent / "api"),
                llm_model_func=gpt_4o_mini_complete,
                vector_storage="MilvusVectorDBStorage",
                kv_storage="MongoKVStorage",
                graph_storage="Neo4JStorage",
                log_level=logging.INFO,
                enable_llm_cache=False
            )
            logger.info("LightRAG initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur d'initialisation de LightRAG : {e}")
            logger.error(traceback.format_exc())
            self.rag = None

    async def process_user_message(self, payload: dict):
        """
        Traite les messages de type 'user'
        
        Args:
            payload (dict): Charge utile du message
        """
        try:
            text = payload.get('user_info', '')
            user_id = payload.get('user_id')
            
            if not text:
                logger.warning("Message utilisateur vide")
                return
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                text, 
                prompt_domain='user',
                metadata={'user_id': user_id} if user_id else None
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message utilisateur: {e}")
            logger.error(traceback.format_exc())

    async def process_activity_message(self, payload: dict):
        """
        Traite les messages de type 'activity'
        
        Args:
            payload (dict): Charge utile du message
        """
        try:
            resume = payload.get('resume')
            cid = payload.get('cid')
            city = payload.get('city')
            lat = payload.get('lat')
            lng = payload.get('lng')
            
            if not resume or not cid:
                logger.warning(f"Message activity incomplet: {payload}")
                return
            
            # Préparer les métadonnées
            metadata = {
                'cid': cid,
                'city': city,
                'custom_id': f"{cid}"  # Utiliser cid comme custom_id
            }
            
            # Ajouter les coordonnées si disponibles
            if lat is not None and lng is not None:
                metadata['lat'] = lat
                metadata['lng'] = lng
                logger.info(f"Coordonnées ajoutées pour l'activité : {lat}, {lng}")
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                resume, 
                prompt_domain='activity',
                metadata={
                    'cid': cid,
                    'city': city,
                    'custom_id': f"{cid}",
                    'lat': payload.get('lat'),
                    'lng': payload.get('lng')
                }
            )
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message d'activité: {e}")
            logger.error(traceback.format_exc())

    async def process_event_message(self, payload: dict):
        """
        Traite les messages de type 'event'
        
        Args:
            payload (dict): Charge utile du message d'événement
        """
        try:
            # Extraction des attributs de l'événement
            event_id = payload.get('event_id')
            description = payload.get('description', 'Événement sans description')
            start_date = payload.get('start_date')
            end_date = payload.get('end_date')
            city = payload.get('city')
            
            if not event_id or not description:
                logger.warning(f"Message event incomplet: {payload}")
                return
            
            # Convertir l'ID en chaîne et le normaliser
            event_id_str = str(event_id)
            normalized_event_id = self.normalize_label(event_id_str)
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                description, 
                prompt_domain='event',
                metadata={
                    'event_id': normalized_event_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'city': city,
                    'custom_id': normalized_event_id  # Utiliser event_id normalisé comme custom_id
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message d'événement: {e}")
            logger.error(traceback.format_exc())

    async def process_memo_message(self, payload: dict):
        """
        Traite les messages de type 'memo'
        
        Args:
            payload (dict): Charge utile du message de mémo
        """
        try:
            # Extraction des attributs du mémo
            memo_id = payload.get('memo_id')
            description = payload.get('description', 'Mémo sans description')
            user_id = payload.get('user_id')  # Récupérer l'ID de l'utilisateur
            
            if not memo_id or not description:
                logger.warning(f"Message memo incomplet: {payload}")
                return
            
            # Convertir l'ID en chaîne et le normaliser
            memo_id_str = str(memo_id)
            normalized_memo_id = self.normalize_label(memo_id_str)
            
            # Normaliser l'ID utilisateur si présent
            normalized_user_id = self.normalize_label(str(user_id)) if user_id else None
            
            # Insertion avec le prompt_domain et metadata
            await self.insert_to_lightrag(
                description, 
                prompt_domain='memo',
                metadata={
                    'memo_id': normalized_memo_id,
                    'custom_id': normalized_memo_id,  # Utiliser memo_id normalisé comme custom_id
                    'user_id': normalized_user_id  # Ajouter l'ID utilisateur normalisé
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message de mémo: {e}")
            logger.error(traceback.format_exc())

    async def process_query_message(self, payload: dict):
        """
        Traite les messages de type 'query'
        
        Args:
            payload (dict): Dictionnaire contenant les informations de la requête
        """
        try:
            # Récupération du custom_id
            custom_id = payload.get('custom_id')
            if not custom_id:
                logger.warning("Aucun custom_id trouvé dans le message de query")
                return

            # Autres traitements existants
            user_id = payload.get('user_id', 'user_id_example')
            response = payload.get('response')
            timestamp = payload.get('timestamp')

            logger.info(f"Traitement de la query avec custom_id: {custom_id}")
            
            # Le reste du code de traitement reste inchangé
            metadata = {
                'custom_id': custom_id,
                'user_id': user_id,
                'timestamp': timestamp
            }

            # Insérer la query dans le système
            await self.insert_to_lightrag(
                response, 
                prompt_domain='query',
                metadata=metadata
            )

        except Exception as e:
            logger.error(f"Erreur lors du traitement du message de query: {e}")
            logger.error(traceback.format_exc())

    async def process_message(self, payload: Dict[str, Any]):
        """
        Traite un message JSON brut sans retraitement
        
        Args:
            payload (dict): Charge utile du message
        
        Returns:
            Résultat du traitement du message
        """
        try:
            # Récupérer le type de message
            message_type = payload.get('type', 'activity')
            logger.info(f"Type de message reçu: {message_type}")
            logger.debug(f"Contenu du payload: {payload}")
            
            # Dispatcher vers le bon gestionnaire de message
            message_processors = {
                'user': self.process_user_message,
                'activity': self.process_activity_message,
                'event': self.process_event_message,
                'memo': self.process_memo_message,
                'query': self.process_query_message
            }
            
            # Sélectionner le processeur approprié
            processor = message_processors.get(message_type, self.process_activity_message)
            
            # Traiter le message
            return await processor(payload)
        
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message : {e}")
            logger.error(traceback.format_exc())
            raise

    def normalize_label(self, text: str) -> str:
        """Normalise un texte pour l'utiliser comme label."""
        return text.replace(" ", "_").upper()

    async def insert_to_lightrag(self, text: str, prompt_domain: str = 'activity', metadata: dict = None):
        """
        Méthode d'insertion asynchrone dans LightRAG
        
        :param text: Texte à insérer
        :param prompt_domain: Domaine du prompt
        :param metadata: Métadonnées optionnelles
        :return: Résultat de l'insertion
        """
        try:
            if self.rag is None:
                raise ValueError("LightRAG n'a pas été correctement initialisé")

            # Préparer les métadonnées
            if metadata is None:
                metadata = {}
            
            # Générer un identifiant unique si non fourni
            metadata['id'] = metadata.get('id', str(uuid.uuid4()))
            
            # Insérer le texte
            result = await self.rag.ainsert(
                text, 
                prompt_domain=prompt_domain, 
                metadata=metadata
            )
            
            logger.info(f"Insertion réussie dans LightRAG : {metadata['id']}")
            return result

        except Exception as e:
            logger.error(f"Erreur lors de l'insertion dans LightRAG: {e}")
            logger.error(traceback.format_exc())
            raise

# Créer une instance unique du processeur de messages
message_processor = MessageProcessor()

# Créer un router pour cet API
router = APIRouter()

@router.post("/")
async def insert_message(payload: Dict[str, Any]):
    """
    Endpoint pour insérer un message dans LightRAG

    Args:
        payload (Dict[str, Any]): Données JSON à traiter

    Returns:
        Dict[str, Any]: Résultat de l'insertion

    Raises:
        HTTPException: En cas d'erreur lors du traitement
    """
    try:
        # Insérer le message dans LightRAG
        # Logging des données reçues
        logger.info(f"Données reçues : {payload}")
        
        result = await message_processor.process_message(payload)

        return {
            "status": "success",
            "result": result
        }

    except Exception as e:
        logger.error(f"Erreur lors de l'insertion du message : {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))