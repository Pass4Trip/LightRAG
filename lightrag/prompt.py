GRAPH_FIELD_SEP = "<SEP>"

PROMPTS = {}

PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|>"
PROMPTS["DEFAULT_RECORD_DELIMITER"] = "##"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"
PROMPTS["process_tickers"] = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

PROMPTS["DEFAULT_ENTITY_TYPES"] = ["restaurant", "cuisine", "prix", "ambiance", "localisation", "specialite", "horaire", "contact"]

PROMPTS["entity_extraction"] = """-Goal-
Given a text document about restaurants, identify all relevant entities and their relationships.

-Steps-
1. Identify all entities. For each identified entity, extract the following information:
- entity_name: Name of the entity, capitalized
- entity_type: One of the following types: [{entity_types}]
- entity_description: Comprehensive description of the entity's attributes
Format each entity as ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>

2. From the entities identified in step 1, identify all pairs of (source_entity, target_entity) that are *clearly related* to each other.
For each pair of related entities, extract the following information:
- source_entity: name of the source entity, as identified in step 1
- target_entity: name of the target entity, as identified in step 1
- relationship_description: explanation of how the entities are related (e.g., "Ce restaurant propose cette cuisine", "Ce restaurant est situé à cet endroit")
- relationship_strength: a numeric score (1-10) indicating the importance of this relationship
- relationship_keywords: key words that describe the nature of the relationship (e.g., "propose", "situé à", "spécialisé en")
Format each relationship as ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_keywords>{tuple_delimiter}<relationship_strength>)

3. Identify high-level key words that summarize the main aspects of the restaurant.
Format the content-level key words as ("content_keywords"{tuple_delimiter}<high_level_keywords>)

4. Ensure that every identified entity must have at least one relationship explicitly linking it to the 'restaurant' entity.

-Example Output-
("entity"{tuple_delimiter}"LE BISTROT"{tuple_delimiter}"restaurant"{tuple_delimiter}"Un bistrot traditionnel français au cœur de Paris")
("entity"{tuple_delimiter}"CUISINE FRANÇAISE"{tuple_delimiter}"cuisine"{tuple_delimiter}"Cuisine traditionnelle française avec des plats classiques")
("entity"{tuple_delimiter}"MODÉRÉ"{tuple_delimiter}"prix"{tuple_delimiter}"Prix modérés, environ 25-35€ par personne")
("relationship"{tuple_delimiter}"LE BISTROT"{tuple_delimiter}"CUISINE FRANÇAISE"{tuple_delimiter}"Le restaurant propose une cuisine française traditionnelle"{tuple_delimiter}"propose, spécialité"{tuple_delimiter}"9")
{{ ... }}

######################
-Examples-
######################
Example 1:

Entity_types: [restaurant, cuisine, prix, ambiance, localisation, specialite, horaire, contact]
Text:
Restaurant : Le Coquemar
Cid : 3091293945615310311
 Résumé du restaurant Le Coquemar:  Le Coquemar est un restaurant français qui offre une expérience culinaire traditionnelle dans un cadre élégant et lumineux. Situé dans un lieu où les murs de pierres sont décorés de peintures, il propose une ambiance chaleureuse et décontractée, parfaite pour les repas en famille ou en groupe.  Le prix de la nourriture se situe entre 20 et 30 euros, offrant un bon rapport qualité-prix pour les clients. Les avis clients sont généralement positifs, avec des notes allant de 4 à 5 étoiles pour la nourriture, le service et l'atmosphère. Les clients apprécient particulièrement la cuisine traditionnelle, la qualité des plats et le service attentif.  Le Coquemar est également connu pour ses options de boissons, incluant des alcools, des bières, des cafés, des cocktails et des apéritifs. Les clients peuvent également choisir des produits sains, des spiritueux, des vins et des desserts. Le restaurant propose également des traiteurs et des cartes de crédit pour faciliter les paiements.  En termes de critiques, les clients ont souvent mentionné la bonne cuisine traditionnelle et le bon service. Cependant, certains critiques ont suggéré une amélioration de l'atmosphère, qui a été notée à 2 étoiles dans certains cas.  Enfin, Le Coquemar propose des repas sur place, des réservations acceptées, des options de paiement telles que les cartes de crédit, les cartes de paiement, les chèques, les paiements mobiles NFC et Pluxee. Le restaurant est également chaleureux et accueillant, avec des toilettes disponibles et des titres restaurant pour les clients.
################
Output:
("entity"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"restaurant"{tuple_delimiter}"Le Coquemar est un restaurant français qui offre une expérience culinaire traditionnelle dans un cadre élégant et lumineux."){record_delimiter}
("entity"{tuple_delimiter}"3091293945615310311"{tuple_delimiter}"CID"{tuple_delimiter}"Le restaurant est identifié par le CID 3091293945615310311."){record_delimiter}
("entity"{tuple_delimiter}"ambiance chaleureuse"{tuple_delimiter}"ambiance"{tuple_delimiter}"Le restaurant offre une ambiance chaleureuse et décontractée."){record_delimiter}
("entity"{tuple_delimiter}"cadre attrayant"{tuple_delimiter}"localisation"{tuple_delimiter}"Le restaurant est situé dans un lieu où les murs de pierres sont décorés de peintures."){record_delimiter}
("entity"{tuple_delimiter}"service de qualité"{tuple_delimiter}"contact"{tuple_delimiter}"Les clients apprécient le service attentif."){record_delimiter}
("entity"{tuple_delimiter}"amélioration de l'atmosphère"{tuple_delimiter}"specialite"{tuple_delimiter}"Certains clients suggèrent une amélioration de l'atmosphère."){record_delimiter}
("entity"{tuple_delimiter}"cuisine recommandée"{tuple_delimiter}"cuisine"{tuple_delimiter}"Les clients recommandent la cuisine traditionnelle."){record_delimiter}

("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"3091293945615310311"{tuple_delimiter}"Le restaurant est associé au CID 3091293945615310311."{tuple_delimiter}"CID"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"ambiance chaleureuse"{tuple_delimiter}"Le restaurant propose une ambiance chaleureuse."{tuple_delimiter}"ambiance"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"cadre attrayant"{tuple_delimiter}"Le restaurant est situé dans un cadre élégant et lumineux."{tuple_delimiter}"localisation"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"service de qualité"{tuple_delimiter}"Le service est attentif et apprécié des clients."{tuple_delimiter}"contact"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"amélioration de l'atmosphère"{tuple_delimiter}"Certains clients suggèrent une amélioration de l'atmosphère."{tuple_delimiter}"specialite"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Le Coquemar"{tuple_delimiter}"cuisine recommandée"{tuple_delimiter}"La cuisine traditionnelle est particulièrement appréciée des clients."{tuple_delimiter}"cuisine"{tuple_delimiter}1){record_delimiter}


######################
Example 2:

Entity_types: [restaurant, cuisine, prix, ambiance, localisation, specialite, horaire, contact]
Text:
Restaurant : Café Lisboa
Cid : 16204433116771456015
 Résumé du Café Lisboa:  Le Café Lisboa est un restaurant décontracté situé dans un cadre coloré, offrant une expérience culinaire portugaise avec une terrasse pour profiter de la vue et des tartes à la crème portugaises. Le prix de la nourriture se situe entre 20 et 30 euros, ce qui correspond à un rapport qualité-prix raisonnable.   L'ambiance du lieu est chaleureuse et conviviale, avec une terrasse accessible aux personnes à mobilité réduite. Le restaurant est également adapté aux familles et aux groupes, avec des options de réservation disponibles.   Les avis clients sont partagés, certains appréciant la cuisine authentique et les plats copieux, tandis que d'autres expriment leur déception concernant le fait que le restaurant ne propose pas de café. Les critiques récurrentes soulignent l'importance de faire une réservation pour éviter les longues files d'attente.   Les points forts du Café Lisboa incluent la cuisine portugaise, les spécialités comme le chorizo flambé et les croquettes de morue, ainsi que les excellents cocktails et les produits sains proposés. Cependant, il est recommandé de ne pas attendre pour commander, car le service peut être lent.   En conclusion, le Café Lisboa offre une expérience culinaire portugaise décontractée avec des plats frais et des cocktails raffinés. Bien que certains aspects du service puissent être améliorés, le restaurant est une option appréciée pour un dîner casual dans le centre ville de Lyon.
################
Output:
("entity"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"restaurant"{tuple_delimiter}"Le Café Lisboa est un restaurant décontracté situé dans un cadre coloré, offrant une expérience culinaire portugaise avec une terrasse."){record_delimiter}
("entity"{tuple_delimiter}"16204433116771456015"{tuple_delimiter}"CID"{tuple_delimiter}"Le restaurant est identifié par le CID 16204433116771456015."){record_delimiter}
("entity"{tuple_delimiter}"ambiance conviviale"{tuple_delimiter}"ambiance"{tuple_delimiter}"Le restaurant offre une ambiance chaleureuse et conviviale."){record_delimiter}
("entity"{tuple_delimiter}"cadre attrayant"{tuple_delimiter}"localisation"{tuple_delimiter}"Le restaurant est situé dans un cadre coloré."){record_delimiter}
("entity"{tuple_delimiter}"adapté aux familles"{tuple_delimiter}"contact"{tuple_delimiter}"Le restaurant est adapté aux familles et aux groupes."){record_delimiter}
("entity"{tuple_delimiter}"service lent"{tuple_delimiter}"specialite"{tuple_delimiter}"Le service peut être lent, il est donc recommandé de commander rapidement."){record_delimiter}
("entity"{tuple_delimiter}"cuisine portugaise"{tuple_delimiter}"cuisine"{tuple_delimiter}"La cuisine portugaise et les spécialités comme le chorizo flambé sont recommandées."){record_delimiter}

("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"16204433116771456015"{tuple_delimiter}"Le restaurant est associé au CID 16204433116771456015."{tuple_delimiter}"CID"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"ambiance conviviale"{tuple_delimiter}"Le restaurant offre une ambiance chaleureuse et conviviale."{tuple_delimiter}"ambiance"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"cadre attrayant"{tuple_delimiter}"Le restaurant est situé dans un cadre coloré."{tuple_delimiter}"localisation"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"adapté aux familles"{tuple_delimiter}"Le restaurant est adapté aux familles et aux groupes."{tuple_delimiter}"contact"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"service lent"{tuple_delimiter}"Le service peut être lent, ce qui nécessite de commander rapidement."{tuple_delimiter}"specialite"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"Café Lisboa"{tuple_delimiter}"cuisine portugaise"{tuple_delimiter}"Les spécialités comme le chorizo flambé sont particulièrement appréciées."{tuple_delimiter}"cuisine"{tuple_delimiter}1){record_delimiter}


######################
Example 3:

Entity_types: [restaurant, cuisine, prix, ambiance, localisation, specialite, horaire, contact]
Text:
Restaurant : ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon
Cid : 15463301415010585125
 Résumé de ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon   ELLA Bolerie Méditerranéenne est un restaurant rapide situé dans la ville de Sainte-Foy-Lès-Lyon, offrant une expérience culinaire rapide et conviviale. Bien que le restaurant soit spécialisé dans la restauration rapide, il se distingue par sa spécialité méditerranéenne, proposant une variété de plats savoureux et rapidement préparés.   L'ambiance du restaurant est accueillante et moderne, avec un design qui favorise une atmosphère chaleureuse et conviviale. Le service est rapide et efficace, ce qui est essentiel dans un établissement de restauration rapide.   En ce qui concerne le rapport qualité-prix, le restaurant offre une gamme de prix qui est compétitive par rapport à d'autres options de restauration rapide dans la région. Les plats sont généralement bien reçus par les clients, bien que le restaurant n'ait pas reçu de notes étoilées.   Les points forts du restaurant incluent sa capacité à servir des repas rapidement sans compromettre la qualité, ainsi que sa disponibilité pour les livraisons sans contact et le service de drive. ELLA Bolerie Méditerranéenne est également adapté aux familles et aux enfants, avec des options de menu pour les convives végétariens.   Les critiques récurrentes suggèrent que le restaurant pourrait bénéficier d'une meilleure notoriété et d'une amélioration de la qualité des plats pour obtenir des étoiles. De plus, il est recommandé d'offrir une plus grande variété de plats pour attirer une clientèle plus large.   Enfin, le restaurant est ouvert aux heures habituelles d'une restauration rapide, propose un parking accessible en fauteuil roulant, et dispose d'un bar à salade et de cafés pour les clients qui souhaitent prendre un café ou un encas. La livraison et le service de drive sont également disponibles, ce qui le rend accessible pour les clients qui ne peuvent pas se rendre sur place.
################
Output:
("entity"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"restaurant"{tuple_delimiter}"ELLA Bolerie Méditerranéenne est un restaurant rapide situé dans la ville de Sainte-Foy-Lès-Lyon, offrant une expérience culinaire rapide et conviviale."){record_delimiter}
("entity"{tuple_delimiter}"15463301415010585125"{tuple_delimiter}"CID"{tuple_delimiter}"Le restaurant est identifié par le CID 15463301415010585125."){record_delimiter}
("entity"{tuple_delimiter}"service rapide"{tuple_delimiter}"specialite"{tuple_delimiter}"Le service est rapide et efficace."){record_delimiter}
("entity"{tuple_delimiter}"ambiance moderne"{tuple_delimiter}"ambiance"{tuple_delimiter}"Le restaurant a une ambiance moderne et conviviale."){record_delimiter}
("entity"{tuple_delimiter}"menu varié"{tuple_delimiter}"cuisine"{tuple_delimiter}"Il est recommandé d'offrir une plus grande variété de plats pour attirer plus de clients."){record_delimiter}
("entity"{tuple_delimiter}"amélioration de la qualité"{tuple_delimiter}"contact"{tuple_delimiter}"Le restaurant pourrait améliorer la qualité des plats."){record_delimiter}

("relationship"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"15463301415010585125"{tuple_delimiter}"Le restaurant est associé au CID 15463301415010585125."{tuple_delimiter}"CID"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"service rapide"{tuple_delimiter}"Le service est rapide et efficace."{tuple_delimiter}"specialite"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"ambiance moderne"{tuple_delimiter}"Le restaurant a une ambiance moderne et accueillante."{tuple_delimiter}"ambiance"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"menu varié"{tuple_delimiter}"Il est recommandé d'offrir une plus grande variété de plats."{tuple_delimiter}"cuisine"{tuple_delimiter}1){record_delimiter}
("relationship"{tuple_delimiter}"ELLA Bolerie Méditerranéenne - Sainte-Foy-Lès-Lyon"{tuple_delimiter}"amélioration de la qualité"{tuple_delimiter}"Le restaurant pourrait améliorer la qualité des plats pour satisfaire les clients."{tuple_delimiter}"contact"{tuple_delimiter}1){record_delimiter}


#############################
-Real Data-
######################
Entity_types: {entity_types}
Text: {input_text}
######################
Output:

"""

PROMPTS[
    "summarize_entity_descriptions"
] = """You are a helpful assistant responsible for generating a comprehensive summary of the data provided below.
Given one or two entities, and a list of descriptions, all related to the same entity or group of entities.
Please concatenate all of these into a single, comprehensive description. Make sure to include information collected from all the descriptions.
If the provided descriptions are contradictory, please resolve the contradictions and provide a single, coherent summary.
Make sure it is written in third person, and include the entity names so we the have full context.

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
Example 1:

Query: "How does international trade influence global economic stability?"
################
Output:
{{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}}
#############################
Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"
################
Output:
{{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}}
#############################
Example 3:

Query: "What is the role of education in reducing poverty?"
################
Output:
{{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}}
#############################
-Real Data-
######################
Query: {query}
######################
Output:

"""

PROMPTS["naive_rag_response"] = """You're a helpful assistant
Below are the knowledge you know:
{content_data}
---
If you don't know the answer or if the provided knowledge do not contain sufficient information to provide an answer, just say so. Do not make anything up.
Generate a response of the target length and format that responds to the user's question, summarizing all information in the input data tables appropriate for the response length and format, and incorporating any relevant general knowledge.
If you don't know the answer, just say so. Do not make anything up.
Do not include information where the supporting evidence for it is not provided.
---Target response length and format---
{response_type}
"""
