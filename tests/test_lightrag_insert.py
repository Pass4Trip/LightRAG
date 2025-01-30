import sys
import os
import asyncio
import logging
import traceback

# Ajouter le chemin du projet au PYTHONPATH
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from api.lightrag_insert import message_processor, MessageProcessor

# Configuration du logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_process_user_message():
    """
    Test de la méthode process_user_message
    """
    try:
        # Exemple de payload de message utilisateur
        payload = {
            "type": "user",
            "text": "Ceci est un test d'insertion de message utilisateur",
            "user_id": "test_user_123",
            "timestamp": "2024-01-30T17:30:00"
        }
        
        # Initialisation du processeur de messages
        processor = MessageProcessor()
        
        # Appel de la méthode process_user_message
        await processor.process_user_message(payload)
        
        logger.info("✅ Test d'insertion de message utilisateur réussi")
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du test : {e}")
        logger.error(f"Traceback : {traceback.format_exc()}")

async def test_process_activity_message():
    """
    Test de la méthode process_activity_message
    """
    try:
        # Exemple de payload de message d'activité
        payload = {"type": "activity", "cid": 3091293945615310311, "restaurant_id": 1, "resume": "###cid=3091293945615310311###    Résumé du Restaurant : Le Coquemar\n\nLe Coquemar est un restaurant français qui propose une cuisine traditionnelle dans une salle à la fois claire et élégante, ornée de murs de pierres et de peintures. Situé à proximité d'une basilique et de la cathédrale, cet établissement attire les gourmands en quête d'authenticité et de saveurs.\n\nAmbiance et Atmosphère :\nL'ambiance du Coquemar est chaleureuse et décontractée, idéale pour des repas en famille ou entre amis. Les clients apprécient souvent le cadre charmant et accueillant. La majorité des avis récents soulignent un service amical et efficace, contribuant à une expérience agréable.\n\nGamme de Prix et Rapport Qualité-Prix :\nLa fourchette de prix est située entre 20 et 30 euros, ce qui est jugé raisonnable par de nombreux clients. Selon plusieurs avis, le rapport qualité-prix est très bon, surtout en considérant que tous les plats sont faits maison. Cependant, un avis a noté une expérience plus moyenne, ce qui indique une certaine variabilité.\n\nQualité du Service et des Plats :\nLa qualité des plats est souvent louée, avec des commentaires particulièrement élogieux concernant la cuisine traditionnelle. Des plats faits maison, comme la crème brûlée et le tiramisu, sont souvent mentionnés. Les avis récents, notamment ceux de contributeurs expérimentés, attestent de la fraîcheur et de l'authenticité des mets servis, bien que quelques critiques isolées aient souligné des attentes modérées.\n\nPoints Forts et Spécialités :\nLe Coquemar se distingue par ses plats faits maison et son ambiance conviviale. Les clients apprécient particulièrement la qualité des desserts, et le restaurant est souvent recommandé pour son excellent rapport qualité-prix, surtout pour les plats traditionnels. \n\nCritiques Récurrentes et Axes d'Amélioration :\nCertaines critiques indiquent que la qualité peut varier, tandis que d'autres signalent des attentes différentes concernant le service. Bien que la majorité des avis soient positifs, il est important de noter cette diversité d'opinions pour une évaluation équilibrée.\n\nInformations Pratiques et Tags :\nLe Coquemar propose des repas sur place, avec des réservations acceptées. Le restaurant n'offre pas de service de livraison, mais il dispose de toilettes et d'un menu pour enfants. Les paiements par carte de crédit, chèque et paiements mobiles sont acceptés. Les animaux de compagnie sont les bienvenus, et le restaurant est accessible aux groupes. Les tags associés incluent \"prix\", \"service\", \"entrée\", et des spécialités telles que \"crème brûlée\" et \"tiramisu\".\n\nHoraires d'Ouverture :\nLe restaurant est ouvert du mardi au dimanche, de 12h00 à 14h00, et est fermé le lundi. \n\nEn résumé, Le Coquemar est une adresse à envisager pour ceux qui recherchent une cuisine traditionnelle de qualité dans une ambiance accueillante, bien que quelques disparités dans les expériences puissent exister.\n Cette activité est située à Lyon", "city": "Lyon", "lat": 45.761579, "lng": 4.821839}
        
        # Initialisation du processeur de messages
        processor = MessageProcessor()
        
        # Appel de la méthode process_activity_message
        logger.info("🔍 Début du test d'insertion d'activité")
        result = await processor.process_activity_message(payload)
        print(f"🏁 Résultat de l'insertion : {result}")
        
        logger.info("✅ Test d'insertion de message d'activité réussi")
    
    except Exception as e:
        logger.error(f"❌ Erreur lors du test : {e}")
        logger.error(f"Traceback : {traceback.format_exc()}")

def main():
    """
    Fonction principale pour exécuter les tests
    """
    #asyncio.run(test_process_user_message())
    asyncio.run(test_process_activity_message())

if __name__ == "__main__":
    main()
