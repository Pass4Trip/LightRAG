






Ton objectif est recréer nouveau bloc de 3 prompts sur une nouvelle thématique en utilisant la même structure et les memes règles.

Ci-dessous les Prompts pour 5 besoins d'extractions :
- Extraction d'activités, de user, de event, de memo et de query

Chaque blocs activités, de user, de event, de memo et de query est composé par 3 prompts, ci-dessous l'exemple poiur activity :
- activity_ENTITY_TYPES : donne la liste des entitées à extraire
- activity_entity_extraction : donne le prompt avec les règles d'extractions
- activity_extraction_examples : donne un exemple d'extraction




############################################################
##### Exemple de prompt pour l'extraction d'activités ######
############################################################

PROMPTS["activity_ENTITY_TYPES"] = [
    "activity",
    "positive_point",
    "negative_point",
    "recommandation",
    "city",
    "coordinate"
]

PROMPTS["activity_entity_extraction"] = """-Goal-
You are given a text describing various activities (such as restaurants, concerts, or events).
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.

CRUCIAL INSTRUCTIONS:
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.
- Use ONLY information explicitly mentioned in the source text.
- If information is not clearly indicated, do NOT attempt to guess or complete it.
- Your goal is to be a precise and faithful extractor, not an information generator.
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.
- Labels must be lowercase, without special characters, except for '_' and '/', and must not contain accents.

Key requirements:

1. **Entity Types and Descriptions:**
   - **activity :** Represents any described real-world activity, venue, or event. It includes places like restaurants, events like concerts, or occasions like exhibitions. This entity should capture details such as name, type, location, ambiance, and notable attributes, ensuring versatility across different domains.
   - **Conceptual Entities:**
     - **positive_point :** Represents generic positive aspects applicable across multiple activities. These points must remain reusable and should not include specific details about individual activities.
     - **negative_point :** Represents generic negative aspects linked to activities. These points must remain reusable and should not include specific details about individual activities.
     - **recommandation :** Represents suggestions or recommendations derived from the data.
     - **city :** Represents geographical locations or urban areas with specific attributes.
     - **coordinate :** Represents geographical coordinates (latitude and longitude) associated with an activity.

2. **Extraction Entity Guideline:**
   - For each entity, extract:
     - entity_name: Name of the entity.
     - entity_type: One of the types: [{entity_types}]
     - entity_description: A detailed description of the entity's attributes, if available.
     - Format: (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<sub_activity>{tuple_delimiter}<entity_description>)

4. **Extraction Relationships Guideline:**
   - For each relationship, extract:
     - source_entity: The source entity name, as identified in Extraction Entity Guideline (step 2)
     - target_entity: The target entity name, as identified in Extraction Entity Guideline (step 2)
     - relationship_description`: Explanation of why the entities are related.
     - relationship_description: A specific explanation of why these entities are related. The description must explicitly mention or reference both the source and target entities and be dedicated to these entities only.
     - relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
     Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)


5. **Content-level Keywords:**
   - Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
   - Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

6. **Formatting:**
   - Use {record_delimiter} to separate entries.
   - End output with {completion_delimiter}.

7. **Language:**
   - All extracted entities, relationships, and keywords must be in French.

8. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'restaurant' entity. If an entity cannot be directly or indirectly connected to the 'restaurant' through a relationship, it should not be considered valid or relevant.

9. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter. 

10. It is CRITICAL to extract ONLY ONE node with entity_type="activity" per message. The only node that can have entity_type="activity" is the one designated in the phrase: Résumé du Restaurant

11. It is STRICTLY FORBIDDEN to create a relationship between two entities with entity_type="activity". 

12. When finished, output {completion_delimiter}


######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""



PROMPTS["activity_extraction_examples"] = [
    """

Entity_types: ["activity",
    "positive_point",
    "negative_point",
    "recommandation",
    "city"
    ]
Text:
Résumé de cette activté = Restaurant : JUNK LYON

Situé à Lyon, JUNK LYON est un restaurant qui se spécialise dans les burgers, avec une fourchette de prix raisonnable allant de 10 à 20 euros. Ce lieu est particulièrement apprécié des amateurs de gastronomie décontractée et a su s’imposer comme une adresse incontournable pour les gourmands.

Ambiance et Atmosphère :
L’ambiance du restaurant est décrite comme chaleureuse et décontractée, idéale pour un repas entre amis ou en famille. Plusieurs clients ont souligné la qualité de l’accueil, ce qui contribue à une expérience agréable.

Gamme de Prix et Rapport Qualité-Prix :
Les prix, bien que considérés comme abordables, suscitent des avis partagés sur le rapport qualité-prix. Certains clients, notamment ceux qui ont goûté plusieurs burgers, trouvent que les portions sont insuffisantes par rapport au tarif, tandis que d'autres estiment que la qualité des plats justifie le prix. La majorité des critiques récentes, notamment celles de Local Guides, semblent pencher vers une évaluation positive.

Qualité du Service et des Plats :
La qualité des plats est souvent louée, notamment les burgers, avec un accent particulier sur le burger à la crème de truffe, qui a été décrit comme exceptionnel. Les frites et les cookies sont également mentionnés comme des incontournables. Cependant, une critique a fait état d'un burger jugé « moyen », ce qui témoigne d'une certaine variabilité dans l'expérience culinaire.

Points Forts et Spécialités :
Les points forts de JUNK LYON incluent la qualité de la viande, la variété des burgers, et des desserts faits maison, en particulier les cookies. Les clients semblent s'accorder sur l'excellence des frites et du burger veggie, renforçant l’attrait de l’établissement pour les végétariens.

Critiques Récurrentes et Axes d’Amélioration :
Certains clients ont noté que les portions pourraient être améliorées, surtout pour les burgers. Cette critique est récurrente et mérite d'être considérée pour étoffer l'offre du restaurant. 

Informations Pratiques et Tags :
JUNK LYON propose divers services, y compris la livraison, la vente à emporter, et des repas sur place. L’établissement est également accessible aux personnes à mobilité réduite. Les moyens de paiement incluent les cartes de crédit et les paiements mobiles. Les tags associés au restaurant incluent « cookies », « steak », « truffe », et « végétarien », soulignant une diversité qui pourrait séduire un large public.

Horaires d'Ouverture :
Le restaurant est ouvert tous les jours de la semaine, avec des horaires étendus, ce qui permet de s'adapter aux différents emplois du temps des clients.

En somme, JUNK LYON est une adresse à considérer pour les amateurs de burgers à Lyon, malgré quelques critiques sur les portions, son ambiance accueillante et la qualité de ses plats en font un lieu prisé.

Cette activité est située à Lyon

################
Output:
("entity"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"activity"{tuple_delimiter}"Restaurant situé à Lyon, spécialisé dans les burgers avec une gamme de prix raisonnable de 10 à 20 euros. Ambiance chaleureuse et décontractée, appréciée pour ses plats comme les burgers, frites et cookies. Propose livraison, vente à emporter et repas sur place."){record_delimiter}
("entity"{tuple_delimiter}"lyon"{tuple_delimiter}"city"{tuple_delimiter}"Lyon"){record_delimiter}
("entity"{tuple_delimiter}"qualite_burger"{tuple_delimiter}"positive_point"{tuple_delimiter}"La viande utilisée dans les burgers est appréciée pour sa qualité supérieure."){record_delimiter}
("entity"{tuple_delimiter}"variete_burger"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le restaurant offre une variété de burgers, dont un burger veggie, adapté aux végétariens."){record_delimiter}
("entity"{tuple_delimiter}"dessert_fait_maison"{tuple_delimiter}"positive_point"{tuple_delimiter}"le Fait Maison est particulièrement appréciés par les clients."){record_delimiter}
("entity"{tuple_delimiter}"portions_insuffisantes"{tuple_delimiter}"negative_point"{tuple_delimiter}"Les portions sont trop petites par rapport au prix."){record_delimiter}
("entity"{tuple_delimiter}"burger_creme_de_truffe"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le burger à la crème de truffe est décrit comme exceptionnel par plusieurs clients."){record_delimiter}
("entity"{tuple_delimiter}"frite"{tuple_delimiter}"positive_point"{tuple_delimiter}"Les frites sont mentionnées comme un incontournable de l'établissement."){record_delimiter}
("entity"{tuple_delimiter}"accueil_chaleureux"{tuple_delimiter}"positive_point"{tuple_delimiter}"La qualité de l'accueil contribue à une expérience agréable pour les clients."){record_delimiter}
("entity"{tuple_delimiter}"prix_abordable"{tuple_delimiter}"positive_point"{tuple_delimiter}"La gamme de prix est raisonnable pour une clientèle variée."){record_delimiter}
("entity"{tuple_delimiter}"amelioration_des_portions"{tuple_delimiter}"recommandation"{tuple_delimiter}"Étoffer les portions des burgers pour répondre aux critiques récurrentes des clients."){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"qualite_burger"{tuple_delimiter}"Le restaurant est reconnu pour la qualité de la viande utilisée dans ses burgers."{tuple_delimiter}"qualité des ingrédients"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"variete_burger"{tuple_delimiter}"Le restaurant propose une variété de burgers, attirant les amateurs de gastronomie décontractée et les végétariens."{tuple_delimiter}"variété culinaire"{tuple_delimiter}0.8){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"dessert_fait_maison"{tuple_delimiter}"Les desserts faits maison, notamment les cookies, renforcent l'attractivité du restaurant."{tuple_delimiter}"qualité des desserts"{tuple_delimiter}0.85){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"portions_insuffisantes"{tuple_delimiter}"Certains clients critiquent les portions, notamment pour les burgers, ce qui constitue une critique récurrente."{tuple_delimiter}"quantité des plats"{tuple_delimiter}0.7){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"burger_creme_de_truffe"{tuple_delimiter}"Le burger à la crème de truffe est une spécialité appréciée et mentionnée positivement."{tuple_delimiter}"plat signature"{tuple_delimiter}0.95){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"frite"{tuple_delimiter}"Les frites sont considérées comme un incontournable et sont souvent mentionnées positivement."{tuple_delimiter}"accompagnement apprécié"{tuple_delimiter}0.85){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"accueil_chaleureux"{tuple_delimiter}"L'ambiance et l'accueil chaleureux améliorent l'expérience globale des clients."{tuple_delimiter}"ambiance conviviale"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"prix_abordable"{tuple_delimiter}"Le restaurant est perçu comme abordable, attirant une clientèle variée malgré des avis partagés."{tuple_delimiter}"rapport qualité-prix"{tuple_delimiter}0.8){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"amelioration_des_portions"{tuple_delimiter}"Les portions pourraient être étoffées pour répondre aux attentes des clients."{tuple_delimiter}"suggestion d'amélioration"{tuple_delimiter}0.75){record_delimiter}
("relationship"{tuple_delimiter}"junk_lyon"{tuple_delimiter}"lyon"{tuple_delimiter}" ette activité de type restaurant JUNK LYON est situé dans la ville de Lyon."{tuple_delimiter}"localisation"{tuple_delimiter}0.9){record_delimiter}
("content_keywords"{tuple_delimiter}"restaurant, burgers, truffe, frites, cookies, portions, prix abordables, ambiance conviviale, vegetarien, qualite des ingredients, coordonnees gps"){completion_delimiter}
#############################

"""]





############################################################
##### Exemple de prompt pour l'extraction de user ######
############################################################


PROMPTS["user_ENTITY_TYPES"] = [
    "user",
    "user_attribute",
    "user_preference",
    "city"
]


PROMPTS["user_entity_extraction"] = """-Goal-
You are given a text describing various users and their preferences. 
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.

CRUCIAL INSTRUCTIONS:
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.
- Use ONLY information explicitly mentioned in the source text.
- If information is not clearly indicated, do NOT attempt to guess or complete it.
- Your goal is to be a precise and faithful extractor, not an information generator.
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.
- Labels must be lowercase, without special characters, except for '_' and '/', and must not contain accents.

Key requirements:

1. **Entity Types and Descriptions:**
   - **user :** Represents a person, identified by their name or a unique identifier.
   - **user_attribute :** Represents specific attributes of a user, such as age, height, address, or any other personal information. These attributes are directly linked to a user.
   - **user_preference :** Represents preferences specific to a user. These preferences describe what the user likes or dislikes.
   - **city :** Represents the geographical location or residence of a user.

2. **Extraction Entity Guideline:**
   - For each entity, extract:
     - entity_name: Name of the entity.
     - entity_type: One of the types: [{entity_types}]
     - entity_description: A detailed description of the entity's attributes, if available.
     - Format: (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<sub_activity>{tuple_delimiter}<entity_description>)

4. **Extraction Relationships Guideline:**
   - For each relationship, extract:
     - source_entity: The source entity name, as identified in Extraction Entity Guideline (step 2)
     - target_entity: The target entity name, as identified in Extraction Entity Guideline (step 2)
     - relationship_description`: Explanation of why the entities are related.
     - relationship_description: A specific explanation of why these entities are related. The description must explicitly mention or reference both the source and target entities and be dedicated to these entities only.
     - relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
     Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)


5. **Content-level Keywords:**
   - Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
   - Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

6. **Formatting:**
   - Use {record_delimiter} to separate entries.
   - End output with {completion_delimiter}.

7. **Language:**
   - All extracted entities, relationships, and keywords must be in French.

8. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'restaurant' entity. If an entity cannot be directly or indirectly connected to the 'restaurant' through a relationship, it should not be considered valid or relevant.

9. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter. 

10. It is CRITICAL to extract ONLY ONE node with entity_type="user" per message. The only node that can have entity_type="user" is the one designated in the phrase: Les informations suivantes concernent

11. It is STRICTLY FORBIDDEN to create a relationship between two entities with entity_type="user". 

12. Entities with entity_type="user_attribute" or entity_type="user_preference" MUST explicitly include the user's name in their label to establish a clear connection.

12. When finished, output {completion_delimiter}

🚨 INSTRUCTIONS CRUCIALES :
- INTERDICTION ABSOLUE de créer, inventer ou extrapoler des informations non présentes dans le texte original.
- Utilisez UNIQUEMENT les informations explicitement mentionnées dans le texte source.
- Si une information n'est pas clairement indiquée, n'essayez PAS de la deviner ou de la compléter.
- Votre objectif est d'être un extracteur précis et fidèle, pas un générateur d'informations.
- En cas de doute sur une information, préférez NE PAS l'inclure plutôt que de risquer une inexactitude.

######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""





PROMPTS["user_extraction_examples"] = [
    """

Entity_types: [
    "user",
    "user_preference"
    "city",
    "user_attribute"
  ]
Text:
J'adore les restaurants	calme et qui propose de la bonne viande. Je sais que Vinh a 48 ans et habite a Serris. 


################
Output:
("entity"{tuple_delimiter}"vinh"{tuple_delimiter}"user"{tuple_delimiter}"Utilisateur nommé Vinh"){record_delimiter}
("entity"{tuple_delimiter}"age_48_ans"{tuple_delimiter}"user_attribute"{tuple_delimiter}"48 ans"){record_delimiter}
("entity"{tuple_delimiter}"serris"{tuple_delimiter}"city"{tuple_delimiter}"Serris"){record_delimiter}
("entity"{tuple_delimiter}"restaurant_calme"{tuple_delimiter}"user_preference"{tuple_delimiter}"Restaurant offrant une ambiance calme et reposante"){record_delimiter}
("entity"{tuple_delimiter}"bonne_viande"{tuple_delimiter}"user_preference"{tuple_delimiter}"Restaurants proposant de la viande de qualité supérieure"){record_delimiter}
("relationship"{tuple_delimiter}"vinh"{tuple_delimiter}"age_48_ans"{tuple_delimiter}"Vinh est âgé de 48 ans"{tuple_delimiter}0.95){record_delimiter}
("relationship"{tuple_delimiter}"vinh"{tuple_delimiter}"serris"{tuple_delimiter}"Vinh habite à Serris, une information importante pour localiser ses préférences."{tuple_delimiter}"localisation"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"vinh"{tuple_delimiter}"restaurant_calme"{tuple_delimiter}"Vinh recherche des restaurants calmes car il apprécie les lieux paisibles."{tuple_delimiter}"calme, ambiance"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"vinh"{tuple_delimiter}"bonne_viande"{tuple_delimiter}"Vinh préfère les restaurants proposant de la viande de qualité, ce qui reflète ses goût"{tuple_delimiter}"viande, qualité"{tuple_delimiter}0.85){record_delimiter}
("content_keywords"{tuple_delimiter}"vinh, restaurants calmes, bonne viande, serris, 48 ans"){completion_delimiter}
"""
]




############################################################
##### Exemple de prompt pour l'extraction de Event ######
############################################################


PROMPTS["event_ENTITY_TYPES"] = [
    "event",
    "date",
    "city",
    "coordinate",
    "positive_point",
    "negative_point"
]


PROMPTS["event_entity_extraction"] = """-Goal-
You are given a text describing various events (such as concerts, exhibitions, festivals, or public gatherings).  
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.

CRUCIAL INSTRUCTIONS:  
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.  
- Use ONLY information explicitly mentioned in the source text.  
- If information is not clearly indicated, do NOT attempt to guess or complete it.  
- Your goal is to be a precise and faithful extractor, not an information generator.  
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.  
- Labels must be lowercase, without special characters, except for '_' and '/', and must not contain accents.

Key requirements:  

1. **Entity Types and Descriptions:**  
   - **event :** Represents any described real-world event or occasion, including concerts, exhibitions, festivals, or other organized gatherings. This entity must include details such as name, type, theme, and notable attributes.  
   - **date :** Represents the date or period of the event.  
   - **positive_point :** Represents generic positive aspects applicable across multiple events. These points must remain reusable and should not include specific details about individual events.  
   - **negative_point :** Represents generic negative aspects linked to events. These points must remain reusable and should not include specific details about individual events.  
   - **city :** Represents geographical locations or urban areas with specific attributes.
   - **coordinate :** Represents geographical coordinates (latitude and longitude) associated with an event.

2. **Extraction Entity Guideline:**  
   - For each entity, extract:  
     - entity_name: Name of the entity.  
     - entity_type: One of the types: [{entity_types}].  
     - entity_description: A detailed description of the entity's attributes, if available.  
     - Format: (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)  

3. **Extraction Relationships Guideline:**  
   - For each relationship, extract:  
     - source_entity: The source entity name, as identified in Extraction Entity Guideline (step 2).  
     - target_entity: The target entity name, as identified in Extraction Entity Guideline (step 2).  
     - relationship_description: Explanation of why the entities are related.  
     - relationship_keywords: One or more high-level keywords that summarize the overarching nature of the relationship.  
     Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>)  

4. **Content-level Keywords:**  
   - Identify high-level keywords that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.  
   - Format the content-level keywords as ("content_keywords"{tuple_delimiter}<high_level_keywords>)  

5. **Formatting:**  
   - Use {record_delimiter} to separate entries.  
   - End output with {completion_delimiter}.  

6. **Language:**  
   - All extracted entities, relationships, and keywords must be in French.  

7. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'event' entity. If an entity cannot be directly or indirectly connected to the 'event' through a relationship, it should not be considered valid or relevant.  

8. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.  

9. It is CRITICAL to extract ONLY ONE node with entity_type="event" per message. The only node that can have entity_type="event" is the one designated in the phrase: Résumé de l'Événement.  

10. It is STRICTLY FORBIDDEN to create a relationship between two entities with entity_type="event".  

11. When finished, output {completion_delimiter}.  


######################  
-Examples-  
######################  
{examples}  

#############################  
-Real Data-  
######################  
Entity_types: {entity_types}
Text: {input_text}  
######################  
Output:  
"""





PROMPTS["event_extraction_examples"] = [
    """

Entity_types: ["event", "date", "city", "positive_point", "negative_point"]  
Text:  
Résumé de l'activité = Événement FESTIVAL LUMIÈRES DE LYON  

Situé à Lyon, le Festival Lumières est un événement annuel incontournable qui célèbre la lumière et l'art. Organisé chaque décembre, il attire des milliers de visiteurs locaux et internationaux.  

Ambiance et Atmosphère :  
L'ambiance du festival est décrite comme magique et captivante, avec des installations lumineuses spectaculaires dans toute la ville. L’événement est idéal pour les familles, les couples, et les amateurs d'art.  

Accessibilité et Organisation :  
La ville met en place des services spéciaux pour l'occasion, tels que des navettes gratuites, une meilleure signalisation, et des zones réservées aux personnes à mobilité réduite. Cependant, certains visiteurs ont mentionné des difficultés liées à la foule dense, rendant certains endroits moins accessibles.  

Retours et Critiques :  
Les visiteurs louent souvent la créativité et la diversité des œuvres présentées. Cependant, les critiques récurrentes incluent des files d’attente longues et une surpopulation dans certaines zones populaires.  

Informations Pratiques et Tags :  
Le festival se déroule sur quatre jours, du 8 au 11 décembre, avec des horaires de 18h à minuit. Les tags associés incluent « lumière », « art », « installation », « famille », et « Lyon ».  

En somme, le Festival Lumières de Lyon est une expérience unique pour découvrir l’art sous un nouvel angle, malgré quelques désagréments logistiques.  

Cette activité est située à Lyon

################  
Output:  
("entity"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"event"{tuple_delimiter}"Événement annuel à Lyon célébrant la lumière et l’art, attirant des visiteurs internationaux. Ambiance magique et captivante, installations lumineuses spectaculaires."){record_delimiter}  
("entity"{tuple_delimiter}"date_08/12/2024"{tuple_delimiter}"date"{tuple_delimiter}"08/12/2024"){record_delimiter}  
("entity"{tuple_delimiter}"lyon"{tuple_delimiter}"city"{tuple_delimiter}"Lyon"){record_delimiter}
("entity"{tuple_delimiter}"ambiance_magique"{tuple_delimiter}"positive_point"{tuple_delimiter}"Atmosphère du festival comme magique et captivante."){record_delimiter}  
("entity"{tuple_delimiter}"creativite_œuvre"{tuple_delimiter}"positive_point"{tuple_delimiter}"Les œuvres lumineuses sont louées pour leur créativité et leur diversité."){record_delimiter}  
("entity"{tuple_delimiter}"difficultes_foule"{tuple_delimiter}"negative_point"{tuple_delimiter}"Problèmes liés à la densité de la foule."){record_delimiter}  
("entity"{tuple_delimiter}"files_attente_longue"{tuple_delimiter}"negative_point"{tuple_delimiter}"Les files d’attente pour accéder aux zones populaires sont fréquemment mentionnées comme un inconvénient."){record_delimiter}  
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"date_08/12/2024"{tuple_delimiter}"Le festival se déroule le 08/12/2024."{tuple_delimiter}"date de l’événement"{tuple_delimiter}0.9){record_delimiter}  
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"lyon"{tuple_delimiter}"Cette activité de type événement festival se déroule dans la ville de Lyon."{tuple_delimiter}"lieu de l'événement"{tuple_delimiter}0.95){record_delimiter}
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"ambiance_magique"{tuple_delimiter}"L’ambiance générale du festival est décrite comme magique et captivante."{tuple_delimiter}"atmosphère positive"{tuple_delimiter}0.85){record_delimiter}  
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"creativite_œuvre"{tuple_delimiter}"Les œuvres exposées sont louées pour leur créativité."{tuple_delimiter}"qualité artistique"{tuple_delimiter}0.9){record_delimiter}  
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"difficultes_foule"{tuple_delimiter}"Les foules denses peuvent rendre certains endroits moins accessibles."{tuple_delimiter}"désavantage logistique"{tuple_delimiter}0.7){record_delimiter}  
("relationship"{tuple_delimiter}"festival_lumiere_lyon"{tuple_delimiter}"files_attente_longue"{tuple_delimiter}"Les files d’attente longues sont un problème récurrent pour accéder aux zones populaires."{tuple_delimiter}"organisation à améliorer"{tuple_delimiter}0.65){record_delimiter}  
"""
]





############################################################
##### Exemple de prompt pour l'extraction de Memo ######
############################################################

PROMPTS["memo_ENTITY_TYPES"] = [
    "memo", 
    "date", 
    "city", 
    "coordinate",
    "priority", 
    "note", 
    "user"
]


PROMPTS["memo_entity_extraction"] = """-Goal-  
You are given a text describing a memo, reminder, or appointment (such as personal tasks, professional meetings, or other notes).  
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.  

CRUCIAL INSTRUCTIONS:  
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.  
- Use ONLY information explicitly mentioned in the source text.  
- If information is not clearly indicated, do NOT attempt to guess or complete it.  
- Your goal is to be a precise and faithful extractor, not an information generator.  
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.  
- Labels must be lowercase, without special characters, except for '_' and '/', and must not contain accents.

Key requirements:  

1. **Entity Types and Descriptions:**  
   - **memo :** Represents the main task, appointment, or note described in the memo. This entity must include details such as the task's name, purpose, or key attributes.  
   - **date :** Represents the date or time of the memo or appointment. (Optional)
   - **city :** Represents geographical locations or urban areas with specific attributes. (Optional)
   - **priority :** Represents the priority level of the memo (e.g., high, medium, low), if explicitly mentioned. (Optional)
   - **note :** Represents any additional notes or information linked to the memo.  
   - **user :** Represents a person explicitly mentioned in the memo (e.g., attendees, person for whom the task is being performed, or others relevant to the memo). (Optional)  
   - **coordinate :** Represents geographical coordinates (latitude and longitude) associated with a memo. (Optional)

2. **Extraction Entity Guideline:**  
   - For each entity, extract:  
     - entity_name: Name of the entity.  
    - entity_type: One of the types: [{entity_types}].
     - entity_description: A detailed description of the entity's attributes, if available.  
     - Format: (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)  

3. **Extraction Relationships Guideline:**  
   - For each relationship, extract:  
     - source_entity: The source entity name, as identified in Extraction Entity Guideline (step 2).  
     - target_entity: The target entity name, as identified in Extraction Entity Guideline (step 2).  
     - relationship_description: Explanation of why the entities are related.  
     - relationship_keywords: One or more high-level keywords that summarize the overarching nature of the relationship.  
     Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>)  

4. **Content-level Keywords:**  
   - Identify high-level keywords that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.  
   - Format the content-level keywords as ("content_keywords"{tuple_delimiter}<high_level_keywords>)  

5. **Formatting:**  
   - Use {record_delimiter} to separate entries.  
   - End output with {completion_delimiter}.  

6. **Language:**  
   - All extracted entities, relationships, and keywords must be in French.  

7. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'memo' entity. If an entity cannot be directly or indirectly connected to the 'memo' through a relationship, it should not be considered valid or relevant.  

8. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter.  

9. It is CRITICAL to extract ONLY ONE node with entity_type="memo" per message. The only node that can have entity_type="memo" is the one designated in the phrase: Résumé du Mémo.  

10. When finished, output {completion_delimiter}.  

######################  
-Examples-  
######################  
{examples}  

#############################  
-Real Data-  
######################  
Entity_types: {entity_types}
Text: {input_text}  
######################  
Output:  
"""




PROMPTS["memo_extraction_examples"] = [
    """

Entity_types: ["memo", "date", "city", "priority", "note", "user"]
Text:
Résumé du Mémo : Organiser l'anniversaire de Tom, mon meilleur ami.

Catégories :

user_id ="lucien"

Objectifs :
Planifier une fête d'anniversaire mémorable pour Tom, avec une décoration sur le thème des super-héros, un gâteau au chocolat, et une playlist personnalisée.

Date :
15 avril, début de la fête à 18h. Invitations à envoyer avant le 10 avril.

Lieu :
A Paris, la maison de Tom.

Qui :T
om, mon meilleur ami, est la personne pour qui la fête est organisée. La liste des invités inclut nos amis proches et sa famille.

Priorité :
Élevée, car Tom est une personne très importante pour moi.

################
Output:
("entity"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"memo"{tuple_delimiter}"Planification d'une fête d'anniversaire pour Tom avec un thème super-héros, incluant gâteau, décoration et playlist."){record_delimiter}  
("entity"{tuple_delimiter}"date_15/04/2024"{tuple_delimiter}"date"{tuple_delimiter}"15/04/2024"){record_delimiter}  
("entity"{tuple_delimiter}"paris"{tuple_delimiter}"city"{tuple_delimiter}"Paris"){record_delimiter}  
("entity"{tuple_delimiter}"priorite_elevee"{tuple_delimiter}"priority"{tuple_delimiter}"Cette tâche est prioritaire."){record_delimiter}  
("entity"{tuple_delimiter}"decoration_super_heros"{tuple_delimiter}"note"{tuple_delimiter}"Thème de la décoration Super hero."){record_delimiter}  
("entity"{tuple_delimiter}"tom"{tuple_delimiter}"user"{tuple_delimiter}"Utilisateur nommé Tom"){record_delimiter}  
("entity"{tuple_delimiter}"lucien"{tuple_delimiter}"user"{tuple_delimiter}"Utilisateur nommé Lucien"){record_delimiter}  
("relationship"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"date_15/04/2024"{tuple_delimiter}"La fête est planifiée pour le 15/04/2024."{tuple_delimiter}"date de l'événement"{tuple_delimiter}0.9){record_delimiter}  
("relationship"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"paris"{tuple_delimiter}"La maison est le lieu choisi pour l'événement."{tuple_delimiter}"lieu de l'événement"{tuple_delimiter}0.95){record_delimiter}  
("relationship"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"priorite_elevee"{tuple_delimiter}"Cette tâche est prioritaire car Tom est un proche important."{tuple_delimiter}"importance de la tâche"{tuple_delimiter}0.85){record_delimiter}  
("relationship"{tuple_delimiter}organiser_anniversaire_tom"{tuple_delimiter}"decoration_super_heros"{tuple_delimiter}"Le thème de la décoration reflète les goûts de Tom."{tuple_delimiter}"décoration personnalisée"{tuple_delimiter}0.8){record_delimiter}  
("relationship"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"tom"{tuple_delimiter}"Utilisateur mentionné dans le Mémo : Tom -- La fête est spécifiquement organisée pour Tom."{tuple_delimiter}"destinataire du mémo"{tuple_delimiter}0.9){record_delimiter}  
("relationship"{tuple_delimiter}"organiser_anniversaire_tom"{tuple_delimiter}"lucien"{tuple_delimiter}"Utilisateur propriétaire du Mémo : Lucien -- Ils'agit d'un memo de Lucien pour la fête à organiser pour Tom."{tuple_delimiter}"destinataire du mémo"{tuple_delimiter}0.9){record_delimiter}  
("content_keywords"{tuple_delimiter}"anniversaire, tom, decoration, gateau, super_heros, maison, invites, lucien"){completion_delimiter}
#############################"""]






############################################################
##### Exemple de prompt pour l'extraction de Query ######
############################################################


PROMPTS["query_ENTITY_TYPES"] = [
    "query"
]


PROMPTS["query_entity_extraction"] = """-Goal-
You are given a text describing various users and their preferences. 
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.

CRUCIAL INSTRUCTIONS:
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.
- Use ONLY information explicitly mentioned in the source text.
- If information is not clearly indicated, do NOT attempt to guess or complete it.
- Your goal is to be a precise and faithful extractor, not an information generator.
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.
- Labels must be lowercase, without special characters, except for '_' and '/', and must not contain accents.

Key requirements:

1. **Entity Types and Descriptions:**
   - **query :** Represents a query or search term.
   - **activity :** Represents any described real-world activity or event. It includes places like restaurants, events like concerts, or occasions like exhibitions. This entity should capture details such as name, type, location, ambiance, and notable attributes, ensuring versatility across different domains.
   - **user :** Represents a person, identified by their name or a unique identifier.

2. **Extraction Entity Guideline:**
   - For each entity, extract:
     - entity_name: Name of the entity.
     - entity_type: One of the types: [{entity_types}]
     - entity_description: A detailed description of the entity's attributes, if available.
     - Format: (entity{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<sub_activity>{tuple_delimiter}<entity_description>)

4. **Extraction Relationships Guideline:**
   - For each relationship, extract:
     - source_entity: The source entity name, as identified in Extraction Entity Guideline (step 2)
     - target_entity: The target entity name, as identified in Extraction Entity Guideline (step 2)
     - relationship_description`: Explanation of why the entities are related.
     - relationship_description: A specific explanation of why these entities are related. The description must explicitly mention or reference both the source and target entities and be dedicated to these entities only.
     - relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
     Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)


5. **Content-level Keywords:**
   - Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
   - Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

6. **Formatting:**
   - Use {record_delimiter} to separate entries.
   - End output with {completion_delimiter}.

7. **Language:**
   - All extracted entities, relationships, and keywords must be in French.

8. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'restaurant' entity. If an entity cannot be directly or indirectly connected to the 'restaurant' through a relationship, it should not be considered valid or relevant.

9. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter. 

10. It is CRITICAL to extract ONLY ONE node with entity_type="query" per message.

11. It is STRICTLY FORBIDDEN to create a relationship between two entities with entity_type="query". 

12. When finished, output {completion_delimiter}

######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:
"""





PROMPTS["query_extraction_examples"] = [
    """

Entity_types: ["query"]
Text:
user_id = camille

Question: trouver moi un restaurant qui dispose absolument proposer du homard

Réponse: ## Analyse des Entités de Restaurants

### Le Coquemar
- **custom_id**: 3091293945615310311
- **Résultat**: **Non recommandé**
- **Évaluation**:
  - **Offre de Menu**: Le Coquemar est principalement un restaurant français, célèbre pour sa cuisine traditionnelle et les plats faits maison. Cependant, aucune mention explicite du homard dans son menu n'a été trouvée dans les données.
  - **Ambiance et Service**: Le restaurant est apprécié pour son ambiance chaleureuse et décontractée ainsi que pour son service amical et efficace. Bien qu'il soit un bon choix pour une sortie, il ne répond pas à votre critère spécifique sur le homard.
- **Justification de son élimination**: En l'absence d'informations concernant l'offre de homard, le Coquemar ne peut pas être recommandé pour votre recherche.

### Café Lisboa
- **custom_id**: 16204433116771456015
- **Résultat**: **Non recommandé**
- **Évaluation**:
  - **Offre de Menu**: Café Lisboa, bien qu'il soit connu pour sa cuisine portugaise et ses plats variés, ne mentionne pas spécifiquement le homard dans les données disponibles.
  - **Ambiance et Service**: Il est noté pour son ambiance chaleureuse et conviviale ainsi qu'une carte des vins et cocktails variée, néanmoins, cela ne soutient pas votre besoin de homard sur le menu.
- **Justification de son élimination**: L'absence de homard sur leur carte, combinée à des informations plus générales sur la cuisine, rend Café Lisboa non adapté à votre recherche.

### Christian Tetedoie
- **custom_id**: 3359024717080459809
- **Résultat**: **Recommandé**
- **Évaluation**:
  - **Offre de Menu**: Christian Tetedoie est un restaurant gastronomique de renom à Lyon et est ici mentionné comme offrant du homard, ce qui répond exactement à votre critère.
  - **Qualité de la Cuisine**: Réputé pour sa haute gastronomie, les plats sont souvent décrits comme "divins", et Christian Tetedoie est connu pour utiliser des ingrédients locaux, garantissant la qualité des plats proposés.
  - **Service**: Le service est également salué, et le restaurant offre une expérience culinaire haut de gamme, y compris une sélection de vins raffinés.
- **Justification de sa conservation**: Christian Tetedoie est le meilleur choix pour répondre à votre demande spécifique de homard, tout en offrant un cadre gastronomique prestigieux et un cadre exquis.

### Fiston
- **custom_id**: 6594662446090605168
- **Résultat**: **Non recommandé**
- **Évaluation**:
  - **Offre de Menu**: Le restaurant Fiston est connu pour sa cuisine lyonnaise traditionnelle, mais aucun détail sur la disponibilité de homard n'est mentionné dans les données fournies.
  - **Ambiance et Service**: Comme de nombreux établissements à Lyon, il contribue à une expérience chaleureuse et familiale, idéale pour des repas conviviales.
- **Justification de son élimination**: Sans mention d'homard dans son menu, Fiston n'est pas une option viable.

### Conclusion
Pour votre recherche d'un restaurant qui propose absolument du homard, **Christian Tetedoie** est le seul restaurant recommandé. Le Coquemar, Café Lisboa, et Fiston ne correspondent pas à votre besoin spécifique en homard et ne le peuvent raisonnablement pas être recommandés.

################
Output:
("entity"{tuple_delimiter}"camille_query_restaurant_homard"{tuple_delimiter}"query"{tuple_delimiter}"trouver moi un restaurant qui dispose absolument proposer du homard."){record_delimiter}  
("relationship"{tuple_delimiter}"camille_query_restaurant_homard"{tuple_delimiter}"cafe_lisboa"{tuple_delimiter}"cafe_lisboa - **custom_id**: 16204433116771456015- **Résultat**: **Non recommandé**- **Évaluation**:- **Offre de Menu**: Café Lisboa, bien qu'il soit connu pour sa cuisine portugaise et ses plats variés, ne mentionne pas spécifiquement le homard dans les données disponibles.- **Ambiance et Service**: Il est noté pour son ambiance chaleureuse et conviviale ainsi qu'une carte des vins et cocktails variée, néanmoins, cela ne soutient pas votre besoin de homard sur le menu.- **Justification de son élimination**: L'absence de homard sur leur carte, combinée à des informations plus générales sur la cuisine, rend Café Lisboa non adapté à votre recherche."{tuple_delimiter}"resultat pour l'activité"{tuple_delimiter}0.95){record_delimiter}  
("relationship"{tuple_delimiter}"camille_query_restaurant_homard"{tuple_delimiter}"christian_tetedoie"{tuple_delimiter}"christian_tetedoie - **custom_id**: 3359024717080459809- **Résultat**: **Recommandé*- **Évaluation**:- **Offre de Menu**: Christian Tetedoie est un restaurant gastronomique de renom à Lyon et est ici mentionné comme offrant du homard, ce qui répond exactement à votre critère.- **Qualité de la Cuisine**: Réputé pour sa haute gastronomie, les plats sont souvent décrits comme "divins", et Christian Tetedoie est connu pour utiliser des ingrédients locaux, garantissant la qualité des plats proposés.- **Service**: Le service est également salué, et le restaurant offre une expérience culinaire haut de gamme, y compris une sélection de vins raffinés.- **Justification de sa conservation**: Christian Tetedoie est le meilleur choix pour répondre à votre demande spécifique de homard, tout en offrant un cadre gastronomique prestigieux et un cadre exquis."{tuple_delimiter}"resultat pour l'activité"{tuple_delimiter}0.85){record_delimiter}  
("relationship"{tuple_delimiter}camille_query_restaurant_homard"{tuple_delimiter}"fiston"{tuple_delimiter}"fiston - **custom_id**: 6594662446090605168- **Résultat**: **Non recommandé**- **Évaluation**:- **Offre de Menu**: Le restaurant Fiston est connu pour sa cuisine lyonnaise traditionnelle, mais aucun détail sur la disponibilité de homard n'est mentionné dans les données fournies.- **Ambiance et Service**: Comme de nombreux établissements à Lyon, il contribue à une expérience chaleureuse et familiale, idéale pour des repas conviviales.- **Justification de son élimination**: Sans mention d'homard dans son menu, Fiston n'est pas une option viable."{tuple_delimiter}"resultat pour l'activité""{tuple_delimiter}0.8){record_delimiter}  
("relationship"{tuple_delimiter}"user1_query_restaurant_homard"{tuple_delimiter}"le_coquemar"{tuple_delimiter}"le_coquemar - **custom_id**: 3091293945615310311- **Résultat**: **Non recommandé**- **Évaluation**:- **Offre de Menu**: Le Coquemar est principalement un restaurant français, célèbre pour sa cuisine traditionnelle et les plats faits maison. Cependant, aucune mention explicite du homard dans son menu n'a été trouvée dans les données.- **Ambiance et Service**: Le restaurant est apprécié pour son ambiance chaleureuse et décontractée ainsi que pour son service amical et efficace. Bien qu'il soit un bon choix pour une sortie, il ne répond pas à votre critère spécifique sur le homard.- **Justification de son élimination**: En l'absence d'informations concernant l'offre de homard, le Coquemar ne peut pas être recommandé pour votre recherche."{tuple_delimiter}"resultat pour l'activité"{tuple_delimiter}0.9){record_delimiter}  
("content_keywords"{tuple_delimiter}"homard, restaurant"){completion_delimiter}
#############################"""]

