GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_LANGUAGE"] = "French"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = [
    "activity",
    "user",
    "user_attribute",
    "user_preference",
    "positive_point",
    "negative_point",
    "recommandation"
]


PROMPTS["activity_ENTITY_TYPES"] = [
    "activity",
    "positive_point",
    "negative_point",
    "recommandation"
]

PROMPTS["user_ENTITY_TYPES"] = [
    "user",
    "user_attribute",
    "user_preference"
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

Key requirements:

1. **Entity Types and Descriptions:**
   - **activity :** Represents any described real-world activity, venue, or event. It includes places like restaurants, events like concerts, or occasions like exhibitions. This entity should capture details such as name, type, location, ambiance, and notable attributes, ensuring versatility across different domains.
   - **Conceptual Entities:**
     - **positive_point :** Represents generic positive aspects applicable across multiple activities. These points must remain reusable and should not include specific details about individual activities.
     - **negative_point :** Represents generic negative aspects linked to activities. These points must remain reusable and should not include specific details about individual activities.
     - **recommandation :** Represents suggestions or recommendations derived from the data.

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

11. When finished, output {completion_delimiter}


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


PROMPTS["user_entity_extraction"] = """-Goal-
You are given a text describing various users and their preferences. 
Your task is to extract structured entities, relationships, and descriptions from the text based on the following requirements.

CRUCIAL INSTRUCTIONS:
- ABSOLUTE PROHIBITION of creating, inventing, or extrapolating information not present in the original text.
- Use ONLY information explicitly mentioned in the source text.
- If information is not clearly indicated, do NOT attempt to guess or complete it.
- Your goal is to be a precise and faithful extractor, not an information generator.
- In case of doubt about any information, prefer NOT to include it rather than risk inaccuracy.

Key requirements:

1. **Entity Types and Descriptions:**
   - **user :** Represents a person, identified by their name or a unique identifier.
   - **user_attribute :** Represents specific attributes of a user, such as age, height, address, or any other personal information. These attributes are directly linked to a user.
   - **user_preference :** Represents preferences specific to a user. These preferences describe what the user likes or dislikes.

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

10. When finished, output {completion_delimiter}

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




PROMPTS["entity_extraction_examples"] = [
    """Example 1:
Entity_types: ["activity", "user", "location", "recommendation"]
Text: Le restaurant JUNK LYON propose des burgers de qualité à Lyon.

Résultat attendu:
(entity{tuple_delimiter}JUNK LYON{tuple_delimiter}restaurant{tuple_delimiter}Restaurant de burgers à Lyon)
(entity{tuple_delimiter}Lyon{tuple_delimiter}location{tuple_delimiter}Ville du restaurant)
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Lyon{tuple_delimiter}Localisation du restaurant{tuple_delimiter}situé à{tuple_delimiter}1.0)
""",

    """Example 2:
Entity_types: ["activity", "user", "location", "recommendation"]
Text: Vinh, 48 ans, habite à Serris et aime les restaurants calmes qui proposent de la bonne viande.

Résultat attendu:
(entity{tuple_delimiter}Vinh{tuple_delimiter}user{tuple_delimiter}Homme de 48 ans)
(entity{tuple_delimiter}Serris{tuple_delimiter}location{tuple_delimiter}Ville de résidence de Vinh)
(entity{tuple_delimiter}restaurants calmes{tuple_delimiter}preference{tuple_delimiter}Type de restaurant préféré par Vinh})
""",

    """

Entity_types: ["activity",
    "positive_point",
    "negative_point",
    "recommandation"
    ]
Text:
Résumé du Restaurant : JUNK LYON

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

################
Output:
(entity{tuple_delimiter}JUNK LYON{tuple_delimiter}activity{tuple_delimiter}Restaurant situé à Lyon, spécialisé dans les burgers avec une gamme de prix raisonnable de 10 à 20 euros. Ambiance chaleureuse et décontractée, appréciée pour ses plats comme les burgers, frites et cookies. Propose livraison, vente à emporter et repas sur place.){record_delimiter}
(entity{tuple_delimiter}Qualité de la viande{tuple_delimiter}positive_point{tuple_delimiter}La viande utilisée dans les burgers est appréciée pour sa qualité supérieure.){record_delimiter}
(entity{tuple_delimiter}Variété des burgers{tuple_delimiter}positive_point{tuple_delimiter}Le restaurant offre une variété de burgers, dont un burger veggie, adapté aux végétariens.){record_delimiter}
(entity{tuple_delimiter}Desserts faits maison{tuple_delimiter}positive_point{tuple_delimiter}Les cookies faits maison sont particulièrement appréciés par les clients.){record_delimiter}
(entity{tuple_delimiter}Portions insuffisantes{tuple_delimiter}negative_point{tuple_delimiter}Certains clients trouvent que les portions des burgers sont trop petites par rapport au prix.){record_delimiter}
(entity{tuple_delimiter}Burger à la crème de truffe{tuple_delimiter}positive_point{tuple_delimiter}Le burger à la crème de truffe est décrit comme exceptionnel par plusieurs clients.){record_delimiter}
(entity{tuple_delimiter}Frites{tuple_delimiter}positive_point{tuple_delimiter}Les frites sont mentionnées comme un incontournable de l’établissement.){record_delimiter}
(entity{tuple_delimiter}Accueil chaleureux{tuple_delimiter}positive_point{tuple_delimiter}La qualité de l’accueil contribue à une expérience agréable pour les clients.){record_delimiter}
(entity{tuple_delimiter}Prix abordables{tuple_delimiter}positive_point{tuple_delimiter}La gamme de prix est raisonnable pour une clientèle variée, bien que certains avis divergent.){record_delimiter}
(entity{tuple_delimiter}Amélioration des portions{tuple_delimiter}recommandation{tuple_delimiter}Étoffer les portions des burgers pour répondre aux critiques récurrentes des clients.){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Qualité de la viande{tuple_delimiter}Le restaurant est reconnu pour la qualité de la viande utilisée dans ses burgers.{tuple_delimiter}qualité des ingrédients{tuple_delimiter}0.9){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Variété des burgers{tuple_delimiter}Le restaurant propose une variété de burgers, attirant les amateurs de gastronomie décontractée et les végétariens.{tuple_delimiter}variété culinaire{tuple_delimiter}0.8){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Desserts faits maison{tuple_delimiter}Les desserts faits maison, notamment les cookies, renforcent l’attractivité du restaurant.{tuple_delimiter}qualité des desserts{tuple_delimiter}0.85){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Portions insuffisantes{tuple_delimiter}Certains clients critiquent les portions, notamment pour les burgers, ce qui constitue une critique récurrente.{tuple_delimiter}quantité des plats{tuple_delimiter}0.7){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Burger à la crème de truffe{tuple_delimiter}Le burger à la crème de truffe est une spécialité appréciée et mentionnée positivement.{tuple_delimiter}plat signature{tuple_delimiter}0.95){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Frites{tuple_delimiter}Les frites sont considérées comme un incontournable et sont souvent mentionnées positivement.{tuple_delimiter}accompagnement apprécié{tuple_delimiter}0.85){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Accueil chaleureux{tuple_delimiter}L’ambiance et l’accueil chaleureux améliorent l’expérience globale des clients.{tuple_delimiter}ambiance conviviale{tuple_delimiter}0.9){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Prix abordables{tuple_delimiter}Le restaurant est perçu comme abordable, attirant une clientèle variée malgré des avis partagés.{tuple_delimiter}rapport qualité-prix{tuple_delimiter}0.8){record_delimiter}
(relationship{tuple_delimiter}JUNK LYON{tuple_delimiter}Amélioration des portions{tuple_delimiter}Les portions pourraient être étoffées pour répondre aux attentes des clients.{tuple_delimiter}suggestion d’amélioration{tuple_delimiter}0.75){record_delimiter}
(content_keywords{tuple_delimiter}restaurant, burgers, truffe, frites, cookies, portions, prix abordables, ambiance conviviale, végétarien, qualité des ingrédients){completion_delimiter}
#############################"""]


PROMPTS["activity_extraction_examples"] = [
    """

Entity_types: ["activity",
    "positive_point",
    "negative_point",
    "recommandation"
    ]
Text:
Résumé du Restaurant : JUNK LYON

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

################
Output:
("entity"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"activity"{tuple_delimiter}"Restaurant situé à Lyon, spécialisé dans les burgers avec une gamme de prix raisonnable de 10 à 20 euros. Ambiance chaleureuse et décontractée, appréciée pour ses plats comme les burgers, frites et cookies. Propose livraison, vente à emporter et repas sur place."){record_delimiter}
("entity"{tuple_delimiter}"Qualité de la viande"{tuple_delimiter}"positive_point"{tuple_delimiter}"La viande utilisée dans les burgers est appréciée pour sa qualité supérieure."){record_delimiter}
("entity"{tuple_delimiter}"Variété des burgers"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le restaurant offre une variété de burgers, dont un burger veggie, adapté aux végétariens."){record_delimiter}
("entity"{tuple_delimiter}"Desserts faits maison"{tuple_delimiter}"positive_point"{tuple_delimiter}"Les cookies faits maison sont particulièrement appréciés par les clients."){record_delimiter}
("entity"{tuple_delimiter}"Portions insuffisantes"{tuple_delimiter}"negative_point"{tuple_delimiter}"Certains clients trouvent que les portions des burgers sont trop petites par rapport au prix."){record_delimiter}
("entity"{tuple_delimiter}"Burger à la crème de truffe"{tuple_delimiter}"positive_point"{tuple_delimiter}"Le burger à la crème de truffe est décrit comme exceptionnel par plusieurs clients."){record_delimiter}
("entity"{tuple_delimiter}"Frites"{tuple_delimiter}"positive_point"{tuple_delimiter}"Les frites sont mentionnées comme un incontournable de l’établissement."){record_delimiter}
("entity"{tuple_delimiter}"Accueil chaleureux"{tuple_delimiter}"positive_point"{tuple_delimiter}"La qualité de l’accueil contribue à une expérience agréable pour les clients."){record_delimiter}
("entity"{tuple_delimiter}"Prix abordables"{tuple_delimiter}"positive_point"{tuple_delimiter}"La gamme de prix est raisonnable pour une clientèle variée, bien que certains avis divergent."){record_delimiter}
("entity"{tuple_delimiter}"Amélioration des portions"{tuple_delimiter}"recommandation"{tuple_delimiter}"Étoffer les portions des burgers pour répondre aux critiques récurrentes des clients."){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Qualité de la viande"{tuple_delimiter}"Le restaurant est reconnu pour la qualité de la viande utilisée dans ses burgers."{tuple_delimiter}"qualité des ingrédients"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Variété des burgers"{tuple_delimiter}"Le restaurant propose une variété de burgers, attirant les amateurs de gastronomie décontractée et les végétariens."{tuple_delimiter}"variété culinaire"{tuple_delimiter}0.8){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Desserts faits maison"{tuple_delimiter}"Les desserts faits maison, notamment les cookies, renforcent l’attractivité du restaurant."{tuple_delimiter}"qualité des desserts"{tuple_delimiter}0.85){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Portions insuffisantes"{tuple_delimiter}"Certains clients critiquent les portions, notamment pour les burgers, ce qui constitue une critique récurrente."{tuple_delimiter}"quantité des plats"{tuple_delimiter}0.7){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Burger à la crème de truffe"{tuple_delimiter}"Le burger à la crème de truffe est une spécialité appréciée et mentionnée positivement."{tuple_delimiter}"plat signature"{tuple_delimiter}0.95){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Frites"{tuple_delimiter}"Les frites sont considérées comme un incontournable et sont souvent mentionnées positivement."{tuple_delimiter}"accompagnement apprécié"{tuple_delimiter}0.85){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Accueil chaleureux"{tuple_delimiter}"L’ambiance et l’accueil chaleureux améliorent l’expérience globale des clients."{tuple_delimiter}"ambiance conviviale"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Prix abordables"{tuple_delimiter}"Le restaurant est perçu comme abordable, attirant une clientèle variée malgré des avis partagés."{tuple_delimiter}"rapport qualité-prix"{tuple_delimiter}0.8){record_delimiter}
("relationship"{tuple_delimiter}"JUNK LYON"{tuple_delimiter}"Amélioration des portions"{tuple_delimiter}"Les portions pourraient être étoffées pour répondre aux attentes des clients."{tuple_delimiter}"suggestion d’amélioration"{tuple_delimiter}0.75){record_delimiter}
("content_keywords"{tuple_delimiter}"restaurant, burgers, truffe, frites, cookies, portions, prix abordables, ambiance conviviale, végétarien, qualité des ingrédients"){completion_delimiter}
#############################"""]


PROMPTS["user_extraction_examples"] = [
    """

Entity_types: [
    "user",
    "user_preference"
  ]
Text:
Les informations suivantes concernent Vinh : Vinh adore les restaurants	calme et qui propose de la bonne viande. Je sais que Vinh a 48 ans et habite a Serris. 

################
Output:
("entity"{tuple_delimiter}"Vinh"{tuple_delimiter}"user"{tuple_delimiter}"Utilisateur nommé Vinh"){record_delimiter}
("entity"{tuple_delimiter}"48 ans"{tuple_delimiter}"user_attribute"{tuple_delimiter}"Vinh à 48 ans"){record_delimiter}
("entity"{tuple_delimiter}"Serris"{tuple_delimiter}"user_attribute"{tuple_delimiter}"Vinh réside à Serris"){record_delimiter}
("entity"{tuple_delimiter}"Restaurants calmes"{tuple_delimiter}"user_preference"{tuple_delimiter}"Vinh préfère les restaurants offrant une ambiance calme et reposante"){record_delimiter}
("entity"{tuple_delimiter}"Bonne viande"{tuple_delimiter}"user_preference"{tuple_delimiter}"Vinh apprécie particulièrement les restaurants proposant de la viande de qualité supérieure"){record_delimiter}
("relationship"{tuple_delimiter}"Vinh"{tuple_delimiter}"48 ans"{tuple_delimiter}"Vinh est âgé de 48 ans"{tuple_delimiter}0.95){record_delimiter}
("relationship"{tuple_delimiter}"Vinh"{tuple_delimiter}"Serris"{tuple_delimiter}"Vinh habite à Serris, une information importante pour localiser ses préférences."{tuple_delimiter}"localisation"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"Vinh"{tuple_delimiter}"Restaurants calmes"{tuple_delimiter}"Vinh recherche des restaurants calmes car il apprécie les lieux paisibles."{tuple_delimiter}"calme, ambiance"{tuple_delimiter}0.9){record_delimiter}
("relationship"{tuple_delimiter}"Vinh"{tuple_delimiter}"Bonne viande"{tuple_delimiter}"Vinh préfère les restaurants proposant de la viande de qualité, ce qui reflète ses goûts gastronomiques."{tuple_delimiter}"gastronomie, qualité"{tuple_delimiter}0.85){record_delimiter}
("content_keywords"{tuple_delimiter}"restaurants calmes, bonne viande, Serris, 48 ans"){completion_delimiter}
"""
]


PROMPTS["summarize_entity_descriptions"] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.
Use {language} as output language.

#######
-Data-
Entities: {entity_name}
Description List: {description_list}
#######
Output:
"""

PROMPTS[
    "entiti_continue_extraction"
] = """MANY entities were missed in the last extraction.  Add them below using the same format:
"""

PROMPTS[
    "entiti_if_loop_extraction"
] = """It appears some entities may have still been missed.  Answer YES | NO if there are still entities that need to be added.
"""

PROMPTS["fail_response"] = "Sorry, I'm not able to provide an answer to that question."

PROMPTS["rag_response"] = """---Role---

You are a helpful assistant responding to questions about data in the tables provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

---Target response length and format---

{response_type}

---Data tables---

{context_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
"""

PROMPTS["keywords_extraction"] = """---Role---

You are a helpful assistant tasked with identifying both high-level and low-level keywords in the user's query.

---Goal---

Given the query, list both high-level and low-level keywords. High-level keywords focus on overarching concepts or themes, while low-level keywords focus on specific entities, details, or concrete terms.

---Instructions---

- Output the keywords in JSON format.
- The JSON should have two keys:
  - "high_level_keywords" for overarching concepts or themes.
  - "low_level_keywords" for specific entities or details.

######################
-Examples-
######################
{examples}

#############################
-Real Data-
######################
Query: {query}
######################
The `Output` should be human text, not unicode characters. Keep the same language as `Query`.
Output:

"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}}
#############################""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}}
#############################""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}}
#############################""",
]


PROMPTS["naive_rag_response"] = """---Role---

You are a helpful assistant responding to questions about documents provided.


---Goal---

Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.

---Target response length and format---

{response_type}

---Documents---

{content_data}

Add sections and commentary to the response as appropriate for the length and format. Style the response in markdown.
"""

PROMPTS[
    "similarity_check"
] = """Please analyze the similarity between these two questions:

Question 1: {original_prompt}
Question 2: {cached_prompt}

Please evaluate:
1. Whether these two questions are semantically similar
2. Whether the answer to Question 2 can be used to answer Question 1

Please provide a similarity score between 0 and 1, where:
0: Completely unrelated or answer cannot be reused
1: Identical and answer can be directly reused
0.5: Partially related and answer needs modification to be used

Return only a number between 0-1, without any additional content.
"""
