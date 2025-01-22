import sys
import os
import subprocess
import logging
from pathlib import Path

# Configuration du logging pour réduire la verbosité
logging.basicConfig(
    level=logging.INFO,  # Niveau de log moins détaillé
    format='%(asctime)s - %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'  # Format de date plus court
)
logger = logging.getLogger(__name__)

def install_dependencies():
    """
    Installe les dépendances nécessaires
    """
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--break-system-packages", "python-dotenv", "pymilvus", "pymongo", "neo4j"])
        logger.info("✅ Dépendances installées avec succès")
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'installation des dépendances : {e}")
        sys.exit(1)

def run_clear_script(script_path):
    """
    Exécute un script de suppression de base de données
    
    Args:
        script_path (str): Chemin absolu du script à exécuter
    """
    try:
        logger.info(f"🔥 Exécution du script : {os.path.basename(script_path)}")
        
        # Vérifier si le script existe
        if not os.path.exists(script_path):
            logger.error(f"❌ Le script {script_path} n'existe pas")
            return
        
        # Vérifier les permissions du script
        if not os.access(script_path, os.X_OK):
            logger.error(f"❌ Le script {script_path} n'est pas exécutable")
            return
        
        # Exécuter le script avec Python et capturer les erreurs
        result = os.system(f"python3 {script_path}")
        
        if result == 0:
            logger.info(f"✅ Script {os.path.basename(script_path)} exécuté avec succès")
        else:
            logger.error(f"❌ Erreur lors de l'exécution de {os.path.basename(script_path)}")
    
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution de {script_path}: {e}")

def main():
    # Installer les dépendances
    install_dependencies()
    
    # Chemins des scripts de suppression de base de données
    base_path = Path(__file__).parent.parent
    
    scripts = [
        base_path / "milvus_docker" / "clear_database.py",
        base_path / "mongodb_docker" / "clear_database.py",
        base_path / "neo4j_microk8s" / "clear_database.py"
    ]
    
    logger.info("🧹 Début du nettoyage de toutes les bases de données")
    
    for script in scripts:
        if script.exists():
            run_clear_script(str(script))
        else:
            logger.error(f"❌ Script non trouvé : {script}")
    
    logger.info("\n🎉 Nettoyage des bases de données terminé")

if __name__ == "__main__":
    main()
