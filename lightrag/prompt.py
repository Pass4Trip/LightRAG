GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_LANGUAGE"] = "French"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["restaurant", "positive_point", "negative_point", "recommandation"]

PROMPTS["entity_extraction"] = """-Goal-
Given a text document that is potentially relevant to this activity and a list of entity types, identify all entities of those types from the text and all relationships among the identified entities.
Use {language} as output language.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, use same language as input text. If English, capitalized the name.
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes and activities
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation as to why you think the source entity and the target entity are related to each other
- relationship_strength: a numeric score indicating strength of the relationship between the source entity and target entity
- relationship_keywords: one or more high-level key words that summarize the overarching nature of the relationship, focusing on concepts or themes rather than specific details
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main concepts, themes, or topics of the entire text. These should capture the overarching ideas present in the document.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'restaurant' entity. If an entity cannot be directly or indirectly connected to the 'restaurant' through a relationship, it should not be considered valid or relevant.

5. For **positive_point**, **negative_point**, and **recommandation**, generate generic and concise labels that summarize key aspects applicable across different restaurants.

6. Return output in French as a single list of all the entities and relationships identified in steps 1 and 2. Use **{record_delimiter}** as the list delimiter. 

7. Extract cid and use it as entity_type ="restaurant"

8. When finished, output {completion_delimiter}

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

Entity_types: [restaurant, positive_point, negative_point, recommandation]
Text:
cid=3091293945615310311
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
(entity{tuple_delimiter}JUNK LYON{tuple_delimiter}restaurant{tuple_delimiter}Restaurant situé à Lyon, spécialisé dans les burgers avec une gamme de prix raisonnable de 10 à 20 euros. Ambiance chaleureuse et décontractée, appréciée pour ses plats comme les burgers, frites et cookies. Propose livraison, vente à emporter et repas sur place.){record_delimiter}
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
#############################""",
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