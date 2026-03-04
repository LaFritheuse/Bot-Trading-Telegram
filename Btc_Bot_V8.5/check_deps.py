"""
Vérification et installation automatique des dépendances
"""
import subprocess
import sys

# Liste des dépendances requises
REQUIRED_PACKAGES = [
    'telegram',           # python-telegram-bot
    'ccxt',
    'pandas',
    'pandas_ta',
    'dotenv'              # python-dotenv
]

def check_and_install_dependencies():
    """Vérifie et installe les dépendances manquantes"""
    print("🔍 Vérification des dépendances...")
    
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} (manquant)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installation des packages manquants...")
        
        # Correspondance nom import -> nom pip
        pip_names = {
            'telegram': 'python-telegram-bot',
            'dotenv': 'python-dotenv',
            'pandas_ta': 'pandas-ta'
        }
        
        for package in missing_packages:
            pip_name = pip_names.get(package, package)
            print(f"  📥 Installation de {pip_name}...")
            
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pip_name]
                )
                print(f"  ✅ {pip_name} installé")
            except subprocess.CalledProcessError:
                print(f"  ❌ Échec de l'installation de {pip_name}")
                return False
        
        # Vérifier job-queue pour telegram
        if 'telegram' in missing_packages:
            print(f"  📥 Installation de python-telegram-bot[job-queue]...")
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "python-telegram-bot[job-queue]"]
                )
                print(f"  ✅ job-queue installé")
            except subprocess.CalledProcessError:
                print(f"  ⚠️ job-queue non installé (optionnel)")
        
        print("\n✅ Toutes les dépendances sont installées !\n")
    else:
        print("\n✅ Toutes les dépendances sont déjà installées !\n")
    
    return True

if __name__ == "__main__":
    success = check_and_install_dependencies()
    sys.exit(0 if success else 1)
