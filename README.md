Fork du repo LightRAG


Utliser le code python examples/lightrag_openai_demo.py 
    - OpenAI avec GPT4oMini
    - Ce fichier utilise en data source "examples/lightrag_openai_demo.py" extraction de la base Myboun : info + resume
    - Il dépose le résultat dans WORKING_DIR = "./restaurant_openai_p4t_test" 
    - La partie non commentée permet de juste créer la base vector et les JSON
    - Le code python s'assure de ne travailler que sur les données non deja intégré (incrémentale)
    - La partie  commenté permet de lancer la question 
    - Ce fichier utilise lightrag/prompt.py pour réaliser l'extraction

Utliser le code python examples/graph_visual_with_html.py
    - pour créer un fichier HTML avce le gra^h
    - le fichier html est examples/knowledge_graph.html

Création d'une base graph in memory NetwokX pour analyser le graph : examples/networkX.py


Reste à faire : 
    - Il y a des entity générées sans edge
    - Il me semble qu'il y a des hallucinations dans les répsonses
