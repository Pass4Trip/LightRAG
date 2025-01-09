
# Recherche deux nœuds spécifiques dans le graphe en utilisant leurs identifiants personnalisés
MATCH (node1 {custom_id: '3091293945615310311'}), (node2 {custom_id: '3359024717080459809'})

# Crée des points géographiques à partir des latitudes et longitudes des nœuds
WITH point({latitude: node1.lat, longitude: node1.lng}) AS point1,
     point({latitude: node2.lat, longitude: node2.lng}) AS point2

# Calcule la distance entre ces deux points en kilomètres
# point.distance() retourne la distance en mètres, donc on divise par 1000 pour obtenir des kilomètres
RETURN point.distance(point1, point2) / 1000 AS distance_km






# Utilise la procédure APOC pour effectuer un géocodage inverse
# Convertit des coordonnées géographiques (latitude, longitude) en une adresse lisible
# 48.83609229697003, 2.7085080726151722 représentent les coordonnées géographiques
# YIELD * signifie que tous les champs retournés par la procédure seront affichés
CALL apoc.spatial.reverseGeocode(48.83609229697003, 2.7085080726151722) 
YIELD *