import requests
import json

def test_insert_endpoint():
    # URL de l'endpoint d'insertion
    url = "http://localhost:8000/insert/"

    # Exemple de payload de test pour une activité
    test_payload = {
        "type": "activity",
        "cid": "test_restaurant_123",
        "restaurant_id": 1,
        "resume": "Restaurant Le Petit Lyon est un établissement charmant situé au cœur de Lyon. "
                  "Spécialisé dans la cuisine traditionnelle française, il offre une expérience culinaire "
                  "authentique dans un cadre convivial. La carte met en valeur des produits locaux et "
                  "change selon les saisons.",
        "city": "Lyon",
        "lat": 45.7597,
        "lng": 4.8422
    }

    try:
        # Envoi de la requête POST
        response = requests.post(url, json=test_payload)
        
        # Vérification du statut de la réponse
        response.raise_for_status()
        
        # Affichage du résultat
        result = response.json()
        print("Résultat de l'insertion :")
        print(json.dumps(result, indent=2))
        
        # Assertions de base
        assert 'id' in result, "La réponse devrait contenir un identifiant"
        
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'insertion : {e}")
        raise

def test_insert_multiple_activities():
    # URL de l'endpoint d'insertion
    url = "http://localhost:8000/insert/"

    # Liste de payloads de test
    test_payloads = [
        {
            "type": "activity",
            "cid": "test_restaurant_124",
            "restaurant_id": 2,
            "resume": "Brasserie Les Artistes, un lieu emblématique de la gastronomie lyonnaise. "
                      "Situé dans le quartier des Terreaux, ce restaurant propose une cuisine bistrot "
                      "raffinée avec une carte qui change régulièrement.",
            "city": "Lyon",
            "lat": 45.7680,
            "lng": 4.8320
        },
        {
            "type": "activity",
            "cid": "test_restaurant_125",
            "restaurant_id": 3,
            "resume": "Le Bistrot des Canuts offre une expérience culinaire unique dans le quartier de la Croix-Rousse. "
                      "Spécialisé dans les plats traditionnels lyonnais, il met à l'honneur les produits locaux "
                      "et l'esprit convivial de la ville.",
            "city": "Lyon",
            "lat": 45.7750,
            "lng": 4.8350
        }
    ]

    results = []
    
    for payload in test_payloads:
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            results.append(result)
            print(f"Insertion réussie pour {payload['cid']} :")
            print(json.dumps(result, indent=2))
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de l'insertion de {payload['cid']} : {e}")
            raise

    # Vérification que tous les résultats ont un identifiant
    assert all('id' in result for result in results), "Tous les résultats devraient contenir un identifiant"

if __name__ == "__main__":
    test_insert_endpoint()
    test_insert_multiple_activities()
