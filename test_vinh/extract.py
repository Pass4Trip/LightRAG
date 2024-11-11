import psycopg2
import os

def connect_to_db(dbname, user, password, host, port):
    try:
        # Connexion à la base de données PostgreSQL
        connection = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        return connection
    except (Exception, psycopg2.Error) as error:
        print("Erreur lors de la connexion à la base de données", error)
        return None

def test_connection(dbname, user, password, host, port):
    connection = connect_to_db(dbname, user, password, host, port)
    if connection:
        print("Connexion OK")
        connection.close()
    else:
        print("Échec de la connexion")

def generate_txt_file(rows, output_file):
    # Écriture des données dans un fichier texte avec un format spécifique
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w') as f:
        for row in rows:
            title, cid, resume = row
            f.write(f"Restaurant : {title}\n")
            f.write(f"Cid : {cid}\n")
            f.write(resume.replace('\n', ' '))
            f.write("\n")  # Ajout d'une ligne vide après chaque entrée pour la séparation
            f.write("****************\n")

    print(f"Les données ont été extraites et écrites dans le fichier {output_file}")


def connect_and_extract(dbname, user, password, host, port, output_file):
    connection = connect_to_db(dbname, user, password, host, port)
    if connection is None:
        return
    
    try:
        cursor = connection.cursor()
        
        # Requête SQL pour extraire des données spécifiques avec jointure
        query = """
          SELECT title, cid, resume FROM restaurants.information
          LEFT JOIN restaurants.longresume ON restaurants.information.id = restaurants.longresume.restaurantid;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Appel de la fonction pour générer le fichier texte
        generate_txt_file(rows, output_file)
        
    except (Exception, psycopg2.Error) as error:
        print("Erreur lors de l'extraction des données", error)
    
    finally:
        # Fermeture de la connexion
        if connection:
            cursor.close()
            connection.close()
            print("Connexion à PostgreSQL fermée")

if __name__ == "__main__":
    # Paramètres de connexion
    dbname = "myboun"
    user = "p4t"
    password = "o3CCgX7StraZqvRH5GqrOFLuzt5R6C"
    host = "vps-af24e24d.vps.ovh.net"
    port = "30030"
    
    # Nom du fichier de sortie
    output_path = os.getenv("OUTPUT_PATH", "./output")
    output_file = os.path.join(output_path, "output2.txt")
    
    # Test de connexion
    test_connection(dbname, user, password, host, port)
    
    # Appel de la fonction
    connect_and_extract(dbname, user, password, host, port, output_file)
