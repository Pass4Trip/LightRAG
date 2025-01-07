from neo4j import GraphDatabase

def test_connection():
    uri = "bolt://localhost:7688"
    username = "neo4j"
    password = "testpassword123"
    
    try:
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            print("Connexion réussie !")
            print(result.single()['test'])
        driver.close()
    except Exception as e:
        print(f"Erreur de connexion : {e}")

if __name__ == "__main__":
    test_connection()
