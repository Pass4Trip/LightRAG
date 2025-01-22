import requests
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URL de l'endpoint
API_LIGHTRAG_URL = 'http://51.77.200.196:30080/insert'

def test_endpoint():
    """
    Teste l'endpoint de l'API LightRAG avec un exemple de payload
    """
    try:
        # Payload exact du Swagger
        payload = {
            "type": "activity", 
            "cid": "16204433116771456015", 
            "restaurant_id": 2, 
            "resume": "###cid=16204433116771456015###    Résumé du Restaurant : CAFÉ LISBOA\n\nCafé Lisboa est un restaurant coloré de style décontracté situé dans le centre de Lyon, offrant une terrasse agréable pour profiter de repas en extérieur. Il se spécialise dans la cuisine portugaise, servant des petites assiettes et des tartes à la crème, avec une fourchette de prix allant de 20 à 30 euros. \n\nAmbiance et Atmosphère :\nLa plupart des avis récents décrivent l'ambiance comme chaleureuse et conviviale, avec une belle terrasse et un décor typiquement portugais. Les clients apprécient le cadre cosy, bien qu'il soit parfois jugé un peu trop bondé. Un consensus se dégage autour de l'invitation à profiter de l'atmosphère décontractée, idéale pour un repas entre amis ou en famille.\n\nGamme de Prix et Rapport Qualité-Prix :\nLes prix sont considérés comme raisonnables, et plusieurs critiques soulignent une bonne qualité de la nourriture par rapport au prix. Cependant, un avis négatif a soulevé des inquiétudes sur la gestion du restaurant, notamment la confusion liée à la commande d'un café, ce qui pourrait nuire à l'expérience globale.\n\nQualité du Service et des Plats :\nLes avis sur la qualité des plats sont globalement positifs, avec des mentions spéciales pour le chorizo flambé et les croquettes de morue, qui sont souvent décrits comme savoureux. En revanche, un client a signalé un service peu accueillant, en lien avec sa tentative de commander un café, ce qui a conduit à une note décevante.\n\nPoints Forts et Spécialités :\nCafé Lisboa se distingue par sa cuisine authentique et ses plats copieux, avec une attention particulière portée aux spécialités portugaises comme le pastel de nata. Les cocktails et la carte des vins sont également mentionnés comme des points forts, rendant l'endroit attractif pour ceux qui cherchent à savourer des boissons tout en dégustant des plats traditionnels.\n\nCritiques Récurrentes et Axes d'Amélioration :\nLes critiques négatives, bien que minoritaires, soulignent des problèmes de service, en particulier lorsqu'il s'agit de la gestion des attentes des clients. Il serait bénéfique pour le restaurant d'améliorer la communication sur son offre, notamment en ce qui concerne la consommation de café.\n\nInformations Pratiques et Tags :\nCafé Lisboa propose des services de repas sur place et à emporter, mais ne fait pas de livraison. Le restaurant est accessible aux personnes à mobilité réduite pour certaines zones, bien que d'autres installations restent inaccessibles. Les moyens de paiement acceptés incluent les cartes de crédit et divers chèques restaurant. Les tags associés au restaurant comprennent « cuisine portugaise », « tapas », « chorizo », et « pastel de nata », reflétant la diversité des plats offerts.\n\nHoraires d'Ouverture :\nLe restaurant est fermé le lundi et ouvert du mardi au dimanche avec des horaires variés, permettant aux clients de planifier facilement leur visite.\n\nEn résumé, Café Lisboa est une adresse à considérer pour une immersion dans la cuisine portugaise à Lyon, malgré quelques critiques concernant le service, son ambiance conviviale et ses plats savoureux en font un lieu prisé pour les amateurs de gastronomie décontractée.\n Cette activité est située à Lyon", 
            "city": "Lyon", 
            "lat": 45.76237, 
            "lng": 4.83463
        }

        # Envoi de la requête POST
        logger.info(f"Envoi de la requête à : {API_LIGHTRAG_URL}")
        logger.info(f"Payload : {json.dumps(payload, indent=2)}")

        response = requests.post(
            API_LIGHTRAG_URL, 
            json=payload, 
            headers={'Content-Type': 'application/json'}
        )

        # Vérification de la réponse
        logger.info(f"Statut de la réponse : {response.status_code}")
        logger.info(f"Contenu de la réponse : {response.text}")

        # Vérification du code de statut
        if response.status_code == 200:
            logger.info("✅ Endpoint validé avec succès !")
            return True
        else:
            logger.error(f"❌ Échec de la requête. Code de statut : {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Erreur de connexion : {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    result = test_endpoint()
    exit(0 if result else 1)
